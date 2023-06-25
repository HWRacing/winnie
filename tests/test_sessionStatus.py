from winnie import sessionStatus

def test_getInteger_all():
	ss = sessionStatus.sessionStatus(True, True, True, True, True)
	expectedResult = 0b11000111

def test_getInteger_cal():
	ss = sessionStatus.sessionStatus(True, False, False, False, False)
	expectedResult = 0b00000001

def test_getInteger_daq():
	ss = sessionStatus.sessionStatus(False, True, False, False, False)
	expectedResult = 0b00000010

def test_getInteger_resume():
	ss = sessionStatus.sessionStatus(False, False, True, False, False)
	expectedResult = 0b00000100

def test_getInteger_store():
	ss = sessionStatus.sessionStatus(False, False, False, True, False)
	expectedResult = 0b01000000

def test_getInteger_run():
	ss = sessionStatus.sessionStatus(False, False, False, False, True)
	expectedResult = 0b10000000
