from winnie import constants

def verifyMessage(message: bytearray) -> bool:
	if len(message) != 8:
		raise ValueError("Messages must be 8 bytes long")
	if message[0] not in constants.commandCodes:
		raise ValueError(f"{message[0]} is not a valid command code")
	return True

def verifyReceivedCounter(response: bytearray, sentCounter: int) -> bool:
	if response[0] != 0xFF:
		raise ValueError("Cannot verify counter of messages other than command return messages")
	if response[2] != sentCounter:
		raise RuntimeError(f"Received counter ({response[2]}) does not match sent counter ({sentCounter})")
	return True

def checkForAcknowledgement(message: bytearray) -> bool:
	if message[0] == 0xFF or message[0] == 0xFE:
		if message[1] == 0x00:
			return True
		else:
			return False
	raise ValueError("Cannot check for acknowledgement of data acquisition message")

def checkResponseCode(code: int) -> bool:
	if code == 0x00:
		return True
	if not code in constants.commandReturnCodes:
		raise ValueError(f"Invalid command response code {code:#x}")
	raise RuntimeError(f"Error: {code:#x} - {constants.commandReturnCodes[code]}")

def verifyResponse(response: bytearray, sentCounter: int) -> bool:
	packetID = response[0]
	# Command return message
	if packetID == 0xFF:
		verifyReceivedCounter(response, sentCounter)
		checkResponseCode(response[1])
	# Event message
	elif packetID == 0xFE:
		checkForAcknowledgement(response)
		checkResponseCode(response[1])
	# Data Acquisition Message
	else:		
		pass
	return True
