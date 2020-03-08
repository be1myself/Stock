import pandas as pd
import numpy as np
import matplotlib

matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import wx
import datetime as dt

import WX

pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

START_DATE = '2010-01-01'
END_DATE = WX.TODAY
DATE = WX.TRADING_DATE

INDEX_CODE = '000300.SH'
# CASH_CODE = '100028.OF'
# EQUITY_LIST = pd.Series({'161005.OF': '富国天惠', '100020.OF': '富国天益', '100038.OF': '富国沪深300', '100032.OF': '富国中证红利'})
# EQUITY_RATIO = pd.Series({'161005.OF': 0.25, '100020.OF': 0.25, '100038.OF': 0.25, '100032.OF': 0.25})
CASH_CODE = '000638.OF'
EQUITY_LIST = pd.Series({'161005.OF': '富国天惠', '100038.OF': '富国沪深300', '002593.OF': '富国美丽中国', '000029.OF': '富国宏观策略'})
EQUITY_RATIO = pd.Series({'161005.OF': 0.30, '100038.OF': 0.30, '002593.OF': 0.20, '000029.OF': 0.20})

CASH = pd.DataFrame(index=DATE)
CASH[CASH_CODE] = pd.read_csv(WX.PATH['FUND_MMF'] + CASH_CODE, index_col='DATE', sep='\t')['EARNING']
EQUITY = pd.DataFrame(index=DATE)
for code in EQUITY_LIST.keys():
    EQUITY[code] = pd.read_csv(WX.PATH['FUND_NAV'] + code, index_col='DATE', sep='\t')['NAV_ADJ']
FUND = CASH.join(EQUITY).dropna()[START_DATE: END_DATE]
START_DATE = FUND.index[0]

YEAR = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019']
MONTH = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
DAY = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']
GOAL_RATE = ['5%', '8%', '10%', '15%', '20%', '25%', '30%', '40%', '50%']
BUY_RATE = ['40%', '45%', '50%', '55%', '60%', '65%', '70%']

INDEX = pd.read_csv(WX.PATH['INDEX_OHLC'] + INDEX_CODE, index_col='DATE', sep='\t')[START_DATE:END_DATE]
PERCENTILE = pd.read_csv(WX.PATH['INDEX_INDICATOR'] + 'percentile/' + INDEX_CODE, index_col='DATE', sep='\t')[START_DATE:END_DATE]


def days(start_date, end_date):
    time = dt.datetime.strptime(end_date, '%Y-%m-%d') - dt.datetime.strptime(start_date, '%Y-%m-%d')
    return time.days + 1


class Goal:

    def __init__(self, start_date, invest, goal_rate, buy_rate):
        FullGoal = pd.DataFrame(index=FUND[start_date:].index)
        phase = 1
        cash = pd.DataFrame(columns=[CASH_CODE])  # 货币资产明细
        equity = pd.DataFrame(columns=EQUITY.columns)  # 权益资产明细
        unit = pd.DataFrame(columns=EQUITY.columns)  # 权益份额明细
        weight = pd.DataFrame(columns=EQUITY.columns)  # 组合占比明细
        rate = pd.DataFrame(columns=['ASSET', 'EQUITY'])  # 组合收益率、权益收益率明细
        remark = pd.DataFrame(columns=['TYPE', 'REMARK'])  # 调仓明细

        start_date = FUND[start_date:].index[0]
        start_cash = invest * (1 - buy_rate)
        start_equity = equity_cost = invest * buy_rate  # 初始买入权益的金额，以及初始权益成本
        cash.loc[start_date] = start_cash
        value = EQUITY.loc[start_date]
        unit.loc[start_date] = start_equity * EQUITY_RATIO / value
        equity.loc[start_date] = value * unit.loc[start_date]
        weight.loc[start_date] = equity.loc[start_date] / len(EQUITY) / invest
        weight.loc[start_date, CASH_CODE] = start_cash / invest
        rate.loc[start_date] = 0
        remark.loc[start_date] = {'TYPE': 'start', 'REMARK': '第1轮投资，初始买入：%.2f' % start_equity + '，剩余现金：%.2f' % start_cash}

        L = M = N = 0
        achieve = False  # 是否止盈标志
        achieve_date = achieve_unit = achieve_asset = None  # 止盈后的剩余份额，以此作为基数，执行后续分批卖出操作 # 止盈时权益市值
        achieve_days = []
        for date, value in FUND[start_date:].iloc[1:].iterrows():
            cash.loc[date] = cash.iloc[-1] * (1 + float(CASH.loc[date]) / 10000)  # 当天计算前的货币资产
            unit.loc[date] = unit.iloc[-1]  # 当天计算前的权益份额
            equity.loc[date] = value * unit.loc[date]  # 计算当天权益资产明细

            equity_asset = equity.loc[date].sum()  # 权益资产
            cash_asset = cash.loc[date].sum()  # 货币资产
            total_asset = equity_asset + cash_asset  # 组合总资产
            #             print(date + '\t%.2f' % equity_asset + '\t%.2f' % cash_asset + '\t%.2f' % total_asset)
            # 计算组合收益率
            asset_rate = total_asset / invest - 1  # 组合收益率（市值成本法）
            # 计算权益收益率
            if equity_asset == 0:  # 如果权益资产为0，即为空仓时，不计算权益收益率
                equity_rate = 0
            else:
                equity_rate = equity_asset / equity_cost - 1  # 权益收益率（市值成本法）
            rate.loc[date] = [asset_rate, equity_rate]

            # 更新组合占比明细
            weight.loc[date] = equity.loc[date] / total_asset
            weight.loc[date, CASH_CODE] = cash_asset / total_asset

            if not achieve:
                if asset_rate < goal_rate:
                    if L < 4 and equity_rate < 0.95 ** (L + 1) - 1:
                        L += 1
                        #                         if L == 1:
                        #                             start_cash = cash_asset
                        buy = start_cash * 0.1 * L  # 计算补仓金额
                        equity_cost += buy  # 权益成本增加
                        cash_asset -= buy  # 货币资产减少
                        cash.loc[date, CASH_CODE] = cash_asset  # 货币资产减少
                        #                         unit.loc[date] += buy / len(FUND_LIST) / value  # 组合份额调整（平均补仓）
                        # 调整为按比例补仓
                        unit.loc[date] += buy * weight.loc[date] * total_asset / equity_asset / value  # 组合份额调整（按比例补仓）
                        equity.loc[date] = value * unit.loc[date]  # 权益资产调整
                        equity_asset = equity.loc[date].sum()
                        # 调仓后更新组合占比明细
                        weight.loc[date] = equity.loc[date] / total_asset
                        weight.loc[date, CASH_CODE] = cash_asset / total_asset
                        #                         print('----------------第' + str(phase) + '轮投资：' + date + '止盈前组合第' + str(L) + '次下跌5%补仓：' + '%.2f' % buy + '元----------------')
                        #                         print(date + '\t{:.4%}'.format(asset_rate) + '\t{:.4%}'.format(equity_rate))
                        #                         print(date + '\t%.2f' % equity_asset + '\t%.2f' % cash_asset + '\t%.2f' % total_asset)
                        remark.loc[date] = {'TYPE': 'buy', 'REMARK': '第' + str(phase) + '轮投资：止盈前第' + str(L) + '次下跌5%，补仓：' + '%.2f' % buy + '(初始现金的' + str(L) + '0%)' + '，持仓成本：%.2f' % equity_cost}
                else:
                    achieve = True
                    achieve_date = date
                    #                     achieve_days = days(start_date, achieve_date)  # 止盈天数
                    achieve_days.append(days(start_date, date))
                    unit.loc[date] /= 2  # 组合份额卖出一半
                    achieve_unit = unit.loc[date]  # 止盈后的份额数，作为分批卖出份额的基数

                    cash_asset += (value * achieve_unit).sum()  # 止盈赎回后，货币资产增加
                    cash.loc[date, CASH_CODE] = cash_asset
                    equity.loc[date] = value * unit.loc[date]  # 止盈赎回后，权益资产重新计算
                    # 重置止盈后权益成本和权益收益率，用于后续计算止盈后分批卖出的条件
                    equity_asset = equity_cost = achieve_asset = equity.loc[date].sum()
                    equity_rate = 0  # 权益收益率调整
                    # 调仓后更新组合占比明细
                    weight.loc[date] = equity.loc[date] / total_asset
                    weight.loc[date, CASH_CODE] = cash_asset / total_asset

                    #                     print('----------------第' + str(phase) + '轮投资：' + date + '组合触发止盈赎回----------------')
                    #                     print(date + '\t{:.4%}'.format(asset_rate) + '\t{:.4%}'.format(equity_rate))
                    #                     print(date + '\t%.2f' % equity_asset + '\t%.2f' % cash_asset + '\t%.2f' % total_asset)
                    remark.loc[date] = {'TYPE': 'achieve', 'REMARK': '触发止盈，卖出一半组合份额'}
            else:
                if weight.loc[date, CASH_CODE] >= 0.6 and ((equity_asset != 0 and equity_rate < 0.9 - 1) or PERCENTILE.loc[date, 'PE_TTM-P250'] < 10):  # 开启下一轮
                    end_days = days(achieve_date, date)
                    buy = (cash_asset - equity_asset) / 2  # 计算买入金额，填平至货币-权益各50%仓位
                    cash_asset -= buy  # 货币资产减少
                    cash.loc[date, CASH_CODE] = cash_asset  # 货币资产减少

                    unit.loc[date] = (equity_asset + buy) * EQUITY_RATIO / value
                    equity.loc[date] = value * unit.loc[date]  # 权益资产调整
                    equity_asset += buy
                    # 调仓后更新组合占比明细
                    weight.loc[date] = equity.loc[date] / total_asset
                    weight.loc[date, CASH_CODE] = cash_asset / total_asset

                    #                     print('%.2f' % total_asset + '\t%.2f' % equity_asset + '\t%.2f' % cash_asset + '\t%.2f' % equity_cost)
                    #                     print(date + '\t{:.4%}'.format(asset_rate) + '\t{:.4%}'.format(equity_rate))
                    #                     print(date + '\t%.2f' % equity_asset + '\t%.2f' % cash_asset + '\t%.2f' % total_asset)

                    remark.loc[date] = {'TYPE': 'start', 'REMARK': '开启第' + str(phase + 1) + '轮投资，初始买入： ' + '%.2f' % buy + '，剩余现金：%.2f' % (cash_asset)}
                    if PERCENTILE.loc[date, 'PE_TTM-P250'] < 10:
                        #                         print('----------------第' + str(phase) + '轮投资：' + date + '沪深300指数估值分位低于10%，开启第' + str(phase + 1) + '轮投资----------------')
                        remark.loc[date, 'REMARK'] += '，原因：沪深300指数估值分位低于10%'
                    else:
                        #                         print('----------------第' + str(phase) + '轮投资：' + date + '止盈后的权益收益率低于90%，开启第' + str(phase + 1) + '轮投资----------------')
                        remark.loc[date, 'REMARK'] += '，原因：止盈后的权益收益率低于90%'

                    # 开启下一轮后的参数初始化
                    phase += 1
                    start_date = date
                    achieve = False
                    achieve_date = achieve_asset = achieve_unit = None
                    invest = total_asset
                    start_cash = invest * (1 - buy_rate)
                    start_buy = invest * buy_rate
                    equity_cost = start_buy
                    L = M = N = 0
                    asset_rate = equity_rate = 0
                    continue

                # 已经空仓，则不作后续判断
                if M + N == 4:
                    equity_rate = 0
                    continue
                if N < 4 and equity_rate > 1.1 ** (N + 1) - 1:  # 每涨10%，分批卖出
                    N += 1
                    sell_unit = achieve_unit * N * 0.1  # 计算待卖出的份额
                    if sell_unit.sum() >= unit.loc[date].sum():  # 如待卖出的份额大于持有份额，则全部卖出持有份额
                        sell_unit = unit.loc[date]
                    sell = (value * sell_unit).sum()  # 计算卖出金额
                    equity_asset -= sell
                    cash_asset += sell
                    cash.loc[date, CASH_CODE] = cash_asset  # 货币资产增加

                    unit.loc[date] -= sell_unit  # 组合份额减少
                    equity.loc[date] = value * unit.loc[date]  # 权益资产减少
                    equity_cost -= achieve_asset * N * 0.1  # 止盈后的总权益成本在分批卖出后同比例变化

                    # 调仓后更新组合占比明细
                    weight.loc[date] = equity.loc[date] / total_asset
                    weight.loc[date, CASH_CODE] = cash_asset / total_asset

                    #                     print('----------------第' + str(phase) + '轮投资：' + date + '止盈后组合第' + str(N) + '次上涨10%分批卖出----------------')
                    #                     print(date + '\t{:.4%}'.format(asset_rate) + '\t{:.4%}'.format(equity_rate))
                    #                     print(date + '\t%.2f' % equity_asset + '\t%.2f' % cash_asset + '\t%.2f' % total_asset)
                    remark.loc[date] = {'TYPE': 'sell', 'REMARK': '第' + str(N) + '次上涨10%，卖出止盈后' + str(N) + '0%份额'}

                elif M == 0 and equity_rate < 0.95 - 1:  # 下跌5%，卖出一半份额
                    M += 1
                    sell_unit = achieve_unit * 0.5  # 计算待卖出的份额
                    if sell_unit.sum() >= unit.loc[date].sum():  # 如待卖出的份额大于持有份额，则全部卖出持有份额
                        sell_unit = unit.loc[date]
                    sell = (value * sell_unit).sum()  # 计算卖出金额
                    equity_asset -= sell
                    cash_asset += sell
                    cash.loc[date, CASH_CODE] = cash_asset  # 货币资产增加

                    unit.loc[date] -= sell_unit  # 组合份额减少
                    equity.loc[date] = value * unit.loc[date]  # 权益资产减少
                    equity_cost -= achieve_asset * 0.5  # 止盈后的总权益成本在分批卖出后同比例变化
                    remark.loc[date] = {'TYPE': 'sell', 'REMARK': '第' + str(M) + '次下跌5%，卖出止盈后50%份额'}

                    # 调仓后更新组合占比明细
                    weight.loc[date] = equity.loc[date] / total_asset
                    weight.loc[date, CASH_CODE] = cash_asset / total_asset

        #                     print('----------------第' + str(phase) + '轮投资：' + date + '止盈后组合下跌5%，卖出止盈后50%份额----------------')
        #                     print(date + '\t{:.4%}'.format(asset_rate) + '\t{:.4%}'.format(equity_rate))
        #                     print(date + '\t%.2f' % equity_asset + '\t%.2f' % cash_asset + '\t%.2f' % total_asset)

        FullGoal = FullGoal.join(cash).join(equity)
        FullGoal['CASH'] = FullGoal[CASH_CODE]
        FullGoal['EQUITY'] = FullGoal[EQUITY.columns].apply(lambda x: x.sum(), axis=1)
        FullGoal['ASSET'] = FullGoal['CASH'] + FullGoal['EQUITY']
        FullGoal = FullGoal.join(remark)
        FullGoal.to_csv('goal/FullGoal_' + start_date + '_' + '%.2f' % goal_rate, sep='\t')
        self.FullGoal = FullGoal
        self.achieve_days = achieve_days

        #         print(np.maximum.accumulate(FullGoal['ASSET']))
        max_asset = FullGoal['ASSET'].cummax()
        # print(((max_asset - FullGoal['ASSET']) / max_asset))
        bottom_date = ((max_asset - FullGoal['ASSET']) / max_asset).idxmax()
        top_date = FullGoal['ASSET'][:bottom_date].idxmax()
        #         print(top_date + '\t' + bottom_date + '\t{:.4%}'.format((FullGoal.loc[top_date, 'ASSET'] - FullGoal.loc[bottom_date, 'ASSET']) / FullGoal.loc[top_date, 'ASSET']))
        self.MaxDrawdown = pd.Series({'TOP_DATE': top_date, 'BOTTOM_DATE': bottom_date})


class Frame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title='目标盈组合', pos=(100, 50), size=(1200, 800))
        panel1 = wx.Panel(self)
        fund_label = wx.StaticText(panel1, label='目标盈组合')
        choices = []
        for code, name in EQUITY_LIST.items():
            choices.append(code + ' - ' + name + ' - ' + '{:.2%}'.format(EQUITY_RATIO[code]))
        self.fund_combo = wx.ComboBox(panel1, choices=choices, style=wx.CB_READONLY)
        self.fund_combo.SetSelection(0)

        date_label = wx.StaticText(panel1, label='起投日期')
        self.year_combo = wx.ComboBox(panel1, choices=YEAR, style=wx.CB_READONLY)
        self.year_combo.SetSelection(8)
        year_label = wx.StaticText(panel1, label='年')
        self.month_combo = wx.ComboBox(panel1, choices=MONTH, style=wx.CB_READONLY)
        self.month_combo.SetSelection(0)
        month_label = wx.StaticText(panel1, label='月')
        self.day_combo = wx.ComboBox(panel1, choices=DAY, style=wx.CB_READONLY)
        self.day_combo.SetSelection(0)
        day_label = wx.StaticText(panel1, label='日')

        goal_label = wx.StaticText(panel1, label='目标收益率')
        self.goal_combo = wx.ComboBox(panel1, choices=GOAL_RATE, style=wx.CB_READONLY)
        self.goal_combo.SetSelection(3)
        first_buy_label = wx.StaticText(panel1, label='初始投入比例')
        self.first_buy_combo = wx.ComboBox(panel1, choices=BUY_RATE, style=wx.CB_READONLY)
        self.first_buy_combo.SetSelection(2)

        fullgoal_button = wx.Button(panel1, label='FullGoal')
        fullgoal_button.Bind(wx.EVT_BUTTON, self.onFullGoal)
        self.fig, self.ax = plt.subplots(nrows=2, ncols=1)
        self.fig.tight_layout()
        panel2 = FigureCanvas(self, wx.ID_ANY, self.fig)
        plt.ion()

        panel3 = wx.Panel(self)
        result_label = wx.StaticText(panel3, label='测算结果')
        self.result_text = wx.TextCtrl(panel3, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(fund_label, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(self.fund_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)

        sizer1.Add(date_label, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(self.year_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(year_label, proportion=0, flag=wx.ALL | wx.CENTER, border=0)
        sizer1.Add(self.month_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(month_label, proportion=0, flag=wx.ALL | wx.CENTER, border=0)
        sizer1.Add(self.day_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(day_label, proportion=0, flag=wx.ALL | wx.CENTER, border=0)
        sizer1.Add(goal_label, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(self.goal_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(first_buy_label, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(self.first_buy_combo, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        sizer1.Add(fullgoal_button, proportion=0, flag=wx.ALL | wx.CENTER, border=5)
        panel1.SetSizer(sizer1)

        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer3.Add(result_label, proportion=0, flag=wx.ALL | wx.LEFT, border=5)
        sizer3.Add(self.result_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)
        panel3.SetSizer(sizer3)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel1, proportion=0, flag=wx.EXPAND | wx.ALL, border=0)
        frame_sizer.Add(panel2, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)
        frame_sizer.Add(panel3, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)
        self.SetSizer(frame_sizer)

    def onFullGoal(self, event):
        year = self.year_combo.GetValue()
        month = self.month_combo.GetValue()
        day = self.day_combo.GetValue()
        start_date = year + '-' + month + '-' + day
        invest = 100000
        goal_rate = float(self.goal_combo.GetValue().strip('%')) / 100
        buy_rate = float(self.first_buy_combo.GetValue().strip('%')) / 100
        goal = Goal(start_date, invest, goal_rate, buy_rate)

        # 组合收益率和止盈情况
        FullGoal = goal.FullGoal
        achieve_days = goal.achieve_days
        start_date, end_date = FullGoal.index[[0, -1]]
        start_asset, end_asset = FullGoal['ASSET'].iloc[[0, -1]]
        asset_rate = end_asset / start_asset - 1
        annual_rate = asset_rate * 365 / days(start_date, end_date)
        equity_mean = FullGoal['EQUITY'].mean()
        cash_mean = FullGoal['CASH'].mean()

        # 指数收益率
        index = INDEX[start_date:]
        start_index, end_index = index['CLOSE'].iloc[[0, -1]]
        index_rate = end_index / start_index - 1
        index_annual_rate = index_rate * 365 / days(start_date, end_date)

        # 最大回撤
        top_date, bottom_date = goal.MaxDrawdown[['TOP_DATE', 'BOTTOM_DATE']]
        asset_drawdown = (FullGoal.loc[top_date, 'ASSET'] - FullGoal.loc[bottom_date, 'ASSET']) / FullGoal.loc[top_date, 'ASSET']
        index_drawdown = (index.loc[top_date, 'CLOSE'] - index.loc[bottom_date, 'CLOSE']) / index.loc[top_date, 'CLOSE']
        self.result_text.AppendText('输入参数：1、起投日期：' + start_date + '，2、目标收益率：{:.2%}'.format(goal_rate) + '，3、初始投入比例：{:.2%}'.format(buy_rate)
                                    + '\n输出结果\n一、起止日期：' + start_date + ' ~ ' + end_date
                                    + '\n二、组合止盈：' + str(len(achieve_days)) + '次，平均止盈天数：%d' % (np.average(achieve_days) if len(achieve_days) != 0 else 0) + '天'
                                    + '\n三、组合资产：%.2f' % start_asset + ' ~ %.2f' % end_asset
                                    + '，组合收益率：{:.2%}'.format(asset_rate) + '，年化收益率：{:.2%}'.format(annual_rate) + '，最大回撤：{:.2%}'.format(asset_drawdown)
                                    + '\n四、同期沪深300指数：%.2f' % start_index + ' ~ %.2f' % end_index
                                    + '，指数收益率：{:.2%}'.format(index_rate) + '，年化收益率：{:.2%}'.format(index_annual_rate) + '，最大回撤：{:.2%}'.format(index_drawdown) + '\n'
                                    )
        #                                     +'\t%.2f' % equity_mean + '\t{:.2%}'.format(equity_mean / (equity_mean + cash_mean))
        #                                      +'\t%.2f' % cash_mean + '\t{:.2%}'.format(cash_mean / (equity_mean + cash_mean)) + '\n')

        buy = FullGoal[FullGoal['TYPE'] == 'buy']
        sell = FullGoal[FullGoal['TYPE'] == 'sell']
        achieve = FullGoal[FullGoal['TYPE'] == 'achieve']
        start = FullGoal[FullGoal['TYPE'] == 'start']

        self.ax[0].clear()
        self.ax[0].grid(linestyle='dashed')
        self.ax[0].yaxis.set_major_formatter(mtick.PercentFormatter(1.00))
        self.ax[0].plot(pd.to_datetime(FullGoal.index), FullGoal['ASSET'] / start_asset - 1, color='blue', linewidth=0.8, label='目标盈组合')
        self.ax[0].plot(pd.to_datetime(index.index), index['CLOSE'] / start_index - 1, color='black', linewidth=0.8, label='沪深300指数')
        self.ax[0].plot(pd.to_datetime(buy.index), buy['ASSET'] / start_asset - 1, 'or', markersize=4, label='买入位')
        self.ax[0].plot(pd.to_datetime(sell.index), sell['ASSET'] / start_asset - 1, 'og', markersize=4, label='卖出位')
        self.ax[0].plot(pd.to_datetime(achieve.index), achieve['ASSET'] / start_asset - 1, 'og', markersize=8, label='止盈位')
        self.ax[0].plot(pd.to_datetime(start.index), start['ASSET'] / start_asset - 1, 'or', markersize=8, label='开启位')
        self.ax[0].plot(pd.to_datetime(FullGoal[top_date:bottom_date].index), FullGoal[top_date:bottom_date]['ASSET'] / start_asset - 1, color='m', linewidth=1.2, label='最大回撤')
        self.ax[0].legend(fontsize=8)
        self.ax[0].text(pd.to_datetime(bottom_date), FullGoal.loc[bottom_date, 'ASSET'] / start_asset - 1, '组合最大回撤：{:.2%}'.format(asset_drawdown) + '\n同期沪深300：{:.2%}'.format(index_drawdown),
                        ha='center', va='top',
                        fontsize=8)

        self.ax[1].clear()
        self.ax[1].grid(linestyle='dashed')
        #         self.ax[1].yaxis.set_major_locator(mtick.MultipleLocator(10000))
        #         self.ax[1].yaxis.set_major_formatter(mtick.PercentFormatter(1.00))
        self.ax[1].plot(pd.to_datetime(FullGoal.index), FullGoal['CASH'], color='green', linewidth=0.8, label='货币资产')
        self.ax[1].plot(pd.to_datetime(FullGoal.index), FullGoal['EQUITY'], color='red', linewidth=0.8, label='权益资产')
        self.ax[1].legend(fontsize=8)


# end_date = '2019-12-31'
# for goal_rate in np.arange(0.05, 0.51, 0.01):
#     for year in range(2016, 2019):
#         for month in range(1, 13):
#             start_date = str(year) + '-%02d' % month + '-01'
#             print(start_date + '_%.2f' % goal_rate)
#             goal = Goal(start_date, 100000, goal_rate , 0.5)
#                
#             FullGoal = goal.FullGoal
#             achieve_days = goal.achieve_days
#             start_asset, end_asset = FullGoal['ASSET'].iloc[[0, -1]]
#             asset_rate = end_asset / start_asset - 1
#             annual_rate = asset_rate * 365 / days(start_date, end_date)
#                
#             index = INDEX[start_date:]
#             start_index, end_index = index['CLOSE'].iloc[[0, -1]]
#             index_rate = end_index / start_index - 1
#             index_annual_rate = index_rate * 365 / days(start_date, end_date)
#                
#             fg = {'beginDate':start_date , 'endDate':end_date, 'totMonths':'42',  # 起止日期和总期数
#                    'beginCost':'%.2f' % start_asset , 'endCost':'%.2f' % end_asset,  # 期初和期末市值
#                   'profitPhase':'%d' % len(achieve_days), 'profitDays':'%d' % (np.average(achieve_days) if len(achieve_days) != 0 else 99999),  # 本期止盈次数和止盈平均天数
#                   'totCostInc': '%.4f' % (asset_rate * 100), 'yieldInc': '%.4f' % (annual_rate * 100),  # 组合收益率、组合年化收益率
#                   'aveCsiRatio':'%.4f' % (index_rate * 100), 'aveCsiYieldRatio':'%.4f' % (index_annual_rate * 100),  # 同期沪深300指数收益率、年化收益率
#                   'aveProfitDate':'', 'totInc':'', 'aveCsiYieldRatio2':''  # 42期平均止盈时长，平均组合年化哦疑虑，平均指数年化收益率
#                   }
#             combineAssetRec = []
#             for date, row in goal.FullGoal.iterrows():
#                 asset = {'date':date, 'asset':'%.2f' % row['ASSET'], 'index':index.loc[date, 'CLOSE'],
#                          'buyFlag':'0', 'saleFlag':'0', 'profitFlag':'0'}
#                 if row['TYPE'] == 'start' or row['TYPE'] == 'buy':
#                     asset['buyFlag'] = '1' 
#                 elif row['TYPE'] == 'achieve':
#                     asset['profitFlag'] = '1'
#                 elif row['TYPE'] == 'sell':
#                     asset['saleFlag'] = '1'
#                 combineAssetRec.append(asset)
#             fg['combineAssetRec'] = combineAssetRec
#             json.dump(fg, open('redis/' + start_date + '_%.2f' % goal_rate, 'w'))

matplotlib.rc('xtick', labelsize=8, color='k')
matplotlib.rc('ytick', labelsize=8, color='k')
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Microsoft Yahei']
matplotlib.rcParams['axes.unicode_minus'] = False
app = wx.App()
Frame().Show()
app.MainLoop()
