from canlib import canlib, Frame
from typing import List, Tuple
from winnie import listops
from winnie import resourceMask as rm
from winnie import formatting
from winnie import verification
from winnie import sessionStatus as sStatus
from winnie import byteops

class Connection:
	def __init__(self, channel: canlib.Channel, id: int, debug: bool = False):
		self.connected = False
		self.channel = channel
		self.counter = 0
		self.id = id
		self.debug = debug
		self.mta = None
		self.mtaExtension = None
		self.mtaNumber = None
	
	def incrementCounter(self):
		self.counter += 1
		if self.counter > 0xFF:
			self.counter = 0x00
	
	def sendFrame(self, frame: Frame) -> bytearray:
		self.channel.write(frame)
		self.channel.writeSync(timeout=500)
		result = self.channel.read(timeout=500)
		return result.data

	def constructCRO(self, commandCode: int, payload: bytearray) -> bytearray:
		if len(payload) > 6:
			raise ValueError(f"Payload must be 6 bytes or less, was actually {len(payload)}")
		cro = bytearray([commandCode, self.counter])
		cro.extend(payload)
		if len(cro) < 8:
			cro.extend([0x00] * (8 - len(cro)))
		return cro

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
		self.incrementCounter()
		verification.verifyResponse(result, currentCounter)

		return result, currentCounter
	
	def sendCRO(self, commandCode: int, payload: bytearray) -> bytearray:
		message = self.constructCRO(commandCode, payload)
		result, _ = self.sendMessage(message)
		return result

	def connect(self, stationID: int) -> bool:
		if self.debug == True:
			print("CONNECT")

		commandCode = 0x01
		idBytes = byteops.intToByteArray(stationID)
		self.sendCRO(commandCode, idBytes)
		self.connected = True
		return True
	
	def disconnect(self, stationID: int, temporary=False) -> bool:
		if self.debug == True:
			print("DISCONNECT")
		commandCode = 0x07
		idBytes = byteops.intToByteArray(stationID)
		temporaryByte = 0x01
		if temporary == True:
			temporaryByte = 0x00
		payload = bytearray([temporaryByte, 0]) + idBytes
		self.sendCRO(commandCode, payload)
		self.connected = False
		return True
	
	def exchangeID(self) -> Tuple[rm.ResourceMask, rm.ResourceMask]:
		if self.debug == True:
			print("EXCHANGE_ID")

		commandCode = 0x17
		response = self.sendCRO(commandCode, bytearray())
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

		commandCode = 0x12
		payload = bytearray([resourceMask.getInteger()])
		response = self.sendCRO(commandCode, payload)
		return response[4:]

	def unlock(self, key: bytearray) -> rm.ResourceMask:
		if self.debug == True:
			print("UNLOCK")
		if len(key) != 6:
			raise ValueError(f"Key must be 6 bytes long, was {len(key)} bytes long")
		message = bytearray([0x13, self.counter])
		message.extend(key)
		response, msgCounter = self.sendMessage(message)
		return rm.maskFromInt(response[3])

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
		self.mta = address
		self.mtaExtension = extension
		self.mtaNumber = mtaNumber
		return True

	def upload(self, blockSize: int) -> bytearray:
		if self.debug == True:
			print("UPLOAD")

		if blockSize > 5:
			raise ValueError("Block size must be 5 bytes or less")
		message = bytearray([0x04, self.counter, blockSize, 0, 0, 0, 0, 0])
		response, msgCounter = self.sendMessage(message)
		self.mta += blockSize
		return response[3:3+blockSize]
	
	# def shortUpload(self, blockSize: int, extension: int, address: int) -> bytearray:
	# 	if self.debug == True:
	# 		print("SHORT_UP")
	# 	if blockSize > 5:
	# 		raise ValueError("Block size must be 5 bytes or less")
	# 	message = bytearray([0x0F, self.counter, blockSize, extension, address, 0, 0, 0])
	# 	response, msgCounter = self.sendMessage(message)
	# 	return response[3:3+blockSize]
	
	def getCCPVersion(self, mainVersion: int, release: int) -> Tuple[int, int]:
		if self.debug == True:
			print("GET_CCP_VERSION")

		commandCode = 0x1B
		payload = bytearray([mainVersion, release])
		response = self.sendCRO(commandCode, payload)
		returnedMainVersion = int(response[3])
		returnedRelease = int(response[4])
		return returnedMainVersion, returnedRelease

	def download(self, data: bytearray) -> bool:
		if self.debug == True:
			print("DOWNLOAD")

		dataLength = len(data)
		if dataLength > 5:
			raise ValueError("Data must be 5 bytes or less")
		commandCode = 0x03
		payload = bytearray([dataLength]) + data
		response = self.sendCRO(commandCode, payload)
		self.mtaExtension = int(response[3])
		self.mta = listops.listToInt(list(response[4:8]))
		return True
	
	def downloadSix(self, data: bytearray) -> bool:
		if self.debug == True:
			print("DNLOAD_6")
		dataLength = len(data)
		if dataLength != 6:
			raise ValueError("Data must be 6 bytes long")
		commandCode = 0x23
		response = self.sendCRO(commandCode, data)
		self.mtaExtension = int(response[3])
		self.mta = listops.listToInt(list(response[4:8]))
		return True

	def setSessionStatus(self, status: sStatus.sessionStatus) -> bool:
		if self.debug == True:
			print("SET_S_STATUS")
		
		sessionInt = status.getInteger()
		
		message = bytearray([0x0C, self.counter, sessionInt, 0, 0, 0, 0, 0])
		response, msgCounter = self.sendMessage(message)
		return True

	def getSessionStatus(self) -> sStatus.sessionStatus:
		if self.debug == True:
			print("GET_S_STATUS")
		message = bytearray([0x0D, self.counter, 0, 0, 0, 0, 0, 0])
		response, msgCounter = self.sendMessage(message)
		return sStatus.statusFromInt(response[3])

	def selectCalibrationPage(self) -> bool:
		if self.debug == True:
			print("SELECT_CAL_PAGE")
		message = bytearray([0x11, self.counter, 0, 0, 0, 0, 0, 0])
		response, msgCounter = self.sendMessage(message)
		return True
