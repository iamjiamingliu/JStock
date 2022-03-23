from search import SearchUI
from stock_view import StockUI
from blessed import Terminal

term = Terminal()

search_ui = SearchUI(term)
stock_ui = StockUI(term)

while 1:
    ticker = search_ui.get_ticker()
    if ticker:
        stock_ui.show(ticker)
    search_ui.clear()
