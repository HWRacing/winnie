def intToByteArray(num: int, bigEndian: bool = False) -> bytearray:
	output = []
	while num > 0:
		output.append(num % 256)
		# Shift the number 8 bits to the right
		num //= 256
	if bigEndian == True:
		output.reverse()
	return bytearray(output)

def extendBytearray(b: bytearray, targetLength: int, left: bool = False, padding: int = 0x00) -> bytearray:
	currentLength = len(b)
	if currentLength >= targetLength:
		return b
	paddingLength = targetLength - currentLength
	paddingBytes = bytearray([padding] * paddingLength)
	if left:
		return paddingBytes + b
	else:
		return b + paddingBytes
