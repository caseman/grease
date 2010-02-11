
class RGBA(object):

	def __init__(self, r_or_colorstr, g=None, b=None, a=None):
		if isinstance(r_or_colorstr, str):
			assert g is b is a is None, "Ambiguous color arguments" 
			self.r, self.g, self.b, self.a = self._parse_colorstr(r_or_colorstr)
		elif g is b is a is None:
			try:
				self.r, self.g, self.b, self.a = r_or_colorstr
			except ValueError:
				self.r, self.g, self.b = r_or_colorstr
				self.a = 1.0
		else:
			self.r = r_or_colorstr
			self.g = g
			self.b = b
			self.a = a
		if self.a is None:
			self.a = 1.0
	
	def _parse_colorstr(self, colorstr):
		length = len(colorstr)
		if not colorstr.startswith("#") or length not in (4, 5, 7, 9):
			raise ValueError("Invalid color string: " + colorstr)
		if length <= 5:
			parsed = [int(c*2, 16) / 255.0 for c in colorstr[1:]]
		else:
			parsed = [int(colorstr[i:i+2], 16) / 255.0 for i in range(1, length, 2)]
		if len(parsed) == 3:
			parsed.append(1.0)
		return parsed
	
	def __len__(self):
		return 4
	
	def __getitem__(self, item):
		return (self.r, self.g, self.b, self.a)[item]
	
	def __iter__(self):
		return iter((self.r, self.g, self.b, self.a))
	
	def __eq__(self, other):
		return tuple(self) == tuple(other)
	
	def __repr__(self):
		return "%s(%.2f, %.2f, %.2f, %.2f)" % (self.__class__.__name__, 
			self.r, self.g, self.b, self.a)
			
			
