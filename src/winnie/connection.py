from canlib import canlib, Frame
from typing import List, Tuple
from winnie import listops
from winnie import resourceMask as rm
from winnie import formatting
from winnie import verification
 
class Connection:
	def __init__(self, channel: canlib.Channel, id: int, debug: bool = False):
		self.connected = False
		self.channel = channel
		self.counter = 0
		self.id = id
		self.debug = debug
	
	def sendFrame(self, frame: Frame) -> bytearray:
		self.channel.write(frame)
		self.channel.writeSync(timeout=500)
		result = self.channel.read(timeout=500)
		return result.data

	def sendMessage(self, message: bytearray) -> bytearray:
		if self.debug == True:
			formatting.printByteArrayWithLabel("Message: ", message)
		if self.connected == False and message[0] != 0x01:
			raise RuntimeError("Connection must be established before sending a message")
		verification.verifyMessage(message)
		# Construct and send the frame
		frame = Frame(id_=self.id, data=message)
		result = self.sendFrame(frame)
		if self.debug == True:
			formatting.printByteArrayWithLabel("Response: ", result)

		currentCounter = self.counter
		self.counter += 0x01
		verification.verifyResponse(result, currentCounter)

		return result, currentCounter

	def connect(self, stationID: int) -> bool:
		if self.debug == True:
			print("CONNECT")

		splitID = listops.splitNumberByBytes(stationID, bigEndian=False)
		message = bytearray([0x01, self.counter, splitID[0], splitID[1], 0, 0, 0, 0])
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			self.connected = True
			return True
		else:
			raise RuntimeError("Connection failed")
	
	def disconnect(self, stationID: int, temporary=False) -> bool:
		if self.debug == True:
			print("DISCONNECT")

		splitID = listops.splitNumberByBytes(stationID, bigEndian=False)
		temporaryByte = 0x01
		if temporary == True:
			temporaryByte = 0x00
		message = bytearray([0x07, self.counter, temporaryByte, 0, splitID[0], splitID[1], 0, 0])
		response, msgCounter = self.sendMessage(message)
		if self.checkForAcknowledgement(response) == True:
			self.connected = False
			return True
		else:
			raise RuntimeError("Disconnect failed")
	
	def exchangeID(self) -> Tuple[rm.ResourceMask, rm.ResourceMask]:
		if self.debug == True:
			print("EXCHANGE_ID")

		message = bytearray([0x17, self.counter, 0, 0, 0, 0, 0, 0])
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

		message = bytearray([0x12, self.counter, resourceMask.getInteger(), 0, 0, 0, 0, 0])
		response, msgCounter = self.sendMessage(message)
		return response[4:]

	def unlock(self, key: bytearray) -> rm.ResourceMask:
		if self.debug == True:
			print("UNLOCK")
		if len(key) != 6:
			raise ValueError(f"Key must be 6 bytes long, was {len(key)} bytes long")
		message = bytearray([0x13, self.counter])
		message.extend(key)
		response, msgCounter = self.sendMessage(message)
		result = rm.ResourceMask(False, False, False)
		result.setFromInteger(response[3])
		return result

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
		message = bytearray(message)
		response, msgCounter = self.sendMessage(message)
		return True

	def upload(self, blockSize: int) -> bytearray:
		if self.debug == True:
			print("UPLOAD")

		if blockSize > 5:
			raise ValueError("Block size must be 5 bytes or less")
		message = bytearray([0x04, self.counter, blockSize, 0, 0, 0, 0, 0])
		response, msgCounter = self.sendMessage(message)
		return response[3:3+blockSize]
	
	def getCCPVersion(self, mainVersion: int, release: int) -> Tuple[int, int]:
		if self.debug == True:
			print("GET_CCP_VERSION")

		message = bytearray([0x1B, self.counter, mainVersion, release, 0, 0, 0, 0])
		response, msgCounter = self.sendMessage(message)
		returnedMainVersion = int(response[3])
		returnedRelease = int(response[4])
		return returnedMainVersion, returnedRelease

	def download(self, data: bytearray) -> Tuple[int, int]:
		if self.debug == True:
			print("DOWNLOAD")

		dataLength = len(data)
		if dataLength > 5:
			raise ValueError("Data must be 5 bytes or less")
		message = bytearray([0x03, self.counter, dataLength])
		message.extend(data)
		message = listops.padToLength(message, 8, padding=0)
		response, msgCounter = self.sendMessage(message)
		newExtension = int(response[3])
		newAddress = listops.listToInt(list(response[4:8]))
		return newExtension, newAddress
