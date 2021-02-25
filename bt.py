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
		# initialize portfolios for each algo

	def backtest():
		'''
		while tradeable day and <= end date
			for algo in algos
				input_from_potfolio_map->algo.decision_engine->output
				write output to porfolios_map
				log change in final price
			inc day
		'''

	def graph():
		# check if we've run backtest() or not. if not, run it first
		# use a graphing library. let's pick one first, then decide how we should store the logs (each strategies ending prices each day)