import time
import csv
import pandas as pd
import numpy as np
from rl_trader.engine.platform_handler.get_candles import get_candles

SUB_PATH = 'raw'


def _csv_path(path, filename):
    return f'{path}/{SUB_PATH}/{filename}.csv'


def _get_raw_candles(start_time, end_time, symbol='tETHUSD', time_frame='1m'):
    candles = get_candles(start_time=start_time, end_time=end_time,
                          symbol=symbol, time_frame=time_frame)
    candles = np.array(candles)
    candles = np.sort(candles, axis=0)
    _t, _o, _c, _h, _l, _v = [], [], [], [], [], []
    for i, c in enumerate(candles):
        last_v = 0
        if i > 0:
            last_v = _v[i - 1]
        _t.append(int(c[0])), _o.append(c[1]), _c.append(c[2]), _h.append(c[3]), _l.append(c[4]), _v.append(
            c[5] - last_v)
    return _t, _o, _c, _h, _l, _v


def _make_raw_ds(filename, path='datasets', symbol='tETHUSD', time_frame='1m', time_period=1):
    _t, _o, _c, _h, _l, _v = [], [], [], [], [], []

    NOW = int(round(time.time() * 1000))
    start_time = int(NOW - 8.64e+7 * time_period)
    for t in range(1, time_period+1):
        end_time = int(start_time + 8.64e+7 * t)
        t, o, c, h, l, v = _get_raw_candles(start_time=start_time, end_time=end_time,
                                            symbol=symbol, time_frame=time_frame)
        _t.extend(t), _o.extend(o), _c.extend(c), _h.extend(h), _l.extend(l), _v.extend(v)
    dict_ = {'time': _t, 'open': _o, 'close': _c, 'high': _h, 'low': _l, 'volume': _v}
    df = pd.DataFrame(dict_)
    df.to_csv(_csv_path(path, filename), index=False)


def _read_raw_csv(path, filename):
    with open(_csv_path(path, filename)) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        ds = []
        for row in reader:
            ds.append([row[1:]])
        return ds


def get_raw_ds(path='datasets', symbol='tETHUSD', time_frame='1m', time_period=1, filename=None):
    if filename is None:
        filename = (symbol + '_' + time_frame + '_' + str(time_period)).lower()
    try:
        return _read_raw_csv(path, filename)

    except:
        print(f'file {filename} at {path} does not exist. Getting data from API and creating csv file...')
        _make_raw_ds(filename, path, symbol=symbol, time_frame=time_frame, time_period=time_period)
        return _read_raw_csv(path, filename)
