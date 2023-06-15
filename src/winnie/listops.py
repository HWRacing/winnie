from typing import List

def splitNumberByBytes(num: int, bigEndian: bool = True) -> List[int]:
	output = []
	while num > 0:
		output.append(num % 256)
		# Shift the number 8 bits to the right
		num //= 256
	if bigEndian == True:
		output.reverse()
	return output
