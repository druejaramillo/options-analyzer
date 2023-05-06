import tda
from tda import auth
from tda.client import Client
from urllib.request import urlopen
import json
import datetime
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil
import math
import sys
import time

# Get the necessary data
def get_options(ticker, c):

	# Import options chain
	r = c.get_option_chain(ticker, to_date = date.today() + timedelta(days = 60))
	if r.status_code == 429:
		print('API Call Limit Reached. Waiting 60 seconds...')
		time.sleep(60)
		r = c.get_option_chain(ticker, to_date = date.today() + timedelta(days = 60))
	assert r.status_code == 200
	chain = r.json()

	# Separate puts and calls
	all_puts = chain['putExpDateMap']
	all_calls = chain['callExpDateMap']

	# Get the expiration dates
	exp_dates = list(all_puts.keys())
	for i in range(len(exp_dates)):
		temp = exp_dates[i].split(':')
		exp_dates[i] = temp[0]

	# Find the expiration dates surrounding 30 days from now
	thirty_days = date.today() + timedelta(days = 30)
	near_date = ''
	next_date = ''
	found = False
	i = 0
	while not found:

		near_date = exp_dates[i]
		next_date = exp_dates[i+1]

		if date.fromisoformat(next_date) > thirty_days:
			found = True
		
		i += 1

	# Calculate the DTEs
	temp = date.fromisoformat(near_date) - date.today()
	near_dte = temp.days
	temp = date.fromisoformat(next_date) - date.today()
	next_dte = temp.days

	if datetime.now().hour >= 22:
		near_dte -= 1
		next_dte -= 1

	# Extract the corresponding put and call chains
	near_puts_temp = all_puts[near_date+':'+str(near_dte)]
	near_calls_temp = all_calls[near_date+':'+str(near_dte)]
	next_puts_temp = all_puts[next_date+':'+str(next_dte)]
	next_calls_temp = all_calls[next_date+':'+str(next_dte)]

	# Extract only the necessary data
	near_pstrikes = list(near_puts_temp.keys())
	next_pstrikes = list(next_puts_temp.keys())
	near_puts = []
	near_calls = []
	next_puts = []
	next_calls = []
	for i in range(len(near_puts_temp)):
		strike = near_pstrikes[i]
		put_price = near_puts_temp[strike][0]['last']
		call_price = near_calls_temp[strike][0]['last']
		bid_size = near_puts_temp[strike][0]['bidSize']
		if bid_size > 0 and put_price != 0 and call_price != 0:
			near_puts.append([float(strike), put_price])
			near_calls.append([float(strike), call_price])
	for i in range(len(next_puts_temp)):
		strike = next_pstrikes[i]
		put_price = next_puts_temp[strike][0]['last']
		call_price = next_calls_temp[strike][0]['last']
		bid_size = next_puts_temp[strike][0]['bidSize']
		if bid_size > 0 and put_price != 0 and call_price != 0:
			next_puts.append([float(strike), put_price])
			next_calls.append([float(strike), call_price])

	return near_puts, near_calls, next_puts, next_calls, near_dte, next_dte

# Perform the calculation
def calc_iv(ticker, c):

	# Get the data
	near_puts, near_calls, next_puts, next_calls, near_dte, next_dte = get_options(ticker, c)

	# Risk-free rate
	r = 0.0005

	# Calculate sigma^2 for near expiration

	minimum = sys.maxsize
	temp = 0
	j = 0
	for i in range(len(near_puts)):
		temp = abs(near_calls[i][1] - near_puts[i][1])
		if temp < minimum:
			minimum = temp
			j = i

	T_near = near_dte/365

	F = near_puts[j][0] + math.exp(r*T_near) * abs(near_calls[j][1] - near_puts[j][1])

	temp = 0
	i = 0
	while temp < F:
		temp = near_puts[i][0]
		i += 1
	K_star = near_puts[i-2][0]

	temp = 0
	for i in range(len(near_puts)):

		delta = 0
		if i == 0:
			delta = near_puts[1][0] - near_puts[0][0]
		elif i == (len(near_puts) - 1):
			delta = near_puts[len(near_puts)-1][0] - near_puts[len(near_puts)-2][0]
		else:
			delta = 0.5 * (near_puts[i+1][0] - near_puts[i-1][0])

		M = 0
		if near_puts[i][0] < K_star:
			M = near_puts[i][1]
		elif near_puts[i][0] > K_star:
			M = near_calls[i][1]
		else:
			M = 0.5 * (near_puts[i][1] + near_calls[i][1])

		temp += delta / pow(near_puts[i][0], 2) * math.exp(r*T_near) * M

	sigma_sq_near = 2 / T_near * temp - 1 / T_near * pow((F / K_star - 1), 2)

	# Calculate sigma^2 for next expiration

	minimum = sys.maxsize
	temp = 0
	j = 0
	for i in range(len(next_puts)):
		temp = abs(next_calls[i][1] - next_puts[i][1])
		if temp < minimum:
			minimum = temp
			j = i

	T_next = next_dte/365

	F = next_puts[j][0] + math.exp(r*T_next) * abs(next_calls[j][1] - next_puts[j][1])

	temp = 0
	i = 0
	while temp < F:
		temp = next_puts[i][0]
		i += 1
	K_star = next_puts[i-2][0]

	temp = 0
	for i in range(len(next_puts)):

		delta = 0
		if i == 0:
			delta = next_puts[1][0] - next_puts[0][0]
		elif i == (len(next_puts) - 1):
			delta = next_puts[len(next_puts)-1][0] - next_puts[len(next_puts)-2][0]
		else:
			delta = 0.5 * (next_puts[i+1][0] - next_puts[i-1][0])

		M = 0
		if next_puts[i][0] < K_star:
			M = next_puts[i][1]
		elif next_puts[i][0] > K_star:
			M = next_calls[i][1]
		else:
			M = 0.5 * (next_puts[i][1] + next_calls[i][1])

		temp += delta / pow(next_puts[i][0], 2) * math.exp(r*T_next) * M

	sigma_sq_next = 2 / T_next * temp - 1 / T_next * pow((F / K_star - 1), 2)

	# Calculate IV

	N_thirty = 43200
	N_near = near_dte * 1440 + 600
	N_next = next_dte * 1440 + 600

	V_sq = (T_near * sigma_sq_near * ((N_next - N_thirty) / (N_next - N_near)) + T_next * sigma_sq_next * ((N_thirty - N_near) / (N_next - N_near))) * 365 / 30

	IV = math.sqrt(V_sq)

	return IV