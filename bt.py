import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import holidays
import yahoo_fin.stock_info as si

class Algo:

	def __init__(self, name, decision_engine):
		self.decision_engine = decision_engine
		self.name = name
	'''
	true default wouldnt invest
	a default algo decision engine that tracks only appl would be to buy as much appl as much.
	it would simply do that on day 1, and every day from then on would not be able to buy any more bc of lack of cash
	therefore portfolio of only appl would continue to grow


	input:
		current portfolio (tickers, shares, purchase price, unallocated cash) (can calculate worth from this)
		date
	decision engine
		output is to buy, sell, do nothing
		here is where the magic happens, use a yahoo finance api, use a finviz api, use a beautifulsoup(openinsider) api
		when to buy, open or close
		calculates new portfolio
	ouput:
		date
		new portfolio
	'''

'''
Portfolio
{
	'amzn' : {
		'shares' : '10',
		'purchase_price' : '128.55'
	}

	'cash' : 2000
}
'''
def get_stock(ticker, date):
	# format:
	# 			open			high				low				close				adj close		vol		tkr
	# [[757.9199829101562, 758.760009765625, 747.7000122070312, 753.6699829101562, 753.6699829101562, 3521100, 'AMZN']]
	res = si.get_data(ticker, start_date = date.strftime("%m-%d-%Y"), end_date = (date + timedelta(days=1)).strftime("%m-%d-%Y")).values.tolist()[0]
	return {'open': res[0], 'close': res[3]}


def noop_engine(input_portfolio, date):
	return input_portfolio


def basic_stock_engine(input_portfolio, date, ticker='aapl'):
	'''
	if more spare cash than purchase price, purchase as much as i can
	subtract from cash wallet
	'''
	# if we don't create a deep copy, we may modify the referenced portfolio belonging to a different algo
	# i.e. each portfolio was initialized pointing to an empty cash wallet. they each actually point to a single
	# dictionary in memory, several keys to the same value. so to reassign one value without making a copy will edit
	# the referenced dictionary that all keys point to
	portfolio = input_portfolio.copy()
	stock = get_stock(ticker, date)
	if portfolio['cash'] > stock['close']:
		units_to_buy = portfolio['cash'] // stock['close']
		# for simplicity, only buy if we have cash for multiple shares
		if units_to_buy > 1:
			portfolio[ticker] = {'shares': units_to_buy, 'purchase_price': stock['close']}
			portfolio['cash'] -= (units_to_buy * stock['close'])
	return portfolio


def calculate_portfolio_value(portfolio):
	# todo
	return


class Backtester:

	def __init__(self, start_date, end_date, algos, starting_wallet):
		self.start_date = datetime.strptime(start_date, '%m-%d-%Y')
		self.end_date = datetime.strptime(end_date, '%m-%d-%Y')
		self.algos = algos
		self.cash = starting_wallet
		self.run = False
		# initialize portfolios for each algo { 'algo1': {'cash': 1000}, 'algo2': {'cash': 1000}}
		default_portfolio = {'cash': starting_wallet}
		self.portfolios = dict.fromkeys([algo.name for algo in self.algos], default_portfolio)
		# todo, initialize a log of the portfolio values end of each day
		# dates is an array, the xs
		# then make several values arrays, one for each algo. probly 
		#self.dates = []
		#self.portfolio_values = dict.fromkeys([algo.name for algo in self.algos], [])
		# need to watch out for editing this one too and overwriting
		

	def backtest(self):

		delta = timedelta(days=1)
		while self.start_date < self.end_date:
			print(self.start_date.strftime("%m-%d-%Y"))

			try:
				# check if valid trading day
				test_data = si.get_data("amzn", start_date = self.start_date.strftime("%m-%d-%Y"), end_date = (self.start_date + delta).strftime("%m-%d-%Y"))

				for algo in self.algos:
					print(algo.name)
					self.portfolios[algo.name] = algo.decision_engine(self.portfolios[algo.name], self.start_date)
					print(self.portfolios)
				'''
				input from portfolio_map -> algo.decision_engine -> output
				write outtput to the portfolios map
				log change in final price
				'''
			except:
				# not a valid trading day
				pass 
				
			self.start_date += delta
		


		'''
		while tradeable day and <= end date
			for algo in algos
				input_from_potfolio_map->algo.decision_engine->output
				write output to porfolios_map
				log change in final price
			inc day
		'''
		self.run = True
		return

	def graph(self):
		# check if we've run backtest() or not. if not, run it first
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
		plt.ylabel("Portfolio Value")

		# plot algos
		xs = [datetime(2005, 2, 1), datetime(2005, 2, 15), datetime(2005, 3, 1), datetime(2005, 3, 22), datetime(2005, 4, 1)]
		ax.plot(xs, [1,2,3,4,5], marker='', color=palette(1), linewidth=1, alpha=0.9, label='first')
		ax.plot(xs, [1,4,3,3,2], marker='', color=palette(2), linewidth=2, alpha=0.9, label='second')
		plt.legend(loc=2, ncol=2) # legend top left
		#plt.show()

		return






start = '1-12-2021'
end = '1-16-2021'
algos = [Algo('nop', noop_engine), Algo('aapl', basic_stock_engine)]
starting_funds = 2000


bt = Backtester(start, end, algos, 2000)
bt.graph()







