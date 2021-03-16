import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import yahoo_fin.stock_info as si
import requests
from bs4 import BeautifulSoup

# ---------------------------
# CLASSES
# ---------------------------

'''
Algo class. Initialized with a (string) name, and a (function) decision_engine
The decision_engine is a function that takes in a given portfolio dict and datetime date 
and decides what to do on that given date, whether to buy, sell, do nothing, etc.
'''
class Algo:
	def __init__(self, name, decision_engine):
		self.decision_engine = decision_engine
		self.name = name

'''
Portfolio object format
{
	'amzn' : {
		'shares' : '10',
		'purchase_price' : '128.55'
	},
	'cash' : 2000
}
'''

# ---------------------------
# UTILITY FUNCTIONS
# ---------------------------

'''
get_stock function returns the opening and closing price of a stock on a given day
(string) ticker, (datetime) date -> dictionary with open and close price (string to float)
'''
def get_stock(ticker, date):
	# format:
	# 			open			high				low				close				adj close		vol		tkr
	# [[757.9199829101562, 758.760009765625, 747.7000122070312, 753.6699829101562, 753.6699829101562, 3521100, 'AMZN']]
	res = si.get_data(ticker, start_date = date.strftime("%m-%d-%Y"), end_date = (date + timedelta(days=1)).strftime("%m-%d-%Y")).values.tolist()[0]
	return {'open': res[0], 'close': res[3]}

def sma(ticker, interval, date):
	# we call this on a specific trading day, we can only know the SMA of the previous X days. So technically this is 
	# the SMA of the previous day using the close prices
	# fetch the last 12 days to be safe and not miss data from holidays and weekends
	# we'll take only the last 5
	res = si.get_data(ticker, start_date = (date - timedelta(days=12)).strftime("%m-%d-%Y"), end_date = date.strftime("%m-%d-%Y")).values.tolist()[-interval:]
	closes = []
	for result in res:
		closes.append(result[3])
	return sum(closes) / len(closes)

def sma_volume(ticker, interval, date):
	# we call this on a specific trading day, we can only know the SMA of the previous X days. So technically this is 
	# the SMA of the previous day using the close prices
	# fetch the last 12 days to be safe and not miss data from holidays and weekends
	# we'll take only the last 5
	res = si.get_data(ticker, start_date = (date - timedelta(days=12)).strftime("%m-%d-%Y"), end_date = date.strftime("%m-%d-%Y")).values.tolist()[-interval:]
	closes = []
	for result in res:
		closes.append(result[5])
	return sum(closes) / len(closes)

def get_openinsider(url):
	req = requests.get(url, headers={"content-type":"text"})
	soup = BeautifulSoup(req.content, 'html.parser')
	table = []
	for row in soup.select('thead tr'):
		table.append([x.text for x in row.find_all('th')])
	for row in soup.select('tbody tr'):
		table.append([x.text for x in row.find_all('td')])
	# this is a cool table, but for now lets just grab the ticker
	if len(table) > 0:
		return table[2][3].strip()
	else:
		return ''

def limit_sells(portfolio, date, stop_loss, stop_gain):
	# cannot change dictionary size during iteration
	# therefore can't use syntax ticker 'in portfolio'
	# need to forrce a separate copy of list of keys, not an iterator of actual dict
	for ticker in list(portfolio):
		if ticker != 'cash':
			stock = get_stock(ticker, date)
			if (stock['open'] < (1 - stop_loss) * portfolio[ticker]['purchase_price']):
				# at open, we're below stop loss
				holdings = portfolio.pop(ticker)
				portfolio['cash'] += holdings['shares'] * stock['open']
			elif (stock['open'] > (1 + stop_gain) * portfolio[ticker]['purchase_price']):
				# at open, we're above the stop gain
				holdings = portfolio.pop(ticker)
				portfolio['cash'] += holdings['shares'] * stock['open']
			elif (stock['close'] < (1 - stop_loss) * portfolio[ticker]['purchase_price']):
				# at close, we're below stop loss
				holdings = portfolio.pop(ticker)
				portfolio['cash'] += holdings['shares'] * stock['close']
			elif (stock['close'] > (1 + stop_gain) * portfolio[ticker]['purchase_price']):
				# at close, we're above stop gain
				holdings = portfolio.pop(ticker)
				portfolio['cash'] += holdings['shares'] * stock['close']
	return portfolio


def sell(portfolio, ticker, shares, sell_price):
	try:
		if portfolio[ticker]['shares'] - shares < 0:
			print('Cannot sell that many shares')
		else:
			portfolio[ticker]['shares'] -= shares
			portfolio['cash'] += shares * sell_price
	except:
		print("Don't own the stock trying to be sold")
	finally:
		return portfolio

def sell_all(portfolio, ticker, sell_price):
	try:
		holdings = portfolio.pop(ticker)
		portfolio['cash'] += holdings['shares'] * stock['open']
	except:
		print("Don't own the stock trying to be sold")
	finally:
		return portfolio

def buy(portfolio, ticker, shares, purchase_price):
	pass
	#todo




'''
calculate_portfolio_value function returns the total portfolio worth at close on given date
(dict) portfolio, (datetime) date -> (float) total
'''
def calculate_portfolio_value(portfolio, date):
	total = 0
	total += portfolio['cash']
	for ticker in portfolio:
		if ticker == 'cash':
			continue
		else:
			closing_price_on_date = si.get_data(ticker, start_date = date.strftime("%m-%d-%Y"), end_date = (date + timedelta(days=1)).strftime("%m-%d-%Y")).values.tolist()[0][3]
			shares = portfolio[ticker]['shares']
			total += (closing_price_on_date * shares)
	return total

# ---------------------------
# INDICATORS
# ---------------------------

'''
if the 5-day SPY SMA is increasing return true
'''
def fiveday_spy_sma_3_apart_indicator(date):
	return (sma('spy', 5, date) - sma('spy', 5, date - timedelta(days=2))) > 0

'''
if the 5-day SPY SMA volume is increasing return true
'''
def fiveday_spy_vol_sma_3_apart_indicator(date):
	return (sma_volume('spy', 5, date) - sma_volume('spy', 5, date - timedelta(days=2))) > 0

# ---------------------------
# DECISION ENGINES
# ---------------------------

'''
sample decision_engine no-op
(dict) portfolio, (datetime) date -> (dict) portfolio
'''
def noop_engine(portfolio, date):
	return portfolio

'''
basic_stock_engine to buy a single stock when enough cash and hold onto it
(dict) portfolio, (datetime) date, [optional] (string) ticker -> (dict) portfolio
'''
def basic_stock_engine(portfolio, date, ticker='spy'):
	try:
		# include get_stock in try block in case the yahoo finance api can't find stock data
		# if it fails, return portfolio itself
		stock = get_stock(ticker, date)
		if portfolio['cash'] > stock['open']:
			units_to_buy = portfolio['cash'] // stock['open']
			# if we buy a stock that already exists, average the purchase price and add the shares
			if ticker in portfolio:
				portfolio[ticker] = {'shares': units_to_buy + portfolio[ticker]['shares'], 'purchase_price': (stock['open'] * units_to_buy + portfolio[ticker]['purchase_price'] * portfolio[ticker]['shares']) / (units_to_buy + portfolio[ticker]['shares'])}
			else:
				portfolio[ticker] = {'shares': units_to_buy, 'purchase_price': stock['open']}
			portfolio['cash'] -= (units_to_buy * stock['open'])
	except:
		pass
	return portfolio

def basic_msft_stock_engine(portfolio, date, ticker='msft'):
	return basic_stock_engine(portfolio, date, ticker)

def basic_arkk_stock_engine(portfolio, date, ticker='arkk'):
	return basic_stock_engine(portfolio, date, ticker)

def openinsider_cluster_stock_engine(pf, date, stop_loss=0.05, stop_gain=0.02):
	portfolio = limit_sells(pf, date, stop_loss, stop_loss)
	date2 = date.strftime("%m-%d-%Y").replace('-', '%2F')
	date1 = (date - timedelta(days=2)).strftime("%m-%d-%Y").replace('-', '%2F')
	url = "http://openinsider.com/screener?s=&o=&pl=3&ph=&ll=&lh=&fd=90&fdr=&td=-1&tdr=" + date1 + "+-+" + date2 + "&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=2&nfl=&nfh=&nil=4&nih=&nol=0&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"
	stock = get_openinsider(url)
	if stock != '':
		return basic_stock_engine(portfolio, date, stock)
	else:
		return portfolio

def openinsider_cluster_stock_engine2(pf, date, stop_loss=0.05, stop_gain=0.02):
	portfolio = limit_sells(pf, date, stop_loss, stop_loss)
	if not fiveday_spy_vol_sma_3_apart_indicator(date):
		return portfolio
	date2 = date.strftime("%m-%d-%Y").replace('-', '%2F')
	date1 = (date - timedelta(days=2)).strftime("%m-%d-%Y").replace('-', '%2F')
	url = "http://openinsider.com/screener?s=&o=&pl=3&ph=&ll=&lh=&fd=90&fdr=&td=-1&tdr=" + date1 + "+-+" + date2 + "&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=2&nfl=&nfh=&nil=4&nih=&nol=0&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"
	stock = get_openinsider(url)
	if stock != '':
		return basic_stock_engine(portfolio, date, stock)
	else:
		return portfolio

def openinsider_cluster_stock_engine3(pf, date, stop_loss=0.02, stop_gain=0.02):
	portfolio = limit_sells(pf, date, stop_loss, stop_loss)
	date2 = date.strftime("%m-%d-%Y").replace('-', '%2F')
	date1 = (date - timedelta(days=2)).strftime("%m-%d-%Y").replace('-', '%2F')
	url = "http://openinsider.com/screener?s=&o=&pl=&ph=5&ll=&lh=&fd=0&fdr=&td=-1&tdr=" + date1 + "+-+" + date2 + "&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=8&cnt=100&page=1"
	stock = get_openinsider(url)
	if stock != '':
		return basic_stock_engine(portfolio, date, stock)
	else:
		return portfolio

def openinsider_cluster_stock_engine4(pf, date, stop_loss=0.05, stop_gain=0.02):
	portfolio = limit_sells(pf, date, stop_loss, stop_loss)
	date2 = date.strftime("%m-%d-%Y").replace('-', '%2F')
	date1 = (date - timedelta(days=2)).strftime("%m-%d-%Y").replace('-', '%2F')
	url = "http://openinsider.com/screener?s=&o=&pl=&ph=50&ll=&lh=&fd=0&fdr=&td=-1&tdr=" + date1 + "+-+" + date2 + "&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=8&cnt=100&page=1"
	stock = get_openinsider(url)
	if stock != '':
		return basic_stock_engine(portfolio, date, stock)
	else:
		return portfolio

def openinsider_cluster_stock_engine5(pf, date, stop_loss=0.08, stop_gain=0.05):
	portfolio = limit_sells(pf, date, stop_loss, stop_loss)
	date2 = date.strftime("%m-%d-%Y").replace('-', '%2F')
	date1 = (date - timedelta(days=2)).strftime("%m-%d-%Y").replace('-', '%2F')
	url = "http://openinsider.com/screener?s=&o=&pl=&ph=5&ll=&lh=&fd=0&fdr=&td=-1&tdr=" + date1 + "+-+" + date2 + "&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=8&cnt=100&page=1"
	stock = get_openinsider(url)
	if stock != '':
		return basic_stock_engine(portfolio, date, stock)
	else:
		return portfolio

def openinsider_cluster_stock_engine6(pf, date, stop_loss=0.05, stop_gain=0.02):
	portfolio = limit_sells(pf, date, stop_loss, stop_loss)
	date2 = date.strftime("%m-%d-%Y").replace('-', '%2F')
	date1 = (date - timedelta(days=2)).strftime("%m-%d-%Y").replace('-', '%2F')
	url = "http://openinsider.com/screener?s=&o=&pl=&ph=5&ll=&lh=&fd=0&fdr=&td=-1&tdr=" + date1 + "+-+" + date2 + "&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=8&cnt=100&page=1"
	stock = get_openinsider(url)
	if stock != '':
		return basic_stock_engine(portfolio, date, stock)
	else:
		return portfolio


def openinsider_cluster_stock_engine7(pf, date, stop_loss=0.05, stop_gain=0.02):
	portfolio = limit_sells(pf, date, stop_loss, stop_loss)
	date2 = date.strftime("%m-%d-%Y").replace('-', '%2F')
	date1 = (date - timedelta(days=2)).strftime("%m-%d-%Y").replace('-', '%2F')
	url = "http://openinsider.com/screener?s=&o=&pl=&ph=6&ll=&lh=&fd=0&fdr=&td=-1&tdr=" + date1 + "+-+" + date2 + "&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=2&nfl=&nfh=&nil=3&nih=&nol=0&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=8&cnt=100&page=1"
	stock = get_openinsider(url)
	if stock != '':
		return basic_stock_engine(portfolio, date, stock)
	else:
		return portfolio

def openinsider_cluster_stock_engine8(pf, date, stop_loss=0.05, stop_gain=0.02):
	portfolio = limit_sells(pf, date, stop_loss, stop_loss)
	if not fiveday_spy_sma_3_apart_indicator(date):
		return portfolio
	date2 = date.strftime("%m-%d-%Y").replace('-', '%2F')
	date1 = (date - timedelta(days=2)).strftime("%m-%d-%Y").replace('-', '%2F')
	url = "http://openinsider.com/screener?s=&o=&pl=&ph=5&ll=&lh=&fd=0&fdr=&td=-1&tdr=" + date1 + "+-+" + date2 + "&fdlyl=&fdlyh=&daysago=&xp=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&isofficer=1&iscob=1&isceo=1&ispres=1&iscoo=1&iscfo=1&isgc=1&isvp=1&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=8&cnt=100&page=1"
	stock = get_openinsider(url)
	if stock != '':
		return basic_stock_engine(portfolio, date, stock)
	else:
		return portfolio
		
'''
theres a lot of room to fiddle arround with adding overrall market indicator flags, sort by different things, different stop limits
zacks doesn't look accessible, but maybe i could use a stock screener for undersold and highest volume
also print actual transactions
'''

# try with zachs picks or something?

	


'''
Backtester class. Initialized with a (datetime) start_date and end_date, (list) array of
algo objects to backtest, and (int) starting portfolio cash. Log portfolio worth each day
and graph with matplotlib
'''
class Backtester:

	def __init__(self, start_date, end_date, algos, starting_wallet):
		self.start_date = datetime.strptime(start_date, '%m-%d-%Y')
		self.end_date = datetime.strptime(end_date, '%m-%d-%Y')
		self.algos = algos
		self.cash = starting_wallet
		self.run = False
		self.portfolios = {algo.name: {'cash': starting_wallet} for algo in self.algos}
		self.dates = []
		self.portfolio_values = {algo.name: [] for algo in self.algos}
		

	def backtest(self):
		delta = timedelta(days=1)
		while self.start_date < self.end_date:
			print(self.start_date.strftime("%m-%d-%Y"))
			# skip over all weekends
			if (self.start_date.weekday() < 5 ):
				try:
					# check if valid trading day (not holiday)
					test_data = si.get_data("amzn", start_date = self.start_date.strftime("%m-%d-%Y"), end_date = (self.start_date + delta).strftime("%m-%d-%Y"))

					self.dates.append(self.start_date)
					for algo in self.algos:
						# run engine and update portfolio for this day
						try:
							self.portfolios[algo.name] = algo.decision_engine(self.portfolios[algo.name], self.start_date)
						except Exception as e:
							print('THE DECISION ENGINE FAILED ', algo.name, e)
						# log the portfolio value
						self.portfolio_values[algo.name].append(calculate_portfolio_value(self.portfolios[algo.name], self.start_date))
				except:
					# not a valid trading day
					pass
			self.start_date += delta
		self.run = True
		return

	def graph(self):
		if not self.run:
			self.backtest()

		# plot config
		plt.style.use('seaborn-darkgrid') # style
		palette = plt.get_cmap('Set1') # line colors
		fig, ax = plt.subplots(constrained_layout=True)
		locator = mdates.AutoDateLocator() # date formatter on axis
		formatter = mdates.ConciseDateFormatter(locator)
		ax.xaxis.set_major_locator(locator)
		ax.xaxis.set_major_formatter(formatter)
		plt.title("Backtester", loc='left', fontsize=14, fontweight=0, color='black')
		plt.ylabel("Portfolio Value ($)")

		# plot algos
		for index, ticker in enumerate(self.portfolios):
			ax.plot(self.dates, self.portfolio_values[ticker], marker='', color=palette(index), linewidth=2, alpha=0.9, label=ticker)
		plt.legend(loc=2, ncol=2) # legend top left
		plt.show()

		return


if __name__ == '__main__':
	# could make these dates and starting funds command line arguments
	start = '1-01-2021'
	end = '3-05-2021'
	algos = [Algo('nop', noop_engine), Algo('spy', basic_stock_engine), Algo('arkk', basic_arkk_stock_engine), Algo('cluster3', openinsider_cluster_stock_engine3), Algo('cluster4', openinsider_cluster_stock_engine4), Algo('cluster5', openinsider_cluster_stock_engine5), Algo('cluster6', openinsider_cluster_stock_engine6), Algo('cluster7', openinsider_cluster_stock_engine7), Algo('cluster8', openinsider_cluster_stock_engine8)]
	starting_funds = 2000

	bt = Backtester(start, end, algos, starting_funds)
	bt.graph()







'''

trending up
1. 
Under $50
Performance: Week Up
20-Day Simple Moving Average: Price above SMA
50-Day Simple Moving Average: Price above SMA
200-Day Simple Moving Average: Price above SMA
Change: Up
Relative Volume: Over 1
Gap: Up 3%
Change from Open: Up
https://daytradingz.com/how-to-use-finviz/#Best_Finviz_Scans

reversing up
2.
Under $50
20-Day Simple Moving Average: Price above SMA
50-Day Simple Moving Average: Price below SMA
200-Day Simple Moving Average: Price below SMA
Average volume over 500k
EPS growth: over 20%

dekmar breakout
3.
Under $10
RSI Oversold (40) (bottom of their pattern, we don't want overbought but underbought about to spike but currently dipping)
Relative Volume Over 3 (3x our average volume)
Change Up (optional, green day today)
Today Up (optional)
Click ownership tab, sort by float (lowest at the top) (under 8 mil float)
Look thru the first 8 or so

continuation setting (long play probly)
4.
Performance Today Up
Under $10
Performance 2 Today +15%
Change Up
Change from Open IP
Current Volume Over 200k

swing trade (overnight trade up to two week hold)
5.
Market Cap Mid
Under $5
20-Day Simple Moving Average: Price above SMA
50-Day Simple Moving Average: Price above SMA
200-Day Simple Moving Average: Price above SMA
Average True Range Over 0.25
EPS growth qtr over qtr Over 5%
Sales growth qtr over qtr Over 5%
Institutional Ownership Over 10%

bounce plays (falling, looking to buy on the dips)
6. 
Today Down
Under $10
Performance 2 -5%
Avg True Range Over 0.25
Average Volume OVer 200k
Change Down
'''
