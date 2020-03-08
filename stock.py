import WX
import os
import pandas as pd
import tushare as ts
import talib as ta

pro = ts.pro_api('db6994b8f74e1b1301dfb3e2a82a52c966a5c14dd4a637432c0a3b70')
pd.set_option('display.max_rows', 50000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def read_stock_ohlc(code):
    if os.path.exists(WX.PATH['STOCK_OHLC'] + code):
        return pd.read_csv(WX.PATH['STOCK_OHLC'] + code, index_col='DATE', sep='\t')
    else:
        return pd.DataFrame()


def read_stock_factor(code):
    if os.path.exists(WX.PATH['STOCK_FACTOR'] + code):
        return pd.read_csv(WX.PATH['STOCK_FACTOR'] + code, index_col='DATE', sep='\t')
    else:
        return pd.DataFrame()


def write_trading_date(start_date='1990-01-01', end_date=WX.TODAY):
    # 获取交易日期
    print('下载交易日期：{0} - {1}'.format(start_date, end_date))
    start_date, end_date = [date.replace('-', '') for date in [start_date, end_date]]
    date = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date).rename(columns={'cal_date': 'DATE'})
    date = date.loc[date['is_open'] == 1]['DATE'].map(lambda x: '{0}-{1}-{2}'.format(x[0:4], x[4:6], x[6:8]))
    date.to_csv('date/TRADING_DATE', index=False, sep='\t')


def write_stock_factor(dates, codes):
    # 下载并写入按日期的股票复权因子数据
    for date in dates:
        if not os.path.exists(WX.PATH['TS_DATE_FACTOR'] + date):
            print('下载并写入{0}复权因子数据'.format(date))
            daily = pro.adj_factor(trade_date=date.replace('-', '')).sort_values(by=['ts_code'])
            daily.to_csv(WX.PATH['TS_DATE_FACTOR'] + date, index=False, sep='\t')
            factor = daily[['ts_code', 'adj_factor']].rename(columns={'ts_code': 'CODE', 'adj_factor': 'FACTOR'}).set_index('CODE')
            factor.to_csv(WX.PATH['DATE_FACTOR'] + date, sep='\t', float_format='%.3f')

    # 转换成按股票的复权因子数据
    FACTOR = pd.DataFrame(columns=['CODE', 'DATE', 'FACTOR']).set_index('CODE')
    for date in dates:
        print('读取{0}数据：{1}'.format(date, WX.PATH['DATE_FACTOR'] + date))
        factor = pd.read_csv(WX.PATH['DATE_FACTOR'] + date, index_col='CODE', sep='\t')
        factor['DATE'] = date
        FACTOR = FACTOR.append(factor)
    for code in codes:
        if code in FACTOR.index:
            print('写入股票复权因子数据：{0} - {1}'.format(code, WX.STOCK_LIST.loc[code, 'NAME']))
            header = True if not os.path.exists(WX.PATH['STOCK_FACTOR'] + code) else False
            FACTOR[FACTOR.index == code].to_csv(WX.PATH['STOCK_FACTOR'] + code, mode='a', header=header, index=False, sep='\t', float_format='%.3f')


def write_stock_ohlc(dates, codes):
    # 获取股票基础数据，上市状态：L上市 D退市 P暂停上市
    print('下载股票基础数据')
    fields = 'ts_code,name,area,industry,fullname,market,list_date,list_status'
    pro.stock_basic(list_status='L', fields=fields).to_csv(WX.FILE['STOCK_LIST'], index=False, header=['CODE', 'NAME', 'AREA', 'INDUSTRY', 'FULLNAME', 'MARKET', 'LISTING_DATE', 'STATUS'], sep='\t')

    # 下载股票日线行情数据
    for date in dates:
        if not os.path.exists(WX.PATH['TS_DATE_OHLC'] + date):
            print('下载{0}日线行情数据'.format(date))
            daily = pro.daily(trade_date=date.replace('-', '')).sort_values(by=['ts_code'])
            daily.to_csv(WX.PATH['TS_DATE_OHLC'] + date, index=False, sep='\t')

    # 写入股票日线行情数据，单位：成交量（手）、成交额（千元）
    for date in dates:
        src = WX.PATH['TS_DATE_OHLC'] + date
        dst = WX.PATH['DATE_OHLC'] + date
        if not os.path.exists(dst):
            ohlc = pd.read_csv(src, usecols=['ts_code', 'open', 'high', 'low', 'close', 'pre_close', 'vol', 'amount'], sep='\t').rename(
                columns={'ts_code': 'CODE', 'open': 'OPEN', 'high': 'HIGH', 'low': 'LOW', 'close': 'CLOSE', 'pre_close': 'PRE_CLOSE', 'vol': 'VOLUME', 'amount': 'AMOUNT'}).set_index('CODE')
            print('处理{0}数据：{1}'.format(date, dst))
            ohlc.to_csv(dst, sep='\t', float_format='%.2f')

    # 转换成按股票的行情数据
    OHLC = pd.DataFrame(columns=['CODE', 'DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'PRE_CLOSE', 'VOLUME', 'AMOUNT']).set_index('CODE')
    for date in dates:
        print('读取{0}数据：{1}'.format(date, WX.PATH['DATE_OHLC'] + date))
        ohlc = pd.read_csv(WX.PATH['DATE_OHLC'] + date, index_col='CODE', sep='\t')
        ohlc['DATE'] = date
        OHLC = OHLC.append(ohlc)
    for code in codes:
        if code in OHLC.index:
            print('写入股票日线行情数据：{0} - {1}'.format(code, WX.STOCK_LIST.loc[code, 'NAME']))
            header = True if not os.path.exists(WX.PATH['STOCK_OHLC'] + code) else False
            OHLC[OHLC.index == code].to_csv(WX.PATH['STOCK_OHLC'] + code, mode='a', header=header, index=False, sep='\t', float_format='%.2f')


def reverse_K():
    K = pd.DataFrame()
    for code, row in WX.STOCK_LIST.iterrows():
        print('{0} - {1}'.format(code, row['NAME']))
        ohlc = read_stock_ohlc(code)[WX.START_DATE:]
        factor = read_stock_factor(code)[WX.START_DATE:]
        ohlc['RATE'] = (ohlc['CLOSE'] / ohlc['PRE_CLOSE'] - 1) * 100
        ohlc['POST_RATE'] = ohlc['RATE'].shift(-1)
        C1 = (ohlc['CLOSE'] - ohlc['PRE_CLOSE']).shift(1) < 0  # 前一天阴线
        C2 = (ohlc['CLOSE'] - ohlc['PRE_CLOSE']) > 0  # 当天是阳线
        C3 = ohlc['OPEN'] == ohlc['LOW']  # 开盘价即是最低价
        C4 = ohlc['CLOSE'] > ((ohlc['CLOSE'] + ohlc['OPEN']) / 2).shift(1)  # 阳线的收盘价至少要收复昨日阴线实体的一半
        C5 = (ohlc['HIGH'] - ohlc['CLOSE']) < (ohlc['CLOSE'] - ohlc['OPEN'])  # 阳线的上影线比阳线的实体要短
        C6 = ohlc['HIGH'].shift(1) > ohlc['CLOSE']  # 当天阳线的收盘价不高于昨日阴线的最高价
        C7 = ohlc['RATE'] >= 2  #
        ohlc = ohlc.loc[C1 & C2 & C3 & C4 & C5 & C6 & C7]
        ohlc.insert(0, 'CODE', code)
        K = K.append(ohlc)

    K.sort_index(inplace=True)
    K.to_csv('K', sep='\t', float_format='%.2f')
    df = pd.read_csv('K', index_col='DATE', sep='\t')
    print(df.groupby('DATE').apply(lambda t: t[t['RATE'] == t['RATE'].max()]))


def change_rate(ohlc, factor, start_date, interval):
    start_date, end_date = WX.TRADING_DATE[WX.TRADING_DATE >= start_date].iloc[[0, interval]]
    price = round(ohlc.loc[[start_date, end_date], ['PRE_CLOSE', 'CLOSE']].multiply(factor.loc[[start_date, end_date], 'FACTOR'], axis=0), 2)
    start_price = price.loc[start_date, 'PRE_CLOSE']
    end_price = price.loc[end_date, 'CLOSE']
    print(price)
    # print('{:.2%}'.format(end_price / start_price - 1))
    return end_price / start_price - 1


def K(ohlc, factor):
    ohlc[['ADJ_OPEN', 'ADJ_HIGH', 'ADJ_LOW', 'ADJ_CLOSE', 'ADJ_PRE_CLOSE']] = round(ohlc[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'PRE_CLOSE']].multiply(factor['FACTOR'], axis=0), 2)
    HIGH = ta.MAX(ohlc['ADJ_HIGH'], timeperiod=120)['2019-01-01':]
    # R = pd.DataFrame(columns=['DATE', 'HIGH', 'DIFF']).set_index('DATE')
    # R['DIFF'] = HIGH.diff()
    # print(R[R['DIFF'] > 0])
    ohlc = ohlc.loc[HIGH[HIGH.diff() > 0].index]
    intervals = [2, 5, 10, 20]


if __name__ == '__main__':
    WX.PATH['STOCK_OHLC'] = 'stock/2010-2019/'
    code = '300418.SZ'
    ohlc = read_stock_ohlc(code)
    factor = read_stock_factor(code)
    K(ohlc, factor)
    # change_rate(ohlc, factor, '2015-11-10', 2)

# write_stock_factor(WX.TRADING_DATE[WX.TRADING_DATE >= '2020-03-05'], WX.STOCK_LIST.index)
