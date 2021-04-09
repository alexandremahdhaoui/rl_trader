# TODO: Documentation

from rl_trader.engine.rl_environment.account_api.fake_api import FakeAPI
from rl_trader.engine.rl_environment.account_api.platform_api import PlatformAPI
from rl_trader.engine.data.context_datasets import get_context_ds
from rl_trader.engine.data.raw_datasets import get_raw_ds
from rl_trader.engine.rl_environment.types.env_market_types import Market

import numpy as np

CONTEXT_RANGE = 60


class Environment:
    def __init__(self,
                 pairs,
                 symbols,
                 time_period=1,
                 fake_usd_start=20,
                 ):
        self.fake_usd_start = fake_usd_start
        self.pairs, self.symbols = pairs, symbols
        self.time_period = time_period
        self._get_ds_from_symbols()
        self.reset()

    def reset(self):
        """
        :return: observation of time_step=0
        """
        self.training_api = FakeAPI(self.symbols, fake_usd_start=self.fake_usd_start)
        self._reset_counter()
        self._reset_history()
        self._init_market()

        self._update_context()
        self._update_market()
        wallets, open_orders, total_balance = self.training_api.step()
        observation = (self.context, wallets, open_orders)
        self._increment_counter()
        return observation

    def step(self, a: dict):
        """
        :param
            a: { create_order: list of order describing dict, cancel_order: list of order_id }
        :return: (
            observation,
            reward,
            done,
            info
        )
        """
        # TODO: Create step fn.
        #   - Get observation=[context, wallets, open_orders]
        #   - Compute rewards
        # START
        # Compute actions -> Meaning compute training_api.create_order() and training_api.cancel_order()
        self._compute_actions(a)
        # Update time-step
        self._update_context()
        self._update_market()
        # Get wallets, open_orders, total_balance
        wallets, open_orders, total_balance = self.training_api.step()
        self.history['total_balance'].append(total_balance)
        # Get observation
        observation = (self.context, wallets, open_orders)
        # Compute rewards
        reward: float = self._compute_rewards()
        # END
        if self.counter < self.final_step and total_balance >= self.fake_usd_start/2:
            done = False
            self._increment_counter()
        else:
            done = True
        return (
            observation,
            reward,
            done,
            'info'
        )

    def _compute_actions(self, a):
        """
        :param:
            a: {
            create_order: list of dict describing pair, order_type, price, amount,
            cancel_order: list of order_id
            }
        """
        for order in a['create_order']:
            self.training_api.create_order(
                order['pair'],
                order['order_type'],
                order['price'],
                order['amount'],
            )
        for order_id in a['cancel_order']:
            self.training_api.cancel_order(order_id)

    def _compute_rewards(self):
        # We will use Context Reward Scaling (Proposition 4.a.)
        # Reward = (b(T=t) - mean) / std --> b(t) is the sum of balances when Time = t
        # If context reward scaling is ineffective please try using Proposition 2.b.: (b(t) - b(t-1)) / b(t)
        # To get b(t-60): with t=13 do if t<60: b(t-60)=b(t-t)
        balance_ctx = self._get_reward_context()
        reward: float = (balance_ctx - np.mean(balance_ctx)) / np.std(balance_ctx)[-1]
        return reward

    def _get_reward_context(self):
        t = self.counter
        b_hist = self.history['total_balance']
        _2, _4, _12, _cr = int(CONTEXT_RANGE / 2), int(CONTEXT_RANGE / 4), int(CONTEXT_RANGE / 12), CONTEXT_RANGE
        if t < _cr:
            _cr = t
        if t < _2:
            _2 = t
        if t < _4:
            _4 = t
        if t < _12:
            _12 = t
        balance_ctx = [
            b_hist[t - _cr],
            b_hist[t - _2],
            b_hist[t - _4],
            b_hist[t - _12],
            b_hist[t],
        ]
        return balance_ctx

    def _get_ds_from_symbols(self):
        self.context_ds, self.mean_std_ds = {}, {}
        self.market_ds = {}
        for pair in self.pairs:
            self.context_ds[pair], self.mean_std_ds[pair] = get_context_ds(
                pair=pair,
                time_period=self.time_period
            )
            self.market_ds[pair] = get_raw_ds(pair=pair, time_period=self.time_period)

    def _init_market(self):
        self._market = Market(self.pairs)
        self.training_api.init_market(self._market)

    def _reset_counter(self):
        self._counter = 0

    def _reset_history(self):
        self.history = {}

    def _increment_counter(self):
        self._counter += 1

    def _update_context(self):
        current_context = {}
        for pair in self.pairs:
            current_context[pair] = self.context_ds[pair][self.counter]
        self._context = current_context

    def _update_mean_std(self):
        current_mean_std = {}
        for pair in self.pairs:
            current_mean_std[pair] = self.mean_std_ds[pair][self.counter]

    def _update_market(self):
        for pair, object_ in self._market.pairs:
            time_open_close_high_low_volume = self.market_ds[pair][self.counter + CONTEXT_RANGE]
            object_.open = time_open_close_high_low_volume[1]
            object_.close = time_open_close_high_low_volume[2]
            object_.high = time_open_close_high_low_volume[3]
            object_.low = time_open_close_high_low_volume[4]
            object_.volume = time_open_close_high_low_volume[5]

    @property
    def counter(self):
        return self._counter

    @property
    def final_step(self):
        return self.context_ds.__len__()

    @property
    def market(self):
        return self._market.pairs

    @property
    def context(self):
        return self._context
