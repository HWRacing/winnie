from canlib import canlib, Frame
from typing import List, Tuple
from winnie import listops
from winnie import resourceMask as rm
 
class Connection:
	def __init__(self, channel: canlib.Channel, id: int):
		self.connected = False
		self.channel = channel
		self.counter = 0
		self.id = id

	def sendMessage(self, message: List[int]) -> List[int]:
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

		currentCounter = self.counter
		self.counter += 0x01

		# Verify that the command counter of the response matches the one of the command
		if response[0] == 0xFF or response[0] == 0xFE:
			if response[2] != currentCounter:
				raise RuntimeError("Message counter in response does not match")

		return response, currentCounter

	def connect(self, stationID: int) -> bool:
		splitID = listops.splitNumberByBytes(stationID, bigEndian=False)
		message = [0x01, self.counter, splitID[0], splitID[1], 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		if response[0] == 0xFF and response[1] == 0x00:
			self.connected = True
			return True
		else:
			raise RuntimeError("Connection failed")
	
	def exchangeID(self) -> Tuple[rm.ResourceMask, rm.ResourceMask]:
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
		message = [0x12, self.counter, resourceMask.getInteger(), 0, 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		if response[0] != 0xFF:
			raise RuntimeError(f"Expected packet id 0xFF, received packed ID {response[0]:#x}")
		if response[1] != 0x00:
			raise RuntimeError(f"GET_SEED message responded with error code {response[1]:#x}")
		return response[4:]

	def unlock(self, key: Tuple[int, int, int, int, int, int]) -> rm.ResourceMask:
		message = [0x13, self.counter]
		message.extend(key)
		response, msgCounter = self.sendMessage(message)
		if response[0] == 0xFF and response[1] == 0x00:
			result = rm.ResourceMask(False, False, False)
			result.setFromInteger(response[3])
			return result
		else:
			raise RuntimeError("UNLOCK failed")

	def setMemoryTransferAddress(self, mtaNumber: int, extension: int, address: int) -> bool:
		if mtaNumber != 0 and mtaNumber != 1:
			raise ValueError("Memory transfer address number must be 0 or 1")
		# Construct the message
		message = [0x02, self.counter, extension]
		message.extend(listops.splitNumberByBytes(address, bigEndian=False))
		# Send message and handle response
		response, msgCounter = self.sendMessage(message)
		if response[0] == 0xFF and response[1] == 0x00:
			return True
		else:
			raise RuntimeError("SET_MTA failed")

	def upload(self, blockSize: int) -> List[int]:
		if blockSize > 5:
			raise ValueError("Block size must be 5 bytes or less")
		message = [0x04, self.counter, blockSize, 0, 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		if response[0] == 0xFF and response[1] == 0x00:
			return response[3:3+blockSize]
		else:
			raise ValueError("UPLOAD failed")
