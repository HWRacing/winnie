from winnie import sessionStatus

def test_getInteger_all():
	ss = sessionStatus.sessionStatus(True, True, True, True, True)
	assert ss.getInteger() == 0b11000111

def test_getInteger_cal():
	ss = sessionStatus.sessionStatus(True, False, False, False, False)
	assert ss.getInteger() == 0b00000001

def test_getInteger_daq():
	ss = sessionStatus.sessionStatus(False, True, False, False, False)
	assert ss.getInteger() == 0b00000010

def test_getInteger_resume():
	ss = sessionStatus.sessionStatus(False, False, True, False, False)
	assert ss.getInteger() == 0b00000100

def test_getInteger_store():
	ss = sessionStatus.sessionStatus(False, False, False, True, False)
	assert ss.getInteger() == 0b01000000

def test_getInteger_run():
	ss = sessionStatus.sessionStatus(False, False, False, False, True)
	assert ss.getInteger() == 0b10000000

def test_statusFromInt():
	assert sessionStatus.statusFromInt(0b11000111).getInteger() == 0b11000111
