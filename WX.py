import datetime as dt
import os
import pandas as pd

FIRST_DATE = '2000-01-01'
START_DATE = '2010-01-01'
LAST_DATE = END_DATE = TODAY = str(dt.date.today())

PATH = {
    'INDEX_OHLC': 'index/ohlc/',
    'INDEX_INDICATOR': 'index/indicator/',
    'INDEX_INDICATOR_PERCENTILE': 'index/indicator/percentile/',
    'FUND_NAV': 'fund/nav/',
    'FUND_MMF': 'fund/mmf/',
    'STOCK_OHLC': 'stock/ohlc/',
    'STOCK_FACTOR': 'stock/factor/',
    'DATE_OHLC': 'date/ohlc/',
    'DATE_FACTOR': 'date/factor/',
    'DATE_NAV': 'fund/nav',

    'TS_STOCK_OHLC': 'download/stock/ohlc/' + TODAY + '/',
    'TS_DATE_OHLC': 'download/date/ohlc/',
    'TS_DATE_FACTOR': 'download/date/factor/',
    'TS_INDEX_OHLC': 'download/index/ohlc/' + TODAY + '/'
    # 'TS_FUND_NAV': 'download/fund/nav/' + TODAY + '/',
}

FILE = {
    'TRADING_DATE': 'date/TRADING_DATE',
    'TS_STOCK_LIST': 'download/tushare/stock_basic',
    'STOCK_LIST': 'stock/STOCK_LIST',
}
for path in PATH.values():
    if not os.path.exists(path):
        os.makedirs(path)

INDEX = {
    '000001.SH': '上证综指',
    '399001.SZ': '深证成指',
    '399006.SZ': '创业板指',
    '000016.SH': '上证50',
    '000300.SH': '沪深300',
    '000905.SH': '中证500',
    '000922.CSI': '中证红利',
    '399975.SZ': '证券公司',
    '399967.SZ': '中证军工',
    '399976.SZ': '新能源车'
}

# INDEX = ['000001.SH - 上证综指', '000016.SH - 上证50', '000300.SH - 沪深300', '000905.SH - 中证500', '000922.CSI - 中证红利',
#          '399975.SZ - 证券公司', '399967.SZ - 中证军工', '399976.SZ - 新能源车']
FUND = ['100053.OF - 富国上证综指ETF联接', '110003.OF - 易方达上证50指数A', '100038.OF - 富国沪深300指数增强', '161017.OF - 富国中证500指数增强', '100032.OF - 富国中证红利指数增强',
        '161027.OF - 富国中证全指证券公司指数分级', '161024.OF - 富国中证军工指数分级', '161028.OF - 富国中证新能源汽车指数分级',
        '161005.OF - 富国天惠成长混合A', '002593.OF - 富国美丽中国混合', '000029.OF - 富国宏观策略灵活配置混合', '001371.OF - 富国沪港深价值混合']
MMF = '000638.OF - 富国富钱包货币'
INDEX_FUND = {'000001.SH': '100053.OF', '000016.SH': '110003.OF', '000300.SH': '100038.OF', '000905.SH': '161017.OF',
              '000922.CSI': '100032.OF',
              '399975.SZ': '161027.OF', '399967.SZ': '161024.OF', '399976.SZ': '161028.OF'}

TRADING_DATE = pd.read_csv(FILE['TRADING_DATE'])['DATE']
STOCK_LIST = pd.read_csv(FILE['STOCK_LIST'], index_col='CODE', sep='\t')
