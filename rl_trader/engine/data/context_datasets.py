# TODO:  get_context_ds() has to return a GENERATOR/ITERATOR
# TODO: Documentation
import numpy as np
import pandas as pd
from numpy.core._multiarray_umath import ndarray

from rl_trader.engine.data.raw_datasets import get_raw_ds

CONTEXT_RANGE = 60                          # Can change context range to 30 or 12. Or even to 180
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


def _make_context_ds(filename, path='datasets', pair='tETHUSD', time_frame='1m', time_period=1):
    raw_ds = get_raw_ds(path=path, pair=pair, time_frame=time_frame, time_period=time_period,
                        filename=filename)
    context_ds = []
    mean_std_ds = []
    _2, _4, _12, _cr = int(CONTEXT_RANGE / 2), int(CONTEXT_RANGE / 4), int(CONTEXT_RANGE / 12), CONTEXT_RANGE
    for t in range(CONTEXT_RANGE, raw_ds.__len__()):
        context = [
            raw_ds[t - CONTEXT_RANGE],              # t-60
            raw_ds[t - _2],                         # t-30
            raw_ds[t - _4],                         # t-15
            raw_ds[t - _12],                        # t-5
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
        f't-{_cr}_open', f't-{_cr}_close', f't-{_cr}_high', f't-{_cr}_low', f't-{_cr}_volume',
        f't-{_2}_open', f't-{_2}_close', f't-{_2}_high', f't-{_2}_low', f't-{_2}_volume',
        f't-{_4}_open', f't-{_4}_close', f't-{_4}_high', f't-{_4}_low', f't-{_4}_volume',
        f't-{_12}_open', f't-{_12}_close', f't-{_12}_high', f't-{_12}_low', f't-{_12}_volume',
        't_open', 't_close', 't_high', 't_low', 't_volume',
    ])

    df = pd.DataFrame(context_ds, columns=context_cols)
    df.to_csv(_csv_path(path, filename), index=False)

    mean_std_ds = np.array(mean_std_ds, dtype=np.float)
    # noinspection PyTypeChecker
    np.savetxt(_mean_std_csv_path(path, filename), mean_std_ds, delimiter=',', header='mean, standard deviation')


def _read_context_csv(path, filename):
    return pd.read_csv(_csv_path(path, filename))


def _read_mean_std_csv(path, filename):
    return pd.read_csv(_mean_std_csv_path(path, filename))


def get_context_ds(path='datasets', pair='tETHUSD', time_frame='1m', time_period=1, filename=None):
    """
    Attributes:
        path:
        pair:
        time_frame:
        time_period:
        filename:
    :return: context_ds, mean_std_ds
        The mean_std dataset is used to resolve Order.price from the 'scaled_price' of the agent.
        We want the agent to decide prices accordingly to the current context he is seeing.
        To resolve price: scaled_price = (price - mean)/std <=> price = (sc_price * std) + mean
    """
    if filename is None:
        filename = (pair + '_' + time_frame + '_' + str(time_period)).lower()
    try:
        return _read_context_csv(path, filename), _read_mean_std_csv(path, filename)
    except:
        print(f'file {filename} at {path} does not exist. Getting data from API and creating csv file...')
        _make_context_ds(filename, path=path, pair=pair, time_frame=time_frame, time_period=time_period)
        return _read_context_csv(path, filename), _read_mean_std_csv(path, filename)
