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

def padToLength(l: List, targetLength: int, padding=None) -> List:
	currentLength = len(l)
	if currentLength > targetLength:
		raise ValueError(f"List too long ({currentLength}) for target length ({targetLength})")
	l.extend([padding] * (targetLength - currentLength))
	return l

def listToInt(l: List[int]) -> int:
	result = 0
	for i in l:
		result = (result << 8) | i
	return result
