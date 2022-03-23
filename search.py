import art
import signal
from blessed import Terminal, keyboard
import reprint
import json
from typing import *
import readchar


class SearchUI:
    def __init__(self, terminal: Terminal):
        self.terminal = terminal
        self.cur_query = ""
        self.search_histories = []  # the ones at the front are the newest
        with open("tickers.json", "r") as tickers_json:
            self.ticker_data = json.load(tickers_json)
        self.autocompletes = []
        self.selected_idx = None

    def get_autocompletes(self):
        cur_selected = '' if self.selected_idx is None else self.autocompletes[self.selected_idx]
        results = []
        for key in self.ticker_data:
            if len(results) <= 25:
                if self.cur_query.lower() in key.lower() or self.cur_query.lower() in self.ticker_data[key].lower():
                    results.append(key)
            else:
                break
        self.autocompletes = results[:5]
        if cur_selected in self.autocompletes:
            self.selected_idx = self.autocompletes.index(cur_selected)

    def print_logo(self):
        # 7 is the height of logo + 1 empty row + search bar
        print('\n' * max((self.terminal.height - 7) // 3, 0))
        logo = art.text2art('JStock', font='cybermedum').split('\n')
        max_width = len(max(logo, key=len))
        for l in logo:
            print(self.leading_margin() + ' ' * ((72 - max_width) // 2) + l)

    def leading_margin(self) -> str:
        return ' ' * (max((self.terminal.width - 72) // 2, 0))

    def get_ticker(self) -> str:
        self.print_logo()
        with self.terminal.cbreak() as break_manager, \
                reprint.output(initial_len=max((self.terminal.height - 7) // 3 * 2, 9), no_warning=True) as output:
            # width 72
            output[0] = self.leading_margin() + '╭' + '—' * 70 + '╮'
            output[1] = self.leading_margin() + '│' + '%-69s' % '🔎 ' + '│'
            output[2] = self.leading_margin() + '╰' + '—' * 70 + '╯'
            for i in range(3, max((self.terminal.height - 7) // 3 * 2, 9)):
                output[i] = '\n'

            while 1:
                key = readchar.readkey()
                if key == "\r":  # Enter
                    return self.commit()
                elif key == "\x7f":  # Backspace
                    self.selected_idx = None
                    self.cur_query = self.cur_query[:-1]
                    output[1] = self.leading_margin() + '│' + '%-69s' % ('🔎 ' + self.cur_query) + '│'
                elif key == '\x1b[A':  # arrow up
                    if self.selected_idx is None:
                        self.selected_idx = 0
                    else:
                        self.selected_idx = (len(self.autocompletes) + self.selected_idx - 1) % len(self.autocompletes)
                elif key == '\x1b[B':  # arrow down
                    if self.selected_idx is None:
                        self.selected_idx = 0
                    else:
                        self.selected_idx = (len(self.autocompletes) + self.selected_idx + 1) % len(self.autocompletes)

                # elif val:
                if key.lower().isalpha() or key == ' ':
                    self.cur_query += key
                    output[1] = self.leading_margin() + '│' + '%-69s' % ('🔎 ' + self.cur_query) + '│'

                if self.cur_query:
                    self.get_autocompletes()
                else:
                    self.autocompletes = []
                    self.selected_idx = None
                if self.autocompletes:
                    output[2] = self.leading_margin() + '│' + ' ' * 70 + '│'
                    for i, a in enumerate(self.autocompletes):
                        line = f'{" " if i != self.selected_idx else "•"}   {a} - {self.ticker_data[a]} '[:70]
                        output[i + 3] = self.leading_margin() + '│' + '%-70s' % line + '│'
                    output[3 + len(self.autocompletes)] = self.leading_margin() + '╰' + '—' * 70 + '╯'
                else:
                    output[2] = self.leading_margin() + '╰' + '—' * 70 + '╯'
                for i in range(2, len(output)):
                    if output[i] == self.leading_margin() + '╰' + '—' * 70 + '╯':
                        for j in range(i + 1, len(output)):
                            output[j] = '\n'
                        break

    def commit(self) -> str:
        if self.selected_idx is not None:
            q = self.autocompletes[self.selected_idx]
        elif len(self.autocompletes) == 1:
            q = self.autocompletes[0]
        else:
            return ''  # nothing found
        for i, h in enumerate(self.search_histories):
            if h.lower() == q.lower():
                self.search_histories.pop(i)
                self.search_histories.insert(0, q)
                break
        if not self.search_histories or self.search_histories[0] != q:
            self.search_histories.insert(0, q)
        self.cur_query = ''
        self.selected_idx = None
        return q

    @staticmethod
    def clear():
        print("\033c", end="")


if __name__ == '__main__':

    term = Terminal()

    ui = SearchUI(term)


    def on_resize(sig, action):
        print(f'height={term.height}, width={term.width}')


    signal.signal(signal.SIGWINCH, on_resize)

    while 1:
        print(ui.get_ticker())
