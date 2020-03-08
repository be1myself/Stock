import pandas as pd
import numpy as np
import talib as ta
import matplotlib

matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.pyplot as plt
import wx
import datetime as dt
import stock

import WX

pd.set_option('display.max_rows', 10000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000)

START_DATE = '2019-01-01'
END_DATE = '2020-02-28'
CODE = '399006.SZ'
OHLC = pd.read_csv(WX.PATH['INDEX_OHLC'] + CODE, index_col='DATE', sep='\t')
INVEST = 100000
HIGH = ta.MAX(OHLC['HIGH'], timeperiod=55)[START_DATE:END_DATE]
LOW = ta.MIN(OHLC['LOW'], timeperiod=20)[START_DATE:END_DATE]
PRE_HIGH = HIGH.shift()
PRE_LOW = LOW.shift()
ATR = ta.ATR(OHLC['HIGH'], OHLC['LOW'], OHLC['CLOSE'])[START_DATE:END_DATE]
POSITION = pd.DataFrame(columns=['DATE', 'TYPE', 'PRICE', 'SIZE', 'VALUE']).set_index('DATE')

for date in HIGH[HIGH.diff() > 0].index:
    if not POSITION.empty:
        if date <= POSITION.index[-1] or (POSITION.iloc[-1]['TYPE'] != 'EXIT' and POSITION.iloc[-1]['TYPE'] != 'STOP'):
            # print(date, POSITION.index[-1])
            continue
    entry = PRE_HIGH[date] if PRE_HIGH[date] >= OHLC.loc[date, 'OPEN'] else OHLC.loc[date, 'OPEN']
    M = 1
    N = round(ATR[date], 2)
    size = INVEST / (N * entry)
    POSITION.loc[date] = ['ENTRY', entry, size, entry * size]
    for date, row in OHLC[OHLC.index > date].iterrows():
        high, low = row[['HIGH', 'LOW']]
        price = POSITION.iloc[-1]['PRICE']
        add = price + 0.5 * N
        stop = price - 2 * N
        exit = PRE_LOW[date]
        if M < 4 and high >= add:
            # print(date, high, add)
            if OHLC.loc[date, 'OPEN'] > add:
                add = OHLC.loc[date, 'OPEN']
            POSITION.loc[date] = ['ADD', add, size, add * size]
            M += 1
            continue
        if low <= stop:
            if OHLC.loc[date, 'OPEN'] < stop:
                stop = OHLC.loc[date, 'OPEN']
            size = POSITION['SIZE'].sum() * -1
            POSITION.loc[date] = ['STOP', stop, size, stop * size]
            break
        if low <= exit:
            if OHLC.loc[date, 'OPEN'] < exit:
                exit = OHLC.loc[date, 'OPEN']
            size = POSITION['SIZE'].sum() * -1
            POSITION.loc[date] = ['EXIT', exit, size, exit * size]
            break

# POSITION.loc[OHLC.index[-1]] = {'TYPE':'END', 'PRICE': OHLC.iloc[-1]['CLOSE'], }
print(POSITION)
print(POSITION['VALUE'].sum())


# print(TURTLE['HIGH'])
# ohlc.insert(0, 'DATE', dts.date2num(pd.to_datetime(ohlc.index)))
# ohlc = ohlc[['DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE']]
# quotes = []
# [quotes.append(tuple) for tuple in ohlc.itertuples(index=False)]
class Frame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title='Turtle', pos=(100, 50), size=(1200, 600))

        fig, ax = plt.subplots(nrows=1, ncols=1)
        fig.tight_layout()
        panel = FigureCanvas(self, wx.ID_ANY, fig)
        plt.ion()
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)
        self.SetSizer(frame_sizer)

        ax.plot(pd.to_datetime(OHLC.index), OHLC['CLOSE'], color='blue', linewidth=1, label=CODE)
        ax.plot(pd.to_datetime(HIGH.index), HIGH, color='red', linewidth=1, label=CODE)
        ax.plot(pd.to_datetime(LOW.index), LOW, color='green', linewidth=1, label=CODE)
        entry = POSITION[POSITION['TYPE'] == 'ENTRY']
        add = POSITION[POSITION['TYPE'] == 'ADD']
        ax.plot(pd.to_datetime(entry.index), entry['PRICE'], 'or', markersize=8, label='ENTRY')
        ax.plot(pd.to_datetime(add.index), add['PRICE'], 'or', markersize=4, label='ADD')
        ax.grid(True, 'major', 'both', ls='--', lw=0.5, c='k', alpha=0.5)

# matplotlib.rc('xtick', labelsize=8, color='k')
# matplotlib.rc('ytick', labelsize=8, color='k')
# matplotlib.rcParams['font.family'] = 'serif'
# matplotlib.rcParams['font.serif'] = ['Microsoft Yahei']
# matplotlib.rcParams['axes.unicode_minus'] = False
# app = wx.App()
# Frame().Show()
# app.MainLoop()
