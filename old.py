import WX
import json
import os
import numpy as np
import pandas as pd
import requests
import tushare as ts
from WindPy import w

STOCK_LIST_URL = 'http://stock.gtimg.cn/data/index.php?appn=rank&t=ranka/code&p=1&o=1&l=5000&v=stock_list'
STOCK_OHLC_URL = 'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={0},day,{1},{2},10000,'
INDUSTRY_URL = 'http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C._BKHY&sty=FPGBKI&st=c&sr=-1&p=1&ps=5000&cb=&js=[(x)]&token=7bc05d0d4c3c22ef9fca8c2a912d779c'
STOCK_INDUSTRY_URL = 'http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?type=CT&cmd=C.{0}1&sty=FCOIATA&sortType=C&sortRule=-1&page=1&pageSize=500&js=[(x)]&token=7bc05d0d4c3c22ef9fca8c2a912d779c'


def download_stock():
    # 股票列表
    file = WX.PATH['DOWNLOAD_STOCK_LIST'] + WX.TODAY
    if not os.path.exists(file):
        print('正在下载股票列表至：' + file)
        error, data = w.wset('listedsecuritygeneralview', 'sectorid=a001010100000000', usedf=True)
        data.to_csv(file, sep='\t', float_format='%.2f')
        stock_list = pd.read_csv(file, usecols=['wind_code', 'sec_name', 'close_price', 'total_market_value', 'mkt_cap_float', 'ipo_date'], sep='\t').rename(
            columns={'wind_code': 'CODE', 'sec_name': 'NAME', 'close_price': 'PRICE', 'total_market_value': 'TOTAL_VALUE', 'mkt_cap_float': 'FLOAT_VALUE', 'ipo_date': 'IPO_DATE'}).set_index('CODE')
        stock_list.to_csv(WX.FILE['STOCK_LIST'], sep='\t', float_format='%.2f')

    # 股票IPO
    file = WX.PATH['DOWNLOAD_STOCK_IPO'] + WX.TODAY
    if not os.path.exists(file):
        print('正在下载股票发行资料至：' + file)
        error, data = w.wset('newstockissueinfo', 'startdate={0};enddate={1};datetype=online;board=0'.format(WX.FIRST_DATE, WX.LAST_DATE), usedf=True)
        data.to_csv(file, sep='\t', float_format='%.2f')
        stock_ipo = pd.read_csv(file, usecols=['wind_code', 'listing_date', 'issue_price', 'province', 'csrc_industry'], sep='\t').rename(
            columns={'wind_code': 'CODE', 'listing_date': 'LISTING_DATE', 'issue_price': 'ISSUE_PRICE', 'province': 'PROVINCE', 'csrc_industry': 'INDUSTRY'}).set_index('CODE')
        stock_ipo.to_csv(WX.FILE['STOCK_IPO'], sep='\t', float_format='%.2f')

    # 股票行情
    for code, row in stock_list().iterrows():
        file = WX.PATH['DOWNLOAD_STOCK_OHLC'] + WX.TODAY + '/' + code
        if not os.path.exists(file):
            # 600000.SH -> sh600000
            code_tx = '{0[1]}{0[0]}'.format(code.lower().split('.'))
            download_url = STOCK_OHLC_URL.format(code_tx, WX.START_DATE, WX.END_DATE)
            print('正在下载股票行情：{0} - {1}，下载地址：{2}'.format(code, row['NAME'], download_url))
            text = requests.get(download_url).text
            with open(file, 'w') as file:
                file.write(text)


def write_stock_ohlc(code, date=WX.TODAY):
    with open(WX.PATH['DOWNLOAD_STOCK_OHLC'] + date + '/' + code, 'r') as file:
        # 600000.SH -> sh600000
        code_tx = '{0[1]}{0[0]}'.format(code.lower().split('.'))
        data = json.load(file)['data'][code_tx]['day']

    if 'FHcontent' not in str(data):
        ohlc = pd.DataFrame(data, columns=['DATE', 'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME'], dtype=np.float64).set_index('DATE')
        factor = pd.DataFrame(columns=['FACTOR', 'CONTENT'])
    else:
        df = pd.DataFrame(data, columns=['DATE', 'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME', 'CONTENT'], dtype=np.float64).set_index('DATE')
        ohlc = df[['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']]
        factor = df[['CONTENT']].dropna()
        factor.insert(0, 'FACTOR', np.nan)
    ohlc.insert(0, 'PRE_CLOSE', ohlc['CLOSE'].shift(1))

    stock_ohlc = read_stock_ohlc(code)
    if stock_ohlc is not None and len(stock_ohlc) != 0:
        end_date = stock_ohlc.index[-1]
        ohlc = ohlc[end_date:].iloc[1:]
        factor = factor[end_date:].iloc[1:]
    for date in ohlc.index:
        if date in factor.index:
            content = factor.loc[date, 'CONTENT']['FHcontent']
            dividend = share = 0
            if '派' in content:
                dividend = float(content[content.find('派') + 1:content.find('元')])
            if '送' in content:
                share += float(content[content.find('送') + 1:content.find('股')])
            if '转' in content:
                share += float(content[content.find('转') + 1:content.rfind('股')])
            pre_close = ohlc.loc[date, 'PRE_CLOSE']
            # 除权价=（除权前一日收盘价+配股价X配股比率－每股派息）/（1+配股比率+送股比率）
            ohlc.loc[date, 'PRE_CLOSE'] = round((pre_close - dividend / 10) / (1 + share / 10), 2)
            factor.loc[date, 'FACTOR'] = ohlc.loc[date, 'PRE_CLOSE'] / pre_close
            factor.loc[date, 'CONTENT'] = content
    # print('追加写入{0}条行情数据，{1}条分红送配数据'.format(len(ohlc), len(factor)))
    ohlc.to_csv(WX.PATH['STOCK_OHLC'] + code, mode='a', header=False, sep='\t', float_format='%.2f')
    factor.to_csv(WX.PATH['STOCK_FACTOR'] + code, mode='a', header=False, sep='\t', float_format='%.8f')
