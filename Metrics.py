import json
import datetime
from datetime import date
from datetime import timedelta
import dateutil
import atexit
import math
from scipy.stats import norm

# Get the intrinsic value of a call option at expiration
def call_value(S, K):

	if S > K:
		return S-K
	else:
		return 0.0

# Get the intrinsic value of a put option at expiration
def put_value(S, K):

	if K > S:
		return K-S
	else:
		return 0.0

# Get the profit/loss of a spread at an underlying price at expiration
def get_pl(spread, price, credit):

	pl = 0
	for i in range(1, len(spread)):
		pl_leg = 0
		leg = spread[i]
		if leg[1] == 'C':
			pl_leg += leg[0] * call_value(price, float(leg[2]))
		else:
			pl_leg += leg[0] * put_value(price, float(leg[2]))
		pl += pl_leg
	pl += credit
	pl *= 100

	return pl

class Metrics():

	def __init__(self, dtes, put_strikes, call_strikes, und_price, und_beta, und_IV):
		
		self.dtes = dtes
		self.put_strikes = put_strikes
		self.call_strikes = call_strikes
		self.und_price = und_price
		self.und_beta = und_beta
		self.und_IV = und_IV

	# --------------- Functions to Calculate Metrics ---------------

	# Note: all_spreads = [strangles, straddles, iron_butterflies, iron_condors, jade_lizards, put_bwbs, short_put_spreads, reverse_jade_lizards, call_bwbs, short_call_spreads, put_ratio_spreads, call_ratio_spreads, super_bulls, super_bears]

	# Calculate credit received and check liquidity
	def checks(self, spread):

		dte = self.dtes.index(spread[0])

		credit = 0
		for i in range(1, len(spread)):
			leg = spread[i]
			if leg[1] == 'C':
				if leg[0] < 0:
					credit += self.call_strikes[dte][leg[2]][0]['bid']
				else:
					credit -= self.call_strikes[dte][leg[2]][0]['ask']
			else:
				if leg[0] < 0:
					credit += self.put_strikes[dte][leg[2]][0]['bid']
				else:
					credit -= self.put_strikes[dte][leg[2]][0]['ask']

		liquidity = True
		for i in range(1, len(spread)):
			leg = spread[i]
			if leg[1] == 'C':
				liquidity = liquidity and self.call_strikes[dte][leg[2]][0]['openInterest'] >= 900 and self.call_strikes[dte][leg[2]][0]['ask'] - self.call_strikes[dte][leg[2]][0]['bid'] <= 0.005 * self.und_price
			else:
				liquidity = liquidity and self.put_strikes[dte][leg[2]][0]['openInterest'] >= 900 and self.put_strikes[dte][leg[2]][0]['ask'] - self.put_strikes[dte][leg[2]][0]['bid'] <= 0.005 * self.und_price

		return credit, liquidity

	def max_profit(self, spread, spread_type, credit):

		mp = 0

		if spread_type == 6 or spread_type == 13:
			mp = 100 * (abs(float(spread[3][2]) - float(spread[2][2])) + credit)
		elif spread_type == 9 or spread_type == 11 or spread_type == 12 or spread_type == 14:
			mp = 100 * (abs(float(spread[2][2]) - float(spread[1][2])) + credit)
		else:
			mp = 100 * credit

		return mp

	def expected_value(self, spread):

		dte = spread[0]

		credit, liquidity = self.checks(spread)

		ev = 0
		for i in range(1, 100):
			ev += 0.01 * get_pl(spread, math.exp((norm.ppf(i/100) * self.und_IV * math.sqrt(1.0*dte/365)) + 0.02*dte/365) * self.und_price, credit)
		ev += 0.01 * get_pl(spread, math.exp((norm.ppf(0.999) * self.und_IV * math.sqrt(1.0*dte/365)) + 0.02*dte/365) * self.und_price, credit)

		return ev

	def common_metrics(self, spread, spread_type, break_evens, credit):

		dte = spread[0]
		dte_index = self.dtes.index(dte)

		two_sd_below = self.und_price - 2.01 * self.und_IV * self.und_price * math.sqrt(dte/365)
		two_sd_above = self.und_price + 2.01 * self.und_IV * self.und_price * math.sqrt(dte/365)
		four_sd_below = self.und_price - 4.01 * self.und_IV * self.und_price * math.sqrt(dte/365)
		four_sd_above = self.und_price + 4.01 * self.und_IV * self.und_price * math.sqrt(dte/365)
		step = 0.05 * self.und_price * self.und_IV * math.sqrt(dte/365)

		mp = self.max_profit(spread, spread_type, credit)

		upper_prob = 1
		if break_evens[1] != 1000000:
			upper_prob = norm.cdf((math.log(break_evens[1]/self.und_price) - 0.02*dte/365)/(self.und_IV * math.sqrt(1.0*dte/365)), 0, 1)
		lower_prob = 0
		if break_evens[0] != 0.00001:
			lower_prob = norm.cdf((math.log(break_evens[0]/self.und_price) - 0.02*dte/365)/(self.und_IV * math.sqrt(1.0*dte/365)), 0, 1)
		pop = 100 * (upper_prob - lower_prob)

		tot_delta = 0
		for i in range(1, len(spread)):
			leg = spread[i]
			if leg[1] == 'C':
				delta = 100 * leg[0] * self.call_strikes[dte_index][leg[2]][0]['delta']
			else:
				delta = 100 * leg[0] * self.put_strikes[dte_index][leg[2]][0]['delta']
			tot_delta += delta

		tot_theta = 0
		for i in range(1, len(spread)):
			leg = spread[i]
			if leg[1] == 'C':
				theta = 100 * leg[0] * self.call_strikes[dte_index][leg[2]][0]['theta']
			else:
				theta = 100 * leg[0] * self.put_strikes[dte_index][leg[2]][0]['theta']
			tot_theta += theta

		beta_delta = self.und_beta * tot_delta

		return two_sd_below, two_sd_above, four_sd_below, four_sd_above, step, mp, pop, tot_delta, tot_theta, beta_delta

	# Order: strangle, straddle, iron butterfly, iron condor, jade lizard, put bwb, short put spread, reverse jade lizard, call bwb, short call spread, put ratio spread, call ratio spread, super bull, super bear
	def calc_break_evens(self, spread, spread_type, credit):

		break_evens = []

		if spread_type == 1 or spread_type == 2:
			break_evens = [float(spread[1][2])-credit, float(spread[2][2])+credit]
		elif spread_type == 3 or spread_type == 4:
			break_evens = [float(spread[2][2])-credit, float(spread[3][2])+credit]
		elif spread_type == 5 or spread_type == 13:
			break_evens = [float(spread[1][2])-credit, 1000000]
		elif spread_type == 6:
			break_evens = [float(spread[2][2])-abs(float(spread[3][2])-float(spread[2][2]))-credit, 1000000]
		elif spread_type == 7:
			break_evens = [float(spread[2][2])-credit, 1000000]
		elif spread_type == 8 or spread_type == 14:
			break_evens = [0.00001, float(spread[3][2])+credit]
		elif spread_type == 9 or spread_type == 12:
			break_evens = [0.00001, float(spread[2][2])+(abs(float(spread[2][2])-float(spread[1][2]))+credit)]
		elif spread_type == 10:
			break_evens = [0.00001, float(spread[1][2])+credit]
		else:
			break_evens = [float(spread[1][2])-(abs(float(spread[2][2])-float(spread[1][2]))+credit), 1000000]

		if break_evens[0] < 0.00001:
			break_evens[0] = 0.00001
		if break_evens[1] > 1000000:
			break_evens[1] = 1000000

		return break_evens

	def max_risk(self, spread, spread_type, two_sd_below, two_sd_above, four_sd_below, four_sd_above, step, credit):

		mr = 0
		two_sd_risk = 0
		if spread_type in [1, 2, 5, 8, 11, 12, 13, 14]:
			for i in range(math.floor(four_sd_below/step), math.ceil(four_sd_above/step), 1):
				pl = get_pl(spread, i*step, credit)
				if pl < mr:
					mr = pl
			mr = abs(mr)
			for i in range(math.floor(two_sd_below/step), math.ceil(two_sd_above/step), 1):
				pl = get_pl(spread, i*step, credit)
				if pl < two_sd_risk:
					two_sd_risk = pl
			two_sd_risk = abs(two_sd_risk)
		elif spread_type == 3 or spread_type == 4:
			mr = 100 * max((float(spread[4][2])-float(spread[3][2]))-credit, (float(spread[2][2])-float(spread[1][2]))-credit)
			two_sd_risk = mr
		elif spread_type == 6:
			mr = 100 * ((float(spread[2][2])-float(spread[1][2]))-(float(spread[3][2])-float(spread[2][2]))-credit)
			two_sd_risk = mr
		elif spread_type == 7 or spread_type == 10:
			mr = 100 * (float(spread[2][2])-float(spread[1][2])-credit)
			two_sd_risk = mr
		else:
			mr = 100 * ((float(spread[3][2])-float(spread[2][2]))-(float(spread[2][2])-float(spread[1][2]))-credit)
			two_sd_risk = mr

		return mr, two_sd_risk

	# Calculate metrics
	def calc_metrics(self, spread, spread_type):

		credit, liquidity = self.checks(spread)

		if credit > 0 and liquidity == True:

			dte = spread[0]

			break_evens = self.calc_break_evens(spread, spread_type, credit)

			two_sd_below, two_sd_above, four_sd_below, four_sd_above, step, mp, pop, tot_delta, tot_theta, beta_delta = self.common_metrics(spread, spread_type, break_evens, credit)

			mr, two_sd_risk = self.max_risk(spread, spread_type, two_sd_below, two_sd_above, four_sd_below, four_sd_above, step, credit)

			if mr != 0:
				roc_day = 100*(mp/two_sd_risk)/dte
			else:
				roc_day = 10000

			if mr != 0:
				theta_eff = 100*tot_theta/two_sd_risk
			else:
				theta_eff = 10000

			return [mp, mr, two_sd_risk, roc_day, break_evens, pop, tot_delta, tot_theta, beta_delta, theta_eff]

		else:

			return [0,0,0,0,[],0,0,0,0,0,0,0,0]