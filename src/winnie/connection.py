from canlib import canlib, Frame
from typing import List, Tuple
from winnie import listops
from winnie import resourceMask as rm
from winnie import formatting
 
class Connection:
	def __init__(self, channel: canlib.Channel, id: int, debug: bool = False):
		self.connected = False
		self.channel = channel
		self.counter = 0
		self.id = id
		self.debug = debug

	def sendMessage(self, message: List[int]) -> List[int]:
		if self.debug == True:
			formatting.printHexList("Message: ", message)
		if self.connected == False and message[0] != 0x01:
			raise RuntimeError("Connection must be established before sending a message")
		# Ensure that the message is 8 bytes long
		if len(message) != 8:
			raise ValueError("Messages must be 8 bytes long")
		# Construct and send the frame
		frame = Frame(id_=self.id, data=message)
		self.channel.write(frame)
		self.channel.writeSync(timeout=500)
		# Get the result and increment the counter
		result = self.channel.read(timeout=500)
		response = [x for x in result.data]
		if self.debug == True:
			formatting.printHexList("Response: ", response)

		currentCounter = self.counter
		self.counter += 0x01

		# Verify that the command counter of the response matches the one of the command
		if response[0] == 0xFF or response[0] == 0xFE:
			if response[2] != currentCounter:
				raise RuntimeError("Message counter in response does not match")

		return response, currentCounter

	def checkForAcknowledgement(self, message: List[int]) -> bool:
		if message[0] == 0xFF and message[1] == 0x00:
			return True
		else:
			return False

	def connect(self, stationID: int) -> bool:
		if self.debug == True:
			print("CONNECT")

		splitID = listops.splitNumberByBytes(stationID, bigEndian=False)
		message = [0x01, self.counter, splitID[0], splitID[1], 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			self.connected = True
			return True
		else:
			raise RuntimeError("Connection failed")
	
	def disconnect(self, stationID, temporary=False) -> bool:
		if self.debug == True:
			print("DISCONNECT")

		splitID = listops.splitNumberByBytes(stationID, bigEndian=False)
		temporaryByte = 0x01
		if temporary == True:
			temporaryByte = 0x00
		message = [0x07, self.counter, temporaryByte, 0, splitID[0], splitID[1], 0, 0]
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			self.connected = False
			return True
		else:
			raise RuntimeError("Disconnect failed")
	
	def exchangeID(self) -> Tuple[rm.ResourceMask, rm.ResourceMask]:
		if self.debug == True:
			print("EXCHANGE_ID")

		message = [0x17, self.counter, 0, 0, 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		# Initialise two resource mask objects
		availabilityMask = rm.ResourceMask(False, False, False)
		protectionMask = rm.ResourceMask(False, False, False)
		# Put in the data from the response
		availabilityMask.setFromInteger(response[5])
		protectionMask.setFromInteger(response[6])
		return availabilityMask, protectionMask

	def getSeed(self, resourceMask: rm.ResourceMask) -> List[int]:
		if self.debug == True:
			print("GET_SEED")

		message = [0x12, self.counter, resourceMask.getInteger(), 0, 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		if response[0] != 0xFF:
			raise RuntimeError(f"Expected packet id 0xFF, received packed ID {response[0]:#x}")
		if response[1] != 0x00:
			raise RuntimeError(f"GET_SEED message responded with error code {response[1]:#x}")
		return response[4:]

	def unlock(self, key: Tuple[int, int, int, int, int, int]) -> rm.ResourceMask:
		if self.debug == True:
			print("UNLOCK")

		message = [0x13, self.counter]
		message.extend(key)
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			result = rm.ResourceMask(False, False, False)
			result.setFromInteger(response[3])
			return result
		else:
			raise RuntimeError("UNLOCK failed")

	def setMemoryTransferAddress(self, mtaNumber: int, extension: int, address: int) -> bool:
		if self.debug == True:
			print("SET_MTA")

		if mtaNumber != 0 and mtaNumber != 1:
			raise ValueError("Memory transfer address number must be 0 or 1")
		# Construct the message
		message = [0x02, self.counter, mtaNumber, extension]
		message.extend(listops.splitNumberByBytes(address, bigEndian=True))
		# Add leading 0s to address if necessary (this is why we need to switch to byte arrays)
		if len(message) < 8:
			zerosToAdd = 8 - len(message)
			message = message[:4] + [0] * zerosToAdd + message[4:]
		# Send message and handle response
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			return True
		else:
			raise RuntimeError("SET_MTA failed")

	def upload(self, blockSize: int) -> List[int]:
		if self.debug == True:
			print("UPLOAD")

		if blockSize > 5:
			raise ValueError("Block size must be 5 bytes or less")
		message = [0x04, self.counter, blockSize, 0, 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			return response[3:3+blockSize]
		else:
			raise ValueError("UPLOAD failed")
	
	def getCCPVersion(self, mainVersion: int, release: int) -> Tuple[int, int]:
		if self.debug == True:
			print("GET_CCP_VERSION")

		message = [0x1B, self.counter, mainVersion, release, 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			returnedMainVersion = response[3]
			returnedRelease = response[4]
			return returnedMainVersion, returnedRelease
		else:
			raise RuntimeError("GET_CCP_VERSION failed")
	
	def download(self, data: List[int]) -> Tuple[int, int]:
		if self.debug == True:
			print("DOWNLOAD")

		dataLength = len(data)
		if dataLength > 5:
			raise ValueError("Data must be 5 bytes or less")
		message = [0x03, self.counter, dataLength]
		message.extend(data)
		message = listops.padToLength(message, 8, padding=0)
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			raise RuntimeError("Download failed")
		newExtension = response[3]
		newAddress = listops.listToInt(response[4:8])
		return newExtension, newAddress
