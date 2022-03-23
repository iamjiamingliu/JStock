import time

import readchar
import yfinance
import locale
import json
import reprint
from blessed import Terminal

with open("tickers.json", "r") as tickers_json:
    ticker_data = json.load(tickers_json)

locale.setlocale(locale.LC_ALL, '')


# Format money
def fm(value):
    return locale.currency(value, symbol=False, grouping=True)


def rgb(rgb_list):
    r = rgb_list[0]
    g = rgb_list[1]
    b = rgb_list[2]
    return f"\033[38;2;{r};{g};{b}m"


days_to_scale = {
    5: 4,
    10: 2
}

# Unicode blocks
block = "█"
half_block = "▄"

# ANSI Colors/Codes
green = rgb([56, 255, 75])
red = rgb([252, 36, 3])
reset = "\033[0m"


def get_lines(ticker, days):
    si = [f"\nTicker: {ticker.upper()}"]
    days = days if days < 60 else 60
    graph = []
    # Graph
    try:
        stock = yfinance.Ticker(ticker)
        history = stock.history(period=f"{days}d")

        increment_x = 1
        try:
            increment_x = days_to_scale[days]
        except:
            pass

        # All open and close data
        start_date = str(history.index[0]).split()[0]
        end_date = str(history.index[-1]).split()[0]
        stock_closes = []
        for i in range(len(history["Open"])):
            stock_closes.append(history["Open"][i])
            stock_closes.append(history["Close"][i])

        si.append(f"\nPrevious Open: {green}{fm(stock_closes[-2])}{reset} USD")
        si.append(f"Previous Close: {green}{fm(stock_closes[-1])}{reset} USD")
        difference = round((stock_closes[-1] / stock_closes[-2] - 1) * 100, 3)
        si.append(f"Percent Change: {green if difference >= 0 else red}{difference}{reset} %")

        change = stock_closes[-1] - stock_closes[0]
        close_max = max(stock_closes)
        close_min = min(stock_closes)
        close_range = close_max - close_min
        offset = len(str(int(close_max))) + 3
        # Y-axis increments for graph
        increments_y = [str(round(close_min + close_range * (i / 10), 2)).ljust(offset, "0") for i in range(11)]

        # Building the graph
        for i in range(21):
            graph.append([])
            if i % 2 == 0:
                graph[i].append(increments_y[::-1][i // 2])
            else:
                graph[i].append("".ljust(offset))
            graph[i].append(" | ")
        graph.append(["".ljust(offset + 1), "└ ", "─".ljust(2) * (days + 1)])
        graph.append(["".ljust(offset + 3), start_date, str(end_date).rjust(days * 2 - len(start_date))])

        for close in stock_closes:
            for i in range(21):
                if close >= close_min + close_range * (i / 20):
                    graph[20 - i].append(f"{green if change >= 0 else red}{block}{reset}" * increment_x)
                elif close >= close_min + close_range * (i / 20) - close_range / 40:
                    graph[20 - i].append(f"{green if change >= 0 else red}{half_block}{reset}" * increment_x)
                else:
                    graph[20 - i].append(" " * increment_x)
        # for row in graph:
        #     print("".join(row))
        #     time.sleep(0.03)
    except Exception as e:
        print("No graph")

    try:
        stock_info = stock.info
        currency = stock_info["currency"]

        si.insert(1, f"Name: {stock_info.get('shortName', ticker_data[ticker.upper()])}")

        try:
            si.insert(2, f"Sector: {stock_info['sector']}, {stock_info['industry']}")
        except:
            si.insert(2, "Sector: ---")

        try:
            mc = stock_info.get('marketCap', '---')
            si.append(f"\nMarket Cap: {green if mc != '---' else ''}{fm(mc)}{reset} {currency}")
            rmv = stock_info.get('regularMarketVolume', '---')
            si.append(f"Regular Market Volume: {green if rmv != '---' else ''}{fm(rmv)}{reset} ")

            thd = stock_info.get('twoHundredDayAverage', '---')
            si.append(f"\n200 Day Average: {green if thd != '---' else ''}{fm(thd)}{reset} {currency}")
            fd = stock_info.get('fiftyDayAverage', '---')
            si.append(f"50 Day Average: {green if fd != '---' else ''}{fm(fd)}{reset} {currency}")

            tpe = stock_info.get('trailingPE', '---')
            si.append(f"\nTrailing P/E: {green if tpe != '---' else ''}{tpe}{reset}")
            try:
                if stock_info['forwardPE']:
                    si.append(f"Forward P/E: {green}{stock_info['forwardPE']}{reset}")
                else:
                    raise Exception()
            except:
                si.append("Forward P/E: ---")
        except:
            pass

    except:
        si.insert(1, f"Name: {ticker_data[ticker.upper()]}")

    return [''.join(row) for row in graph], si


class StockUI:
    def __init__(self, terminal: Terminal):
        self.terminal = terminal

    def leading_margin(self) -> str:
        return ' ' * (max((self.terminal.width - 72) // 2, 0))

    def show(self, ticker):
        with reprint.output(no_warning=True) as output:
            graph, description = get_lines(ticker, 30)
            output.append('\n')
            output.append('\n')
            if len(graph[-1]) + len(max(description, key=len)) + 8 < self.terminal.width:
                n = 2
                i = n
                while i < len(description):
                    description.insert(i, '\n')
                    i += (n + 1)
                for i in range(max(len(graph), len(description))):
                    l = ' ' * (self.terminal.width // 2 - 2)
                    if i < len(graph):
                        l = ' ' * (self.terminal.width // 2 - len(graph[-1])) + graph[i]
                    if i < len(description):
                        l += ' ' * 8 + description[i].lstrip()
                    output.append(l)
            else:
                for line in graph + ['\n', '\n', '\n'] + description:
                    output.append(self.leading_margin() + line)

            output.append(self.leading_margin() + "PRESS Q TO EXIT")
        while 1:
            key = readchar.readkey()
            if key == 'q':
                return
