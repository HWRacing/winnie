from canlib import canlib, Frame
from typing import List, Tuple, Callable
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
	
	def debugPrint(self, s: str):
		if self.debug:
			print(s)

	def incrementCounter(self):
		self.counter += 1
		if self.counter > 0xFF:
			self.counter = 0x00
	
	def sendFrame(self, frame: Frame) -> bytearray:
		self.channel.write(frame)
		self.channel.writeSync(timeout=500)
		result = self.channel.read(timeout=500)
		return result.data

	def constructCRO(self, commandCode: int, payload: bytearray=None) -> bytearray:
		if payload == None:
			payload = bytearray()
		elif len(payload) > 6:
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
	
	def sendCRO(self, commandCode: int, payload: bytearray=None) -> bytearray:
		message = self.constructCRO(commandCode, payload)
		result, _ = self.sendMessage(message)
		return result

	def connect(self, stationID: int) -> bool:
		self.debugPrint("CONNECT")
		idBytes = byteops.intToByteArray(stationID)
		self.sendCRO(0x01, payload=idBytes)
		self.connected = True
		return True
	
	def disconnect(self, stationID: int, temporary=False) -> bool:
		self.debugPrint("DISCONNECT")
		idBytes = byteops.intToByteArray(stationID)
		temporaryByte = 0x01
		if temporary == True:
			temporaryByte = 0x00
		payload = bytearray([temporaryByte, 0]) + idBytes
		self.sendCRO(0x07, payload=payload)
		self.connected = False
		return True
	
	def exchangeID(self) -> Tuple[rm.ResourceMask, rm.ResourceMask]:
		self.debugPrint("EXCHANGE_ID")
		response = self.sendCRO(0x17)
		# Initialise two resource mask objects
		availabilityMask = rm.ResourceMask(False, False, False)
		protectionMask = rm.ResourceMask(False, False, False)
		# Put in the data from the response
		availabilityMask.setFromInteger(response[5])
		protectionMask.setFromInteger(response[6])
		return availabilityMask, protectionMask

	def getSeed(self, resourceMask: rm.ResourceMask) -> List[int]:
		self.debugPrint("GET_SEED")
		payload = bytearray([resourceMask.getInteger()])
		response = self.sendCRO(0x12, payload=payload)
		return response[4:]

	def unlock(self, key: bytearray) -> rm.ResourceMask:
		self.debugPrint("UNLOCK")
		if len(key) != 6:
			raise ValueError(f"Key must be 6 bytes long, was {len(key)} bytes long")
		response = self.sendCRO(0x13, payload=key)
		return rm.maskFromInt(response[3])

	def setMemoryTransferAddress(self, mtaNumber: int, extension: int, address: int) -> bool:
		self.debugPrint("SET_MTA")
		if mtaNumber != 0 and mtaNumber != 1:
			raise ValueError("Memory transfer address number must be 0 or 1")
		addressBytes = byteops.intToByteArray(address, bigEndian=True)
		# Add leading zeros to address
		addressBytes = byteops.extendBytearray(addressBytes, 4, left=True)
		payload = bytearray([mtaNumber, extension]) + addressBytes
		self.sendCRO(0x02, payload=payload)
		self.mta = address
		self.mtaExtension = extension
		self.mtaNumber = mtaNumber
		return True

	def upload(self, blockSize: int) -> bytearray:
		self.debugPrint("UPLOAD")
		if blockSize > 5:
			raise ValueError("Block size must be 5 bytes or less")
		payload = bytearray([blockSize])
		response = self.sendCRO(0x04, payload=payload)
		self.mta += blockSize
		return response[3:3+blockSize]
	
	def shortUpload(self, blockSize: int, extension: int, address: int) -> bytearray:
		self.debugPrint("SHORT_UP")
		if blockSize > 5:
			raise ValueError("Block size must be 5 bytes or less")
		addressBytes = byteops.intToByteArray(address, bigEndian=True)
		# Add leading zeros to address
		addressBytes = byteops.extendBytearray(addressBytes, 4, left=True)
		payload = bytearray(blockSize, extension) + addressBytes
		response = self.sendCRO(0x0F, payload=payload)
		return response[3:3+blockSize]
	
	def getCCPVersion(self, mainVersion: int, release: int) -> Tuple[int, int]:
		self.debugPrint("GET_CCP_VERSION")
		payload = bytearray([mainVersion, release])
		response = self.sendCRO(0x1B, payload=payload)
		returnedMainVersion = int(response[3])
		returnedRelease = int(response[4])
		return returnedMainVersion, returnedRelease

	def download(self, data: bytearray) -> bool:
		self.debugPrint("DOWNLOAD")
		dataLength = len(data)
		if dataLength > 5:
			raise ValueError("Data must be 5 bytes or less")
		payload = bytearray([dataLength]) + data
		response = self.sendCRO(0x03, payload=payload)
		self.mtaExtension = int(response[3])
		self.mta = listops.listToInt(list(response[4:8]))
		return True
	
	def downloadSix(self, data: bytearray) -> bool:
		self.debugPrint("DNLOAD_6")
		dataLength = len(data)
		if dataLength != 6:
			raise ValueError("Data must be 6 bytes long")
		response = self.sendCRO(0x23, payload=data)
		self.mtaExtension = int(response[3])
		self.mta = listops.listToInt(list(response[4:8]))
		return True

	def setSessionStatus(self, status: sStatus.sessionStatus) -> bool:
		self.debugPrint("SET_S_STATUS")
		sessionInt = status.getInteger()
		self.sendCRO(0x0C, payload=bytearray([sessionInt]))
		return True

	def getSessionStatus(self) -> sStatus.sessionStatus:
		self.debugPrint("GET_S_STATUS")
		response = self.sendCRO(0x0D)
		return sStatus.statusFromInt(response[3])

	def selectCalibrationPage(self) -> bool:
		self.debugPrint("SELECT_CAL_PAGE")
		self.sendCRO(0x11)
		return True
