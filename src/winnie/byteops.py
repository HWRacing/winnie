def intToByteArray(num: int, bigEndian: bool = False) -> bytearray:
	output = []
	while num > 0:
		output.append(num % 256)
		# Shift the number 8 bits to the right
		num //= 256
	if bigEndian == True:
		output.reverse()
	return bytearray(output)
