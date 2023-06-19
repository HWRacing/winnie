from typing import List

def printHexList(text: str, n: List[int]):
	result = [f"0x{num:02X}" for num in n]
	print(text + str(result))

def printByteArrayWithLabel(text: str, n: bytearray):
	intList = list(n)
	printHexList(text, intList)
