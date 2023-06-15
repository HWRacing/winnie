from canlib import canlib, Frame
from typing import List
from winnie import listops
 
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
		return result.data, currentCounter

	def connect(self, stationID: int):
		message = [0x01, self.counter, 0, 0, 0, 0, 0, 0]
		splitID = listops.splitNumberByBytes(stationID)
		splitID.reverse()
		message[2:3] = splitID
		response, msgCounter = self.sendMessage()
		if response[0] == 0xFF and response[1] == 0x00 and response[2] == msgCounter:
			self.connected = True
			return True
		else:
			raise RuntimeError("Connection failed")
