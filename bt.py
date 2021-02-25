import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime


class Algo:

	def __init__(self, decision_engine):
		self.decision_engine = decision_engine

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

class Backtester:

	def __init__(self, start_date, end_date, algos, starting_wallet):
		self.start_date = start_date
		self.end_date = end_date
		self.algos = algos
		self.cash = starting_wallet
		self.run = False
		# initialize portfolios for each algo

	def backtest(self):
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
		plt.legend(loc=2, ncol=2) # legend top left
		plt.title("Backtester", loc='left', fontsize=14, fontweight=0, color='black')
		plt.ylabel("Portfolio Value")

		# plot algos
		xs = [datetime.datetime(2005, 2, 1), datetime.datetime(2005, 2, 15), datetime.datetime(2005, 3, 1), datetime.datetime(2005, 3, 22), datetime.datetime(2005, 4, 1)]
		ax.plot(xs, [1,2,3,4,5], marker='', color=palette(1), linewidth=1, alpha=0.9, label='first')
		ax.plot(xs, [1,4,3,3,2], marker='', color=palette(2), linewidth=2, alpha=0.9, label='second')

		# plt.show()

		return


bt = Backtester(1,2,3,4) #nonsense values for the moment
bt.graph()







