from winnie import resourceMask

def test_getInteger():
	rm = resourceMask.ResourceMask(True, True, True)
	assert rm.getInteger() == 0b01000011

def test_maskFromInt():
	rm = resourceMask.maskFromInt(0b01000011)
	assert rm.read == True and rm.write == True and rm.flash == True
