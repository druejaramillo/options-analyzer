import math

class Constructor():

	def __init__(self):
		
		self.count = 0
		self.spreads = []
		self.actual_dte = None
		self.p = None
		self.c = None

	def make_straddles(self):

		# Construct straddles
		spread = []
		straddles = []
		for strike in range(len(self.p)):

			spread = [self.actual_dte, [-1, 'P', self.p[strike]], [-1, 'C', self.c[strike]]]
			straddles.append(spread)
			self.count += 1

		return straddles

	def make_strangles(self):

		# Construct strangles
		spread = []
		strangles = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.c)):

				spread = [self.actual_dte, [-1, 'P', self.p[strike1]], [-1, 'C', self.c[strike2]]]
				strangles.append(spread)
				self.count += 1

		return strangles

	def make_iron_butterflies(self):

		# Construct the iron butterflies
		spread = []
		iron_butterflies = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.c)):
				for strike3 in range(strike2+1, len(self.c)):

					spread = [self.actual_dte, [1, 'P', self.p[strike1]], [-1, 'P', self.p[strike2]], [-1, 'C', self.c[strike2]], [1, 'C', self.c[strike3]]]
					iron_butterflies.append(spread)
					self.count += 1

		return iron_butterflies

	def make_iron_condors(self):

		# Construct the iron condors
		spread = []
		iron_condors = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.p)):
				for strike3 in range(strike2+1, len(self.c)):
					for strike4 in range(strike3+1, len(self.c)):

						spread = [self.actual_dte, [1, 'P', self.p[strike1]], [-1, 'P', self.p[strike2]], [-1, 'C', self.c[strike3]], [1, 'C', self.c[strike4]]]
						iron_condors.append(spread)
						self.count += 1

		return iron_condors

	def make_jade_lizards(self):

		# Construct the jade lizards
		spread = []
		jade_lizards = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.c)):
				for strike3 in range(strike2+1, len(self.c)):

					spread = [self.actual_dte, [-1, 'P', self.p[strike1]], [-1, 'C', self.c[strike2]], [1, 'C', self.c[strike3]]]
					jade_lizards.append(spread)
					self.count += 1

		return jade_lizards

	def make_put_bwbs(self):

		# Construct the put BWBs
		spread = []
		put_bwbs = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+2, len(self.p)):

				strike3 = strike2 + 1
				try:
					temp = float(self.p[strike3])
				except:
					continue
				while temp < math.floor(float(self.p[strike2]) + (float(self.p[strike2]) - float(self.p[strike1]))) and strike3 < len(self.p):

					spread = [self.actual_dte, [1, 'P', self.p[strike1]], [-2, 'P', self.p[strike2]], [1, 'P', self.p[strike3]]]
					put_bwbs.append(spread)
					self.count += 1

					strike3 += 1
					try:
						temp = float(self.p[strike3])
					except:
						break

		return put_bwbs

	def make_short_put_spreads(self):

		# Construct the short put spreads
		spread = []
		short_put_spreads = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.p)):

				spread = [self.actual_dte, [1, 'P', self.p[strike1]], [-1, 'P', self.p[strike2]]]
				short_put_spreads.append(spread)
				self.count += 1

		return short_put_spreads

	def make_reverse_jade_lizards(self):

		# Construct the reverse jade lizards
		spread = []
		reverse_jade_lizards = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.c)):
				for strike3 in range(strike2+1, len(self.c)):

					spread = [self.actual_dte, [1, 'P', self.p[strike1]], [-1, 'P', self.p[strike2]], [-1, 'C', self.c[strike3]]]
					reverse_jade_lizards.append(spread)
					self.count += 1

		return reverse_jade_lizards

	def make_call_bwbs(self):

		# Construct the call BWBs
		spread = []
		call_bwbs = []
		for strike1 in range(len(self.c)):
			for strike2 in range(strike1+1, len(self.c)):

				strike3 = strike2 + 1
				try:
					temp = float(self.c[strike3])
				except:
					continue
				while temp < float(self.c[strike2]) + (float(self.c[strike2]) - float(self.c[strike1])):
					strike3 += 1
					try:
						temp = float(self.c[strike3])
					except:
						break

				while strike3 < len(self.c):

					spread = [self.actual_dte, [1, 'C', self.c[strike1]], [-2, 'C', self.c[strike2]], [1, 'C', self.c[strike3]]]
					call_bwbs.append(spread)
					self.count += 1

					strike3 += 1

		return call_bwbs

	def make_short_call_spreads(self):

		# Construct the short call spreads
		spread = []
		short_call_spreads = []
		for strike1 in range(len(self.c)):
			for strike2 in range(strike1+1, len(self.c)):

				spread = [self.actual_dte, [1, 'C', self.c[strike1]], [-1, 'C', self.c[strike2]]]
				short_call_spreads.append(spread)
				self.count += 1

		return short_call_spreads

	def make_put_ratio_spreads(self):

		# Construct the put ratio spreads
		spread = []
		put_ratio_spreads = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.p)):

				spread = [self.actual_dte, [-2, 'P', self.p[strike1]], [1, 'P', self.p[strike2]]]
				put_ratio_spreads.append(spread)
				self.count += 1

		return put_ratio_spreads

	def make_call_ratio_spreads(self):

		# Construct the call ratio spreads
		spread = []
		call_ratio_spreads = []
		for strike1 in range(len(self.c)):
			for strike2 in range(strike1+1, len(self.c)):

				spread = [self.actual_dte, [1, 'C', self.c[strike1]], [-2, 'C', self.c[strike2]]]
				call_ratio_spreads.append(spread)
				self.count += 1

		return call_ratio_spreads

	def make_super_bulls(self):

		# Construct the super bulls
		spread = []
		super_bulls = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.c)):
				for strike3 in range(strike2+1, len(self.c)):

					spread = [self.actual_dte, [-1, 'P', self.p[strike1]], [1, 'C', self.c[strike2]], [-1, 'C', self.c[strike3]]]
					super_bulls.append(spread)
					self.count += 1

		return super_bulls

	def make_super_bears(self):

		# Construct the super bears
		spread = []
		super_bears = []
		for strike1 in range(len(self.p)):
			for strike2 in range(strike1+1, len(self.c)):
				for strike3 in range(strike2+1, len(self.c)):

					spread = [self.actual_dte, [-1, 'P', self.p[strike1]], [1, 'P', self.p[strike2]], [-1, 'C', self.c[strike3]]]
					super_bears.append(spread)
					self.count += 1

		return super_bears

	def construct_spreads(self, actual_dte, p, c):

		# Reset variables
		self.count = 0
		self.spreads = []
		self.actual_dte = actual_dte
		self.p = p
		self.c = c

		# Construct spreads
		straddles = self.make_straddles()
		strangles = self.make_strangles()
		iron_butterflies = self.make_iron_butterflies()
		iron_condors = self.make_iron_condors()
		jade_lizards = self.make_jade_lizards()
		put_bwbs = self.make_put_bwbs()
		short_put_spreads = self.make_short_put_spreads()
		reverse_jade_lizards = self.make_reverse_jade_lizards()
		call_bwbs = self.make_call_bwbs()
		short_call_spreads = self.make_short_call_spreads()
		put_ratio_spreads = self.make_put_ratio_spreads()
		call_ratio_spreads = self.make_call_ratio_spreads()
		super_bulls = self.make_super_bulls()
		super_bears = self.make_super_bears()

		self.spreads = [strangles, straddles, iron_butterflies, iron_condors, jade_lizards, put_bwbs, short_put_spreads, reverse_jade_lizards, call_bwbs, short_call_spreads, put_ratio_spreads, call_ratio_spreads, super_bulls, super_bears]

		return self.count, self.spreads