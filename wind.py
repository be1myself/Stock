import pandas as pd
from WindPy import w

import WX


def start():
    w.start()

    # 货币基金万份收益和七日年化
    fund = WX.MMF
    print('基金：' + fund)
    code = fund.split('-')[0].strip()
    error, data = w.wsd(code, 'mmf_unityield', WX.START_DATE, WX.END_DATE, 'Days=Alldays', usedf=True)
    data.dropna().to_csv(WX.PATH['FUND_MMF'] + code, index_label='DATE', header=['EARNING'], sep='\t', float_format='%.4f')
    data = pd.read_csv(WX.PATH['FUND_MMF'] + code, index_col='DATE', sep='\t')
    flag = False
    value = 0
    # 非交易日收益全部计入下一交易日
    for date, row in data.iterrows():
        if date not in WX.TRADING_DATE.values:
            flag = True
            value += row[0]
            data.drop(date, inplace=True)
        else:
            if flag:
                flag = False
                data.loc[date] += value
                value = 0
    data.to_csv(WX.PATH['FUND_MMF'] + code, sep='\t', index_label='DATE', header=['EARNING'], float_format='%.4f')

    # 基金单位净值，累计净值，复权净值
    for fund in WX.FUND:
        print('基金：' + fund)
        code = fund.split('-')[0].strip()
        error, data = w.wsd(code, 'nav,NAV_acc,NAV_adj', WX.START_DATE, WX.END_DATE, usedf=True)
        data.dropna().to_csv(WX.PATH['FUND_NAV'] + code, index_label='DATE', header=['NAV', 'NAV_ACC', 'NAV_ADJ'], sep='\t', float_format='%.4f')

    # 两市融资融券
    # print('融资融券：')
    # error, data = w.wset('markettradingstatistics(value)',
    #                      'exchange=shsz;startdate=2010-01-01;enddate=' + END_DATE + ';frequency=day;sort=asc;'
    #                      + 'field=end_date,shsz_total_balance,margin_balance,period_bought_amount,margin_paid_amount,short_balance,sold_amount,short_paid_amount',
    #                      usedf=True)
    # data['end_date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    # data.dropna().set_index('end_date').astype('float64').to_csv('margin/margin', index_label='DATE',
    #                                                              header=['TOTAL_BALANCE', 'MARGIN_BALANCE',
    #                                                                      'MARGIN_BOUGHT', 'MARGIN_PAID',
    #                                                                      'SHORT_BALANCE', 'SHORT_SOLD', 'SHORT_PAID'],
    #                                                              sep='\t', float_format='%.0f')
    w.stop()


def download_index():
    w.start()
    for code, name in WX.INDEX.items():
        print('下载指数：{0} - {1}'.format(code, name))
        error, data = w.wsd(code, 'pre_close,open,high,low,close,amt,pe_ttm,pb_lf', WX.FIRST_DATE, WX.LAST_DATE, usedf=True)
        # data[['PRE_CLOSE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'AMT']].dropna().to_csv(WX.PATH['INDEX_OHLC'] + code, index_label='DATE', header=['PRE_CLOSE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'AMOUNT'], sep='\t', float_format='%.2f')
        data[['PE_TTM', 'PB_LF']].dropna().to_csv(WX.PATH['INDEX_INDICATOR'] + code, index_label='DATE', sep='\t', float_format='%.4f')
    w.stop()


start()