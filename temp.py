import pandas as pd
import os
import numpy as np
import datetime as dt
import tushare as ts
import WX

pro = ts.pro_api('54c728c38a187a7a355174a0070c033f3f776fa5c3fd500c6c71225e')
df = pro.index_dailybasic(ts_code='000300.SH')
print(df)