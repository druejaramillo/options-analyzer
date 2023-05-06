import tda
from tda import auth
from tda.client import Client
from urllib.request import urlopen
import json
import datetime
from datetime import date
from datetime import timedelta
import dateutil
import atexit
import math
from scipy.stats import norm
import subprocess
import time
import re
from IV_Solver import calc_iv
from Spread_Constructor import Constructor
from Metrics import Metrics

import numpy as np

# Create/Open a file to write the best spreads to
f = open('bestspreads.txt', 'w')
f.write('\n\n\n\n------------================ Best Spreads ================------------')
f.close()

# Get authorization
consumer_key = 'TJCYE4T8WFVW3A21H7GGAGT8ULDE71FB@AMER.OAUTHAP'
redirect_uri = 'https://localhost'
token_path = 'token.pickle'

def make_webdriver():

	from selenium import webdriver
	option = webdriver.ChromeOptions()
	option.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
	driver = webdriver.Chrome(chrome_options = option)
	atexit.register(lambda: driver.quit())
	return driver

c = auth.easy_client(consumer_key, redirect_uri, token_path, make_webdriver)

# ------------ Ask the user for tickers and then get implied volatility data ------------

tickers = []
und_IVs = []

print('\n\nPlease input tickers to analyze:')
print('\nFormat your input as a list of ticker symbols (not case sensitive) separated by commas.')
inputs = input('\n> ')

print('\n\nBeginning program...')
time0 = datetime.datetime.now()

data = inputs.split(',')
for i in range(len(data)):
	data[i] = re.sub('\s+', '', data[i])
for i in range(len(data)):
	ticker = data[i].upper()
	try:
		IV = calc_iv(ticker, c)
	except:
		continue
	else:
		tickers.append(ticker)
		und_IVs.append(IV)

# ------------ Get some account info -------------

r = c.get_account(455323944)
assert r.status_code == 200
info = r.json()

net_liquid_value = info['securitiesAccount']['currentBalances']['liquidationValue']
max_bpr = net_liquid_value * 0.05

# Find the first friday of the year
first_friday = datetime.date(date.today().year, 1, 1)
while first_friday.isoweekday() != 5:
	first_friday = first_friday + timedelta(days=1)

# Get the next 2 expiration dates
# Then calculate the DTEs
def get_next_expirations():

	future_fridays = []
	for i in range(105):
		if first_friday + timedelta(days = (7*i)) > date.today():
			future_fridays.append(first_friday + timedelta(days = (7*i)))

	future_exp_dates = []
	for i in range(len(future_fridays)):
		if (future_fridays[i].day >= 15 and future_fridays[i].day <= 21):
			future_exp_dates.append(future_fridays[i])

	next_expirations = []
	for i in range(len(future_exp_dates)):
		diff = future_exp_dates[i] - date.today()
		if diff <= timedelta(days=60) and diff >= timedelta(days=30):
			next_expirations.append(future_exp_dates[i])

	days_to_exp = []
	for i in range(len(next_expirations)):
		days_to_exp.append((next_expirations[i] - date.today()).days)

	return next_expirations, days_to_exp

expirations, dtes = get_next_expirations()

# Initialize some variables
call_chains = []
put_chains = []
call_strikes = []
put_strikes = []
cs_keys = []
ps_keys = []
und_price = 0
und_IV = 0

time1 = datetime.datetime.now()
print('\n\nTime to process tickers, get expirations, and define functions: ' + str(time1 - time0))

# ------------ Run the program for each ticker ------------

f = open('bestspreads.txt', 'a')

for ticker_counter in range(len(tickers)):

	time1 = datetime.datetime.now()

	ticker = tickers[ticker_counter]
	und_IV = und_IVs[ticker_counter]

	print('\n\n================================ {ticker} ================================'.format(ticker = ticker))

	# ------------ Get the underlying's current price and beta -------------

	r = c.get_quote(ticker)
	if r.status_code == 429:
		print('API Call Limit Reached. Waiting 60 seconds...')
		time.sleep(60)
		r = c.get_quote(ticker)
	if r.status_code != 200:
		continue
	quote = r.json()

	und_price = quote[ticker]['lastPrice']

	r = c.search_instruments(ticker, Client.Instrument.Projection.FUNDAMENTAL)
	if r.status_code == 429:
		print('API Call Limit Reached. Waiting 60 seconds...')
		time.sleep(60)
		r = c.search_instruments(ticker, Client.Instrument.Projection.FUNDAMENTAL)
	if r.status_code != 200:
		continue
	fundamentals = r.json()

	und_beta = fundamentals[ticker]['fundamental']['beta']

	print('\n\nPrice: $' + str(und_price))
	print('Beta: ' + str(und_beta))
	print('Implied Volatility: ' + str(round(100*und_IV, 2)) + '%')

	# Reset arrays we'll need
	call_chains = []
	put_chains = []
	call_strikes = []
	put_strikes = []
	cs_keys = []
	ps_keys = []

	for i in range(len(dtes)):

		# ---------- Get the options chains ----------------

		r = c.get_option_chain(ticker, contract_type = Client.Options.ContractType.CALL,
			from_date = expirations[i] - timedelta(days = 1),
			to_date = expirations[i] + timedelta(days = 1))
		if r.status_code == 429:
			print('API Call Limit Reached. Waiting 60 seconds...')
			time.sleep(60)
			r = c.get_option_chain(ticker, contract_type = Client.Options.ContractType.CALL,
				from_date = expirations[i] - timedelta(days = 1),
				to_date = expirations[i] + timedelta(days = 1))	
		if r.status_code != 200:
			continue
		call_chain = r.json()
		call_chains.append(call_chain)

		r = c.get_option_chain(ticker, contract_type = Client.Options.ContractType.PUT,
			from_date = expirations[i] - timedelta(days = 1),
			to_date = expirations[i] + timedelta(days = 1))
		if r.status_code == 429:
			print('API Call Limit Reached. Waiting 60 seconds...')
			time.sleep(60)
			r = c.get_option_chain(ticker, contract_type = Client.Options.ContractType.PUT,
				from_date = expirations[i] - timedelta(days = 1),
				to_date = expirations[i] + timedelta(days = 1))	
		if r.status_code != 200:
			call_chains.pop()
			continue
		put_chain = r.json()
		put_chains.append(put_chain)

	if call_chains == [] or put_chains == []:
		continue

	# Initialize final arrays
	strangles = []
	straddles = []
	iron_butterflies = []
	iron_condors = []

	jade_lizards = []
	put_bwbs = []
	short_put_spreads = []

	reverse_jade_lizards = []
	call_bwbs = []
	short_call_spreads = []

	put_ratio_spreads = []
	call_ratio_spreads = []
	super_bulls = []
	super_bears = []

	all_spreads = [strangles, straddles, iron_butterflies, iron_condors, jade_lizards, put_bwbs, short_put_spreads, reverse_jade_lizards, call_bwbs, short_call_spreads, put_ratio_spreads, call_ratio_spreads, super_bulls, super_bears]

	time2 = datetime.datetime.now()
	print('\n\nTime to get data and initialize variables: ' + str(time2 - time1))

	# ------------- Construct Spreads --------------

	# Initialize spread-counting variable
	count = 0

	# Make the spread constructor
	constructor = Constructor()

	for dte in range(len(dtes)):

		print('\n\n-------- Constructing Expiration Month {dte} --------'.format(dte = dte+1))
		print('\n\nBeginning construction...')

		actual_dte = dtes[dte]
		call_chain = call_chains[dte]
		put_chain = put_chains[dte]

		# Filter for the data we'll need later
		temp = int(actual_dte)
		if datetime.datetime.now().hour >= 22: # Adjust for difference between Mountain and Eastern timezones
			temp -= 1
		temp = str(temp)
		c_strikes = call_chain['callExpDateMap'][expirations[i].isoformat()+':'+temp]
		p_strikes = put_chain['putExpDateMap'][expirations[i].isoformat()+':'+temp]

		call_strikes.append(c_strikes)
		put_strikes.append(p_strikes)

		# Get the keys for the strike JSON array so we can go through it
		cs_keys_temp = list(c_strikes.keys())
		ps_keys_temp = list(p_strikes.keys())

		# Narrow down our strikes to just past +/- 2 std. devs. from the current price
		l_bound = und_price - 2.1 * und_IV * und_price * math.sqrt(dtes[i]/365)
		u_bound = und_price + 2.1 * und_IV * und_price * math.sqrt(dtes[i]/365)

		for j in range(len(cs_keys_temp)-1, -1, -1):
			if (float(cs_keys_temp[j]) < l_bound or float(cs_keys_temp[j]) > u_bound):
				cs_keys_temp.pop(j)

		for j in range(len(ps_keys_temp)-1, -1, -1):
			if (float(ps_keys_temp[j]) < l_bound or float(ps_keys_temp[j]) > u_bound):
				ps_keys_temp.pop(j)

		cs_keys.append(cs_keys_temp)
		ps_keys.append(ps_keys_temp)

		# Construct the spreads
		count, spreads = constructor.construct_spreads(actual_dte, ps_keys[dte], cs_keys[dte])
		for i in range(len(spreads)):
			for j in range(len(spreads[i])):
				all_spreads[i].append(spreads[i][j])

	print('\n\nConstruction complete')
	print('Total spreads: ' + str(count))
	time3 = datetime.datetime.now()
	print('Time to construct spreads: ' + str(time3 - time2))

	count = 0

	print('\n\n-------- Analyzing Spreads --------')
	print('\n\nBeginning analysis...')

	# Analyze each group of spreads
	# If it doesn't meet the requirements, remove it from the list
	# If it does meet the requirements, append the metrics
	# Reminder: metrics = [mp, mr, 2sd_risk, roc_day, break_evens, pop, tot_delta, tot_theta, beta_delta, theta_eff]

	# Make the metric calculator
	calculator = Metrics(dtes, put_strikes, call_strikes, und_price, und_beta, und_IV)

	for spread_type in range(len(all_spreads)):
		for i in range(len(all_spreads[spread_type])-1, -1, -1):

			metrics = calculator.calc_metrics(all_spreads[spread_type][i], spread_type+1)

			if metrics[3] > 0.25 and metrics[5] > 60 and metrics[0] > 0 and metrics[2] < max_bpr and metrics[9] > 0.25:
				metrics.append(calculator.expected_value(all_spreads[spread_type][i]))
				if metrics[10] > -5:
					all_spreads[spread_type][i].append(metrics)
					count += 1
				else:
					all_spreads[spread_type].pop(i)
			else:
				all_spreads[spread_type].pop(i)

	print('\n\nAnalysis complete')
	print('Total valid spreads: ' + str(count))
	time4 = datetime.datetime.now()
	print('Time to analyze spreads: ' + str(time4 - time3))

	# ------------- Output the best spreads to the file -------------
	# Only if the number of valid spreads is nonzero

	if count != 0:

		f.write('\n\n================== {ticker} =================='.format(ticker = ticker))

		for counter in range(len(all_spreads)):

			if len(all_spreads[counter]) != 0:

				if counter+1 == 1:
					f.write('\n\nStrangles:')
				elif counter+1 == 2:
					f.write('\n\nStraddles:')
				elif counter+1 == 3:
					f.write('\n\nIron Butterflies:')
				elif counter+1 == 4:
					f.write('\n\nIron Condors:')
				elif counter+1 == 5:
					f.write('\n\nJade Lizards:')
				elif counter+1 == 6:
					f.write('\n\nPut BWBs:')
				elif counter+1 == 7:
					f.write('\n\nShort Put Spreads:')
				elif counter+1 == 8:
					f.write('\n\nReverse Jade Lizards:')
				elif counter+1 == 9:
					f.write('\n\nCall BWBs:')
				elif counter+1 == 10:
					f.write('\n\nShort Call Spreads:')
				elif counter+1 == 11:
					f.write('\n\nPut Ratio Spreads:')
				elif counter+1 == 12:
					f.write('\n\nCall Ratio Spreads:')
				elif counter+1 == 13:
					f.write('\n\nSuper Bulls:')
				else:
					f.write('\n\nSuper Bears:')

				for dte in range(len(dtes)):
					for i in range(len(all_spreads[counter])-1, -1, -1):

						spread = all_spreads[counter][i]
						if spread[0] == dtes[dte]:

							metrics = spread[len(spread)-1]

							f.write('\n\n' + expirations[dte].strftime('%b %d %Y'))
							for j in range(1, len(spread)):
								if len(spread[j]) == 3:
									f.write('\n\t' + str(spread[j]))
							f.write('\n\t\tMax Profit: $' + str(round(metrics[0], 2)))
							f.write('\n\t\tMax Risk: $' + str(round(metrics[1], 2)))
							f.write('\n\t\t2 SD Risk: $' + str(round(metrics[2], 2)))
							f.write('\n\t\tROC/Day: ' + str(round(metrics[3], 2)) + '%')
							f.write('\n\t\tBreak-Evens:')
							f.write('\n\t\t\tLow: $' + str(round(metrics[4][0], 2)))
							f.write('\n\t\t\tHigh: $' + str(round(metrics[4][1], 2)))
							f.write('\n\t\tProb. of Profit: ' + str(round(metrics[5], 2)) + '%')
							f.write('\n\t\tExpected Value: $' + str(round(metrics[10], 2)))
							f.write('\n\t\tTotal Delta: ' + str(round(metrics[6], 2)))
							f.write('\n\t\tTotal Theta: ' + str(round(metrics[7], 2)))
							f.write('\n\t\tBeta-Weighted Delta: ' + str(round(metrics[8], 2)))
							f.write('\n\t\tTheta Efficiency: ' + str(round(metrics[9], 2)) + '%')

							all_spreads[counter].pop(i)

f.write('\n\n\n\n')
f.close()

subprocess.call(['open', '-a', 'TextEdit', 'bestspreads.txt'])
time_end = datetime.datetime.now()
print('\n\n\n\n============================================================================')
print('\n\nTotal Runtime: ' + str(time_end - time0))
print('\n\n============================================================================')
print('\n\n')