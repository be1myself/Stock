import matplotlib
import pandas as pd

matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import wx
import datetime as dt

import WX

# pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

START_DATE = '2010-01-01'
END_DATE = str(dt.date.today())
# INDEX = ['000001.SH - 上证综指', '000016.SH - 上证50', '000300.SH - 沪深300', '000905.SH - 中证500', '000922.CSI - 中证红利',
#          '399975.SZ - 证券公司', '399967.SZ - 中证军工', '399976.SZ - 新能源车']
# FUND = ['100053.OF - 富国上证综指ETF联接', '110003.OF - 易方达上证50指数A', '100038.OF - 富国沪深300指数增强', '161017.OF - 富国中证500指数增强', '100032.OF - 富国中证红利指数增强',
#         '161027.OF - 富国中证全指证券公司指数分级', '161024.OF - 富国中证军工指数分级', '161028.OF - 富国中证新能源汽车指数分级',
#         '161005.OF - 富国天惠成长混合A']
# INDEX_FUND = {'000001.SH': '100053.OF', '000016.SH': '110003.OF', '000300.SH': '100038.OF', '000905.SH': '161017.OF', '000922.CSI': '100032.OF',
#               '399975.SZ': '161027.OF', '399967.SZ': '161024.OF', '399976.SZ': '161028.OF'}
FACTOR = ['PE_TTM', 'PB_LF', 'MARGIN']
INTERVAL = ['60', '120', '250', '500', '750', '1000', '1250']


def calc_date(start_date, days):
    dateformat = '%Y-%m-%d'
    end_date = dt.datetime.strptime(start_date, dateformat) + dt.timedelta(days=days)
    return end_date.strftime(dateformat)


def calc_days(start_date, end_date):
    dateformat = '%Y-%m-%d'
    time = dt.datetime.strptime(end_date, dateformat) - dt.datetime.strptime(start_date, dateformat)
    return time.days


class Index:

    def __init__(self, code):
        FUND = pd.read_csv('fund/' + WX.INDEX_FUND[code], index_col='DATE', sep='\t')
        OHLC = pd.read_csv('index/ohlc/' + code, index_col='DATE', sep='\t')
        VALUE = pd.read_csv('index/value/' + code, index_col='DATE', sep='\t')
        MARGIN = pd.read_csv('margin/margin', index_col='DATE', sep='\t')
        for interval in INTERVAL:
            VALUE['PE_TTM-P' + interval] = self.percentileOf(VALUE['PE_TTM'], interval)
            VALUE['PB_LF-P' + interval] = self.percentileOf(VALUE['PB_LF'], interval)
            MARGIN['MARGIN-P' + interval] = self.percentileOf(MARGIN['TOTAL_BALANCE'], interval)
        #         self.Margin = pd.read_csv('margin/margin', index_col='DATE', sep='\t')
        #         Margin['P_BALANCE'] = self.percentileOf(Margin['TOTAL_BALANCE'], 500)
        #         self.Margin = Margin[START_DATE:END_DATE]
        self.code = code
        self.OHLC = OHLC[START_DATE:END_DATE]
        self.VALUE = VALUE[START_DATE:END_DATE]
        self.MARGIN = MARGIN[START_DATE:END_DATE]
        self.FUND = FUND[START_DATE:END_DATE]

    def percentileOf(self, series, interval):
        array = list(series)
        length = len(series)
        interval = int(interval)
        percentile = [0] * length
        for i in range(length):
            if i + interval <= length:
                data = array[i:i + interval]
                rank = 1
                for num in data:
                    if (data[-1] > num):
                        rank += 1
                percentile[i + interval - 1] = rank / interval

        return percentile

    def test(self):
        invest = index_amount = fund_amount = 0
        fund = self.FUND.join(self.OHLC['CLOSE']).join(self.VALUE).dropna()
        for date, row in fund.iterrows():
            if row['PE_TTM-P750'] <= 0.1:
                invest += 100
                close = row['CLOSE']
                value = row['VALUE']
                index_amount += 100 / close
                fund_amount += 100 / value

        start_date, end_date = fund.index[[0, -1]]
        start_close, end_close = fund.loc[[start_date, end_date], 'CLOSE']
        asset = end_close * index_amount
        rate = asset / invest - 1
        annual_rate = rate * 365 / calc_days(start_date, end_date)
        print('Index: Invest: %.2f' % invest + '\tAsset: %.2f' % asset
              + '\tTotal Rate: {:.2%}'.format(rate) + '\tAnnual Rate: {:.2%}'.format(annual_rate))

        asset = fund.loc[end_date, 'VALUE'] * fund_amount
        rate = asset / invest - 1
        annual_rate = rate * 365 / calc_days(start_date, end_date)
        print('Fund: Invest: %.2f' % invest + '\tAsset: %.2f' % asset
              + '\tTotal Rate: {:.2%}'.format(rate) + '\tAnnual Rate: {:.2%}'.format(annual_rate))

        rate = end_close / start_close - 1
        annual_rate = rate * 365 / calc_days(start_date, end_date)
        print('Index: Start: %.2f' % start_close + '\tEnd: %.2f' % end_close
              + '\tIndex Rate: {:.2%}'.format(rate) + '\tAnnual Rate: {:.2%}'.format(annual_rate))

    def test2(self):
        LV = pd.DataFrame(columns=['START_DATE', 'END_DATE', 'START_CLOSE', 'END_CLOSE', 'START_VALUE', 'END_VALUE']).set_index('START_DATE')
        fund = self.FUND.join(self.OHLC['CLOSE']).join(self.VALUE)
        for start_date, row in fund.iterrows():
            if row['PE_TTM-P750'] <= 0.1 and row['PE_TTM-P750'] != 0:
                end_date = calc_date(start_date, 365)
                start_close = row['CLOSE']
                end = fund[:end_date].iloc[-1]
                end_close = end['CLOSE']
                start_value = row['VALUE']
                end_value = end['VALUE']
                LV.loc[start_date] = [end_date, start_close, end_close, start_value, end_value]
        LV['INDEX_RATE'] = LV['END_CLOSE'] / LV['START_CLOSE'] - 1

        LV['FUND_RATE'] = LV['END_VALUE'] / LV['START_VALUE'] - 1
        #         LV['INDEX_RATE'] = LV['INDEX_RATE'].apply(lambda x : format(x, '.2%'))
        #         LV['FUND_RATE'] = LV['FUND_RATE'].apply(lambda x : format(x, '.2%'))
        print(len(LV[LV['INDEX_RATE'] > 0]), len(LV[LV['INDEX_RATE'] < 0]), '{:.2%}'.format(LV['INDEX_RATE'].median()))
        print(len(LV[LV['FUND_RATE'] > 0]), len(LV[LV['FUND_RATE'] < 0]), '{:.2%}'.format(LV['FUND_RATE'].median()))

    #         print(LV)

    def sell(self):
        fund = self.FUND.join(self.OHLC['CLOSE']).join(self.PE)
        flag = False
        for date, row in fund.iterrows():
            close = row['CLOSE']
            if row['P500'] == 1:
                high = close
                flag = True
            elif flag == True and close < high * 0.8:
                print(date)
                flag = False


class Frame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title='WX', pos=(100, 20), size=(1200, 700))
        panel1 = wx.Panel(self)
        index_label = wx.StaticText(panel1, label='指数')
        self.index_combo = wx.ComboBox(panel1, choices=INDEX, style=wx.CB_READONLY)
        self.index_combo.SetSelection(0)
        self.index_combo.Bind(wx.EVT_COMBOBOX, self.onSelect)

        fund_label = wx.StaticText(panel1, label='基金')
        self.fund_combo = wx.ComboBox(panel1, choices=FUND, style=wx.CB_READONLY)
        self.fund_combo.SetSelection(0)

        factor_label = wx.StaticText(panel1, label='指标')
        self.factor_combo = wx.ComboBox(panel1, choices=FACTOR, style=wx.CB_READONLY)
        self.factor_combo.SetSelection(0)

        interval_label = wx.StaticText(panel1, label='移动区间')
        self.interval_combo = wx.ComboBox(panel1, choices=INTERVAL, style=wx.CB_READONLY)
        self.interval_combo.SetSelection(4)

        calc_button = wx.Button(panel1, label='运行')
        calc_button.Bind(wx.EVT_BUTTON, self.onCalc)
        wind_button = wx.Button(panel1, label='Wind')
        wind_button.Bind(wx.EVT_BUTTON, self.onWind)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(index_label, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(self.index_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(fund_label, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(self.fund_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(factor_label, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(self.factor_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(interval_label, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(self.interval_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(calc_button, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(wind_button, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        panel1.SetSizer(sizer1)

        self.fig, self.ax = plt.subplots(nrows=2, ncols=1)
        self.fig.tight_layout()
        self.twinx0 = self.ax[0].twinx()
        self.twinx1 = self.ax[1].twinx()
        plt.ion()
        panel2 = FigureCanvas(self, wx.ID_ANY, self.fig)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel1, proportion=0, flag=wx.EXPAND | wx.ALL, border=0)
        frame_sizer.Add(panel2, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)
        self.SetSizer(frame_sizer)

    def onSelect(self, event):
        #         print(event.GetEventObject().GetId(),self.index_combo.GetId(),self.fund_combo.GetId())
        if (event.GetEventObject().GetId() == self.index_combo.GetId()):
            current_index = self.index_combo.GetValue()
            index_code = current_index.split('-')[0].strip()
            fund_code = INDEX_FUND[index_code]
            for fund in FUND:
                if fund.startswith(fund_code):
                    current_fund = fund
            self.fund_combo.SetValue(current_fund)

    def onCalc(self, event):
        current_index = self.index_combo.GetValue()
        current_fund = self.fund_combo.GetValue()
        index_code = current_index.split('-')[0].strip()
        factor = self.factor_combo.GetValue()
        interval = self.interval_combo.GetValue()

        index = Index(index_code)
        ohlc = index.OHLC
        fund = index.FUND
        value = index.VALUE
        percentile = value[factor + '-P' + interval]
        buy = value[(percentile <= 0.1) & (percentile > 0)].join(ohlc['CLOSE']).join(fund['VALUE'])

        ohlc_rate = ohlc['CLOSE'] / ohlc.loc[fund.index[0], 'CLOSE'] - 1
        fund_rate = fund['VALUE'] / fund.iloc[0]['VALUE'] - 1
        buy_rate = buy['VALUE'] / fund.iloc[0]['VALUE'] - 1
        self.ax[0].clear()
        self.ax[0].grid(linestyle='dashed')
        self.ax[0].plot(pd.to_datetime(ohlc.index), ohlc_rate, color='blue', linewidth=0.5, label='Index - ' + current_index)
        self.ax[0].plot(pd.to_datetime(fund.index), fund_rate, color='black', linewidth=0.5, label='Fund - ' + current_fund)
        self.ax[0].plot(pd.to_datetime(buy.index), buy_rate, 'or', markersize=1, label='Buy')
        self.ax[0].legend(fontsize=8)
        self.ax[0].yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=2))
        #         self.ax[0].yaxis.set_major_locator(mtick.MultipleLocator(0.1))

        self.ax[1].clear()
        self.ax[1].grid(linestyle='dashed')
        self.ax[1].yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=2))
        self.ax[1].yaxis.set_major_locator(mtick.MultipleLocator(0.1))
        self.ax[1].set_ylim(0, 1)
        self.ax[1].plot(pd.to_datetime(value.index), value[factor + '-P' + interval], color='blue', linewidth=0.5, label=factor + ' - ' + current_index)
        self.ax[1].legend(fontsize=8)
        self.twinx1.clear()
        self.twinx1.plot(pd.to_datetime(value.index), value[factor], color='black', linewidth=0.5)

    def onWind(self, event):
        START_DATE = '2000-01-01'


#         w.start()
#         # 指数行情和估值
#         for index in INDEX:
#             print('指数：' + index)
#             code = index.split('-')[0].strip()
#             error, data = w.wsd(code, 'open,high,low,close,amt,pe_ttm,pb_lf', START_DATE, END_DATE, usedf=True)
#             data[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'AMT']].dropna().to_csv('ohlc/' + code, index_label='DATE', header=['OPEN', 'HIGH', 'LOW', 'CLOSE', 'AMOUNT'], sep='\t', float_format='%.2f')
#             data[['PE_TTM', 'PB_LF']].dropna().to_csv('value/' + code, index_label='DATE', sep='\t', float_format='%.4f')
#         
#         # 基金复权净值
#         for fund in FUND:
#             print('基金：' + fund)
#             code = fund.split('-')[0].strip()
#             error, data = w.wsd(code, 'NAV_adj', START_DATE, END_DATE, usedf=True)
#             data.dropna().to_csv('fund/' + code, index_label='DATE', header=['VALUE'], sep='\t', float_format='%.4f')
#         
#         # 两室融资融券
#         print('融资融券：')
#         error, data = w.wset('markettradingstatistics(value)', 'exchange=shsz;startdate=2010-01-01;enddate=' + END_DATE + ';frequency=day;sort=asc;'
#                +'field=end_date,shsz_total_balance,margin_balance,period_bought_amount,margin_paid_amount,short_balance,sold_amount,short_paid_amount', usedf=True)
#         data['end_date'].apply(lambda x: x.strftime('%Y-%m-%d'))
#         data.dropna().set_index('end_date').astype('float64').to_csv('margin/margin', index_label='DATE', header=['TOTAL_BALANCE', 'MARGIN_BALANCE', 'MARGIN_BOUGHT', 'MARGIN_PAID', 'SHORT_BALANCE', 'SHORT_SOLD', 'SHORT_PAID'], sep='\t', float_format='%.0f')
#         w.stop()
# 
#         # 写入估值分位
#         for index in INDEX:
#             print('写入：' + index)
#             code = index.split('-')[0].strip()
#             index = Index(code)
#             ohlc = index.OHLC
#             value = index.VALUE
#             ohlc[['CLOSE']].join(value).dropna().to_csv('value/percentile/' + code, sep='\t', float_format='%.2f')


matplotlib.rc('xtick', labelsize=8, color='k')
matplotlib.rc('ytick', labelsize=8, color='k')
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Microsoft Yahei']
matplotlib.rcParams['axes.unicode_minus'] = False
app = wx.App()
Frame().Show()
app.MainLoop()
