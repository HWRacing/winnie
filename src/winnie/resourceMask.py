class ResourceMask:
	def __init__(self, read: bool, write: bool, flash: bool) -> None:
		self.read = read
		self.write = write
		self.flash = flash
	
	def getInteger(self) -> int:
		output = 0
		if self.write == True:
			output += 1
		if self.read == True:
			output += 2
		if self.flash == True:
			output += 64
		return output

	def setFromInteger(self, n: int) -> None:
		self.write = (n & 1) != 0
		self.read = (n & 2) != 0
		self.flash = (n & 64) != 0
