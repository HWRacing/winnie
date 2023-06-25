from winnie import byteops

def test_intToByteArray_littleEndian():
	input = 0xDEADBEEF
	expectedResult = bytearray([0xEF, 0xBE, 0xAD, 0xDE])
	assert byteops.intToByteArray(input) == expectedResult

def test_intToByteArray_bigEndian():
	input = 0xDEADBEEF
	expectedResult = bytearray([0xDE, 0xAD, 0xBE, 0xEF])
	assert byteops.intToByteArray(input, bigEndian=True) == expectedResult
