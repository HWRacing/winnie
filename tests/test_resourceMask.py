from winnie import resourceMask

def test_getInteger_all():
	rm = resourceMask.ResourceMask(True, True, True)
	assert rm.getInteger() == 0b01000011

def test_getInteger_read():
	rm = resourceMask.ResourceMask(True, False, False)
	assert rm.getInteger() == 0b00000010

def test_getInteger_write():
	rm = resourceMask.ResourceMask(False, True, False)
	assert rm.getInteger() == 0b00000001

def test_getInteger_flash():
	rm = resourceMask.ResourceMask(False, False, True)
	assert rm.getInteger() == 0b01000000

def test_maskFromInt():
	rm = resourceMask.maskFromInt(0b01000011)
	assert rm.read == True and rm.write == True and rm.flash == True
