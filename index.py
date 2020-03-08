import os
import pandas as pd
import tushare as ts

import WX


class Index:
    INTERVAL = [60, 120, 250, 500, 750, 1000, 1250]

    def __init__(self, code):
        # FUND = pd.read_csv('fund/' + INDEX_FUND[code], index_col='DATE', sep='\t')
        OHLC = pd.read_csv(WX.PATH['INDEX_OHLC'] + code, index_col='DATE', sep='\t')
        PE_PB = pd.read_csv(WX.PATH['INDEX_INDICATOR'] + code, index_col='DATE', sep='\t')
        # MARGIN = pd.read_csv('margin/margin', index_col='DATE', sep='\t')
        for interval in self.INTERVAL:
            PE_PB['PE_TTM-P' + str(interval)] = self.__percentileOf(PE_PB['PE_TTM'], interval)
            PE_PB['PB_LF-P' + str(interval)] = self.__percentileOf(PE_PB['PB_LF'], interval)
            # MARGIN['MARGIN-P' + interval] = self.percentileOf(MARGIN['TOTAL_BALANCE'], interval)
        #         self.Margin = pd.read_csv('margin/margin', index_col='DATE', sep='\t')
        #         Margin['P_BALANCE'] = self.percentileOf(Margin['TOTAL_BALANCE'], 500)
        #         self.Margin = Margin[START_DATE:END_DATE]
        self.code = code
        self.OHLC = OHLC[WX.START_DATE:WX.END_DATE]
        self.PE_PB = PE_PB[WX.START_DATE:WX.END_DATE]
        # self.MARGIN = MARGIN[START_DATE:END_DATE]
        # self.FUND = FUND[START_DATE:END_DATE]

    @staticmethod
    def __percentileOf(series, interval):
        array = list(series)
        length = len(series)
        percentile = [0] * length
        for i in range(length):
            if i + interval <= length:
                data = array[i:i + interval]
                rank = 1
                for num in data:
                    if data[-1] > num:
                        rank += 1
                percentile[i + interval - 1] = rank / interval * 100
        return percentile

    def write_percentile(self):
        # 写入估值分位
        print('写入估值指标百分位：{0} - {1}'.format(self.code, WX.INDEX[self.code]))
        self.OHLC[['CLOSE']].join(self.PE_PB).dropna().to_csv(WX.PATH['INDEX_INDICATOR_PERCENTILE'] + self.code, sep='\t', float_format='%.2f')


# if __name__ == '__main__':
#     for code, name in WX.INDEX.items():
#         index = Index(code)
#         index.write_percentile()


def write_index_ohlc():
    pro = ts.pro_api('54c728c38a187a7a355174a0070c033f3f776fa5c3fd500c6c71225e')
    for code, name in WX.INDEX.items():
        daily = pro.index_daily(ts_code=code, start_date='1990-01-01', end_date='2020-12-31')
        if not os.path.exists(WX.PATH['TS_INDEX_OHLC'] + code):
            print('下载并写入{0} - {1}日线行情数据'.format(code, name))
            daily.to_csv(WX.PATH['TS_INDEX_OHLC'] + code, index=False, sep='\t')
            ohlc = daily[['trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'vol', 'amount']].rename(
                columns={'trade_date': 'DATE', 'open': 'OPEN', 'high': 'HIGH', 'low': 'LOW', 'close': 'CLOSE', 'pre_close': 'PRE_CLOSE', 'vol': 'VOLUME', 'amount': 'AMOUNT'}).sort_values(by=['DATE']).set_index('DATE')
            ohlc.index = ohlc.index.map(lambda x: '-'.join([x[0:4], x[4:6], x[6:8]]))
            ohlc.to_csv(WX.PATH['INDEX_OHLC'] + code, sep='\t', float_format='%.2f')
