#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Massimo Strano, PhD
# NOTES:
# - Requires python 3 
# - There were ambiguities in the provided formulae. 
# - I made a number of assumptions in order to provide code that can be run as is.
# Please refer to the comments in the code for more information.


import sys
from datetime import datetime, timedelta
import math
from random import seed, randint, uniform, random

class Trade:
	
	"""
	
	This class implements a trade operation for a stock.
	
	"""
	
	def __init__(self, symbol, t, quantity, buyVsSell, price):
	
		"""
		Instantiate a new Trade object.
		
		Arguments:
			symbol (str): stock symbol
			t (datetime.datetime): timestamp for the trade
			quantity (int): number of stocks traded
			buyVsSell (Boolean): a flag to indicate if the trade is a purchase (True), or a sale (False)
			price (int): the initial ticker price, in pennies
		"""
		self.symbol = symbol
		self.timestamp = t
		self.quantity = quantity
		self._buyVsSell = buyVsSell
		self.price = price
		
	def isSale(self):
		"""
		Return True if this Trade was a sale
		"""
		return not self._buyVsSell
	
	def isPurchase(self):
		"""
		Return true if this trade was a purchase.
		"""
		return self._buyVsSell
	
	def __str__(self):
		"""
		Return a string representation of this Trade object.
		"""
		s = 'Trade ('
		if self._buyVsSell:
			s = s + 'Purchase) '
		else:
			s = s + 'Sale) '
		s = s + 'Quantity: ' + str(self.quantity) + ', Price: ' + str(self.price) \
			+ ' - Timestamp: ' + str(self.timestamp)
		return s

class Stock:
	
	"""
	
	This class implements a stock. This also includes a history of the trades for that 
	stock, and provides methods that rely on this history - to calculate the dividend
	yield and the P/E ratio.
	
	"""
	
	def __init__(self, symbol, initial_price, preferredVsCommon, par_value, last_dividend, fixed_dividend=0):
		"""
		Instantiate a new Stock object.
		Arguments:
			symbol (str): the stock symbol
			initial_price (int): the initial price of the stock, in pennies
			preferredVsCommon (Boolean): a flag to indicate if this is a preferred stock (True) or a common one (False)
			par_value (int): the par value of this stock, in pennies
			last_dividend (int): the last dividend of this stock, in pennies
			fixed_dividend (float): the fixed dividend of this stock - default value is 0.
		"""
		self.symbol = symbol
		self.trades = []
		self.price = initial_price
		self.preferred = preferredVsCommon
		self.par_value = par_value
		self.last_dividend = last_dividend
		self.fixed_dividend = fixed_dividend
	
	def record_trade(self, trade):
		"""
		Record a new trade on this stock and recalculate the new ticker price.
		"""
		self.trades.append(trade) 
		# Automatically recalculate the ticker price
		self.recalculate_price()
	
	def recalculate_price(self):
		"""
		Recalculate the new ticker price and return it, using the trades from
		the last 15 minutes.
		
		IMPORTANT NOTE: In the formula, there is a division by zero if there were no
		trades in the time interval considered. In this case I assumed the price
		would remain the same.
		
		"""
		current_time = datetime.now()
		fifteen_minutes = timedelta(minutes=15) 
		# Loop over the past trades, from the latest to the oldest, 
		# checking the ones that happened in the last 15 minutes, and
		# accumulating en passant the values used to calculate the stock price
		# and stopping at the first trade older than the 15 minutes threshold
		# since all the others will be older than that.
		total_qty = 0
		total_traded_value = 0
		for t in self.trades:
			time_diff = current_time - t.timestamp
			if (time_diff <= fifteen_minutes):
				total_qty = total_qty + t.quantity
				total_traded_value = total_traded_value + (t.price * t.quantity)
			else:
				# If we found a trade older than 15 minutes, all of the following ones will also be older.
				break
		# If some trades have been made in the last 15 minutes, the total quantity will
		# be greater than zero; in this case recalculate the price. Otherwise, the price will
		# be taken to remain the same, to avoid divisions by zero.
		if total_qty > 0:
			self.price = total_traded_value / total_qty
		return self.price
	
	def get_dividend_yield(self):
		"""
		Calculate and return the dividend yield for this stock.
		
		IMPORTANT NOTE: The formula for the preferred stock was ambiguous and unclear.
		Searching online provided very different formulae, because of course they do 
		not need to simplify. I had to make an assumption, and I decided that, 
		as it says only "dividend", I was going to use the last dividend value.
		It should probably be a completely different value involving the fixed dividend,
		as well as the last dividend, but this goes beyond my financial knowledge.
		
		This can be easily fixed if I am given the right formula.
		
		"""
		if self.preferred:
			return ((self.par_value * self.last_dividend) / self.price)
		else:
			return (self.last_dividend / self.price)
	
	def get_price_earnings_ratio(self):
		"""
		Calculate and return the P/E ratio for this stock. This class can
		raise an exception if the last dividend is zero, as the formula
		can't be applied in this case.
		"""
		if self.last_dividend > 0:
			return self.price / self.last_dividend
		else:
			raise ZeroDivisionError('Last dividend is zero, P/E ratio cannot be calculated')
	
	def __str__(self):
		"""
		Return a string representation of this Stock object, including the trades for it.
		"""
		s = '** Stock ('
		if self.preferred:
			s = s + 'Preferred) '
		else:
			s = s + 'Common) '
		s = s + '- Symbol: ' + self.symbol + ', Current price: ' + str(self.price) \
			+ ', Last dividend: ' + str(self.last_dividend) + ', Par value: ' + str(self.par_value) \
			+ ', Number of trades: ' + str(len(self.trades))
		for trade in self.trades:
			s = s + '\n* ' + str(trade)
		return s

class StockExchangeEngine:
	
	"""
	
	This class implements a simplified version of a subset of the tasks of a stock exchange.
	It keeps a set of stocks and of their trades, and provides methods to record
	trades and to calculate the GBCE All Share Index using the provided formulae.
	
	"""
	
	def __init__(self):
		"""
		Instantiate a new stock exchange, with an empty initial list of stocks.
		"""
		self.all_stocks = dict()
	
	def add_stock(self, symbol, initial_price, preferredVsCommon, par_value, last_dividend, fixed_dividend=0):
		"""
		Add a new stock to the stock exchange, if it doesn't already exist.
		
		This operation is idempotent.
		
		Arguments:
		
			symbol (str): the stock symbol
			initial_price (int): the initial price of the stock, in pennies
			preferredVsCommon (Boolean): a flag to indicate if this is a preferred stock (True) or a common one (False)
			par_value (int): the par value of this stock, in pennies
			last_dividend (int): the last dividend of this stock, in pennies
			fixed_dividend (float): the fixed dividend of this stock.
			
		"""
		if not (symbol in self.all_stocks):
			self.all_stocks[symbol] = Stock(symbol, initial_price, preferredVsCommon, par_value, last_dividend, fixed_dividend)
	
	def record_trade(self, symbol, trade): 
		"""
		Record a trade for a stock, if its symbol is present. Otherwise, ignore the request.
		
		Arguments:
			symbol (str): the symbol of the traded stock.
			trade (Trade): the trade to record for the given stock.
		"""
		if symbol in self.all_stocks:
			self.all_stocks[symbol].record_trade(trade)
	
	def get_all_share_index(self):
		"""
		Calculate the GBCE All Share Index, using the provided formula.
		"""
		prices_product = 1
		for stock in self.all_stocks.values():
			prices_product = prices_product * stock.price
		# Nth root of the sum of the prices!
		return math.pow(prices_product, 1/len(self.all_stocks))
	
	def get_symbols(self):
		"""
		Return a list of the symbols of all available stocks.
		"""
		return self.all_stocks.keys()
	
	def get_stock(self, symbol):
		"""
		Return the stock associated with a given symbol. If the symbol
		does not exist, return None.
		
		Argument:
			symbol (str): the wanted symbol
		"""
		if symbol in self.all_stocks:
			return self.all_stocks[symbol]
		else:
			return None

def generate_random_time_deltas(min_trades, max_trades, min_td, max_td):
	"""
	Generate a list of integers, each representing the time differential in minutes
	for a Trade from the current time. The length of the list is randomly determined,
	and it represents the number of trades to generate.
	
	Arguments:
		min_trades (int): The minimum length of the list
		max_trades (int): The maximum length of the list
		min_td (int): The minimum time differential
		max_td (int): The maximum time differential
	"""
	time_deltas = []
	no_of_trades = randint(min_trades, max_trades)
	for t_i in range(no_of_trades):
		time_deltas.append(randint(min_td, max_td))
	return sorted(time_deltas) 

def generate_random_trade(symbol, time_delta, price_variation, current_price, min_qty, max_qty):
	"""
	Generate a Trade object, with a time stamp generated from a time differential
	in minutes. The trade price and quantity are randomly generated; the price is generated
	from the current price by adding or subtracting a random quantity controlled by the
	price variation, and the quantity is a random number between the provided max and min
	quantities provided. 
	
	Arguments:
		symbol (str): The stock symbol
		time_delta (int): The value in minutes of the time differential
		price_variation (float): The percentage of variation from the initial price, used 
			to randomly determine this trade's price.
		current_price (int): The ticker price of the stock, in pennies
		min_qty (int): The minimum quantity for the trade 
		max_qty (int): The maximum quantity for the trade
	"""
	# Generate a timestamp time_delta minutes in the past
	now = datetime.now()
	a_time_delta = timedelta(minutes=time_delta)
	timestamp = now - a_time_delta
	# Generate a trade price, adding a factor to the current price obtained 
	# multiplying the current price by a random factor.
	# Uniform distribution.
	trade_price = current_price + int(current_price * uniform(-price_variation, price_variation))
	qty = randint(min_qty, max_qty)
	# Determine randomly whether this was a purchase or a sale.
	# Chances are 50-50, with uniform distribution.
	buyVsSell = True
	if random() >= 0.5:
		buyVsSell = False
	return Trade(symbol, timestamp, qty, buyVsSell, trade_price)

def main(args):
	print ('*** Simple stocks ***')
	# Simulation data
	min_trades = 6 # Min number of trades
	max_trades = 12 # Max number of trades
	min_time_delta = 1 # Min time differential for a trade - one minute ago
	max_time_delta = 45 # Max time differential for a trade - 45 minute ago
	price_variation = 0.5 # Variation for randomly generated trade prices
	min_quantity = 20 # Min quantity of traded stocks
	max_quantity = 120 # Max quantity of traded stocks
	# Sample data, taken from the Super Simple Stocks document
	#
	# NOTE: I am also adding an initial ticker price for the stocks.
	#
	dataset = [
		dict(symbol='TEA', initial_price=120, preferred=False, par_value=100, last_dividend=0, fixed_dividend=0),
		dict(symbol='POP', initial_price=150, preferred=False, par_value=100, last_dividend=8, fixed_dividend=0),
		dict(symbol='ALE', initial_price=170, preferred=False, par_value=60, last_dividend=23, fixed_dividend=0),
		dict(symbol='GIN', initial_price=190, preferred=True,  par_value=100, last_dividend=8, fixed_dividend=0.02),
		dict(symbol='JOE', initial_price=200, preferred=False, par_value=250, last_dividend=13, fixed_dividend=0)
	]
	# Instantiate stock engine and add the stocks
	se_engine = StockExchangeEngine()
	for s in dataset:
		se_engine.add_stock(s['symbol'], s['initial_price'], s['preferred'], \
		s['par_value'], s['last_dividend'], s['fixed_dividend'])
	print ('** Created stocks: ', se_engine.get_symbols())
	print()
	# Create a trade history for the stocks. The idea: generate a random list of time differentials,
	# that represent the time distance in minutes from now when a random trade occurred.
	now = datetime.now()
	for s in se_engine.get_symbols():
		current_price = se_engine.get_stock(s).price
		# Generate a list of time differential for the trades for the current stock
		time_deltas = generate_random_time_deltas(min_trades, max_trades, min_time_delta, max_time_delta)
		# For each time differential, generate a random trade operation 
		# with randomly determined price and quantity
		for td in time_deltas:
			current_trade = generate_random_trade(s, td, price_variation, current_price, min_quantity, max_quantity)
			se_engine.record_trade(s, current_trade)
		stock = se_engine.get_stock(s)
		print (str(stock))
		print ()
	print ('** Created trade history\n')
	print ('** GBCE All Share Index:', se_engine.get_all_share_index())
	# Conclusion!
	return 0

if __name__ == '__main__':
	sys.exit(main(sys.argv))
