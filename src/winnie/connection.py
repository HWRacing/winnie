from canlib import canlib, Frame
from typing import List
from winnie import listops
from winnie import resourceMask as rm
 
class Connection:
	def __init__(self, channel: canlib.Channel, id: int):
		self.connected = False
		self.channel = channel
		self.counter = 0
		self.id = id

	def sendMessage(self, message: List[int]) -> List[int]:
		if self.connected == False:
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
		currentCounter = self.counter
		self.counter += 0x01

		# Verify that the command counter of the response matches the one of the command
		if result.data[0] == 0xFF or result.data[0] == 0xFE:
			if result.data[2] != currentCounter:
				raise RuntimeError("Message counter in response does not match")

		return result.data, currentCounter

	def connect(self, stationID: int) -> bool:
		message = [0x01, self.counter, 0, 0, 0, 0, 0, 0]
		splitID = listops.splitNumberByBytes(stationID)
		splitID.reverse()
		message[2:3] = splitID
		response, msgCounter = self.sendMessage(message)
		if response[0] == 0xFF and response[1] == 0x00:
			self.connected = True
			return True
		else:
			raise RuntimeError("Connection failed")
	
	def getSeed(self, resourceMask: rm.ResourceMask) -> List[int]:
		message = [0x12, self.counter, rm.getInteger, 0, 0, 0, 0, 0]
		response, msgCounter = self.sendMessage(message)
		if response[0] != 0xFF:
			raise RuntimeError(f"Expected packet id 0xFF, received packed ID {response[0]:#x}")
		if response[1] != 0x00:
			raise RuntimeError(f"GET_SEED message responded with error code {response[1]:#x}")
		return response[4:]
