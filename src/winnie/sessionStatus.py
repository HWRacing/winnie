class sessionStatus:
	def __init__(self, cal: bool, daq: bool, resume: bool, store: bool, run: bool):
		self.cal = cal
		self.daq = daq
		self.resume = resume
		self.store = store
		self.run = run
	
	def getInteger(self):
		output = 0
		if self.cal == True:
			output += 1
		if self.daq == True:
			output += 2
		if self.resume == True:
			output += 4
		if self.store == True:
			output += 64
		if self.run == True:
			output += 128
		return output

def statusFromInt(sessionInt: int) -> sessionStatus:
	cal = (sessionInt & 1) != 0
	daq = (sessionInt & 2) != 0
	resume = (sessionInt & 4) != 0
	store = (sessionInt & 64) != 0
	run = (sessionInt & 128) != 0
	return sessionStatus(cal, daq, resume, store, run)
