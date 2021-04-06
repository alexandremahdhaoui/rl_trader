import numpy as np
import pandas as pd
from rl_trader.engine.data.raw_datasets import get_raw_ds

SUB_PATH = 'context'
MEAN_STD_SUB_PATH = 'mean_std'


def _csv_path(path, filename):
    return f'{path}/{SUB_PATH}/{filename}.csv'


def _mean_std_csv_path(path, filename):
    return f'{path}/{SUB_PATH}/{MEAN_STD_SUB_PATH}/{filename}.csv'


def _scale_context(context):
    prices = []
    volumes = []
    for el in context:
        for i, value in enumerate(el):
            if i < 4:
                prices.append(value)
            else:
                volumes.append(value)

    prices, volumes = np.array(prices, dtype=np.float), np.array(volumes, dtype=np.float)
    mean, std = np.mean(prices), np.std(prices)
    for i, value in enumerate(prices):
        prices[i] = (value - mean) / std

    mean_, std_ = np.mean(volumes), np.std(volumes)
    for i, value in enumerate(volumes):
        volumes[i] = (value - mean_) / std_

    context_ = []
    for c in range(5):
        t_ = []
        for t in range(5):
            if t < 4:
                t_.append(prices[t + c * 4])
            else:
                t_.append(volumes[c])
        context_.append(t_)
    return context_, [mean, std]


def _make_context_ds(filename, path='datasets', symbol='tETHUSD', time_frame='1m', time_period=1):
    raw_ds = get_raw_ds(path=path, symbol=symbol, time_frame=time_frame, time_period=time_period,
                        filename=filename)
    context_ds = []
    mean_std_ds = []
    for t in range(60, raw_ds.__len__()):
        context = [
            raw_ds[t - 60],
            raw_ds[t - 30],
            raw_ds[t - 15],
            raw_ds[t - 5],
            raw_ds[t],
        ]
        context = np.reshape(context, (5, 5))
        context, mean_std = _scale_context(context)
        context_ds.append(np.array(context))
        mean_std_ds.append(np.array(mean_std))

    context_ds = np.array(context_ds, dtype=np.float)
    context_ds = context_ds.reshape((
        context_ds.shape[0],
        context_ds.shape[1] * context_ds.shape[2]
    ))

    context_cols = np.array([
        't-60_open', 't-60_close', 't-60_high', 't-60_low', 't-60_volume',
        't-30_open', 't-30_close', 't-30_high', 't-30_low', 't-30_volume',
        't-15_open', 't-15_close', 't-15_high', 't-15_low', 't-15_volume',
        't-5_open', 't-5_close', 't-5_high', 't-5_low', 't-5_volume',
        't_open', 't_close', 't_high', 't_low', 't_volume',
    ])

    df = pd.DataFrame(context_ds, columns=context_cols)
    df.to_csv(_csv_path(path, filename), index=False)

    mean_std_ds = np.array(mean_std_ds, dtype=np.float)
    np.savetxt(_mean_std_csv_path(path, filename), mean_std_ds, delimiter=',', header='mean, standard deviation')


def _read_context_csv(path, filename):
    return pd.read_csv(_csv_path(path, filename))


def _read_mean_std_csv(path, filename):
    return pd.read_csv(_mean_std_csv_path(path, filename))


def get_context_ds(path='datasets', symbol='tETHUSD', time_frame='1m', time_period=1, filename=None):
    if filename is None:
        filename = (symbol + '_' + time_frame + '_' + str(time_period)).lower()
    try:
        return _read_context_csv(path, filename), _read_mean_std_csv(path, filename)
    except:
        print(f'file {filename} at {path} does not exist. Getting data from API and creating csv file...')
        _make_context_ds(filename, path=path, symbol=symbol, time_frame=time_frame, time_period=time_period)
        return _read_context_csv(path, filename), _read_mean_std_csv(path, filename)
