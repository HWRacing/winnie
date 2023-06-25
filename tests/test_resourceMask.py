from winnie import resourceMask

def test_getInteger():
	rm = resourceMask.ResourceMask(True, True, True)
	assert rm.getInteger() == 0b01000011
