import uuid

from rl_trader.engine.rl_environment.types.env_market_types import Market
from rl_trader.engine.rl_environment.types.env_account_types import Wallets, Order, TokenWallet
from rl_trader.engine.rl_environment.account_api.account_api import AccountAPI


class FakeWallets(Wallets):
    def __init__(self, symbols: list, fake_usd_start=20):
        super(FakeWallets, self).__init__()
        self.make_fake_token_wallets(symbols, fake_usd_start=fake_usd_start)

    def make_fake_token_wallets(self, symbols: list, fake_usd_start=20):
        _tokens = []
        for s in symbols:
            if s == 'USD':
                _tokens.append(TokenWallet(s, balance=fake_usd_start))
            _tokens.append(TokenWallet(s))
        self._tokens = _tokens

    def check_token_balance(self, token_symbol: str, amount_symbol):
        if self.balances[token_symbol] >= amount_symbol:
            return True
        else:
            return False

    def resolve_balance_from_dict(self, dict_: dict):
        for key, value in dict_:
            self.balances[key] += value


class FakeOrder(Order):
    """
    Arguments:
        order_id,
        pair: str e.g= 'tETHUSD',
        order_type: str = 'buy' or 'sell',
        price: float = price of execution of the order,
        amount: float = amount refers to amount you buy if order_type='buy', amount you sell if order_type='sell'
    Attributes:
        order_id,
        pair,
        order_type,
        price,
        amount: float: always the amount we get -> get_amount = amount,
        status,
        get_symbol,
        give_symbol,
        get_amount: amount of get_symbol we want to buy,
        give_amount: amount of give_symbol that will has to be exchanged for get_amount of get_symbol
    Methods:
        is_resolvable,
        execute
    """

    def __init__(self, order_id, pair, order_type, price, amount):
        super(FakeOrder, self).__init__(order_id, pair, order_type, price, amount, status='created')

    def is_executable(self, pair, low, high):
        if pair == self.pair:
            if (low >= self.price and self.order_type == 'buy') or (high <= self.price and self.order_type == 'sell'):
                return True
            else:
                return False
        else:
            return False

    def execute(self):
        self.status = 'executed'


class FakeAPI(AccountAPI):
    def __init__(self, pairs, symbols, fake_usd_start=20):
        super(FakeAPI, self).__init__([], order_history=[])
        self.wallets = FakeWallets(symbols, fake_usd_start)
        self._market = Market(pairs)

    def create_order(self, pair, order_type, price, amount):
        order_id = uuid.uuid1()
        order = FakeOrder(order_id, pair, order_type, price, amount)
        self._orders.append(order)
        return 'order_id'

    def cancel_order(self, order_id):
        order = self._remove_from_orders(order_id)
        order.update(status='cancelled')
        self._order_history.append(order)

    def next_time_step(self, market_updates):
        """
        Arguments:
            market_updates: instance of type Market
        """
        self.market = market_updates
        self._resolve_orders()
        return self.wallets.balances, self.orders

    def _remove_from_orders(self, order_id):
        return self._orders.pop(next(i for i, o in enumerate(self.orders) if order_id == o.id))

    def _resolve_orders(self):
        ORDER_FEE = 2e-3    # 0.2%
        for key, object_ in self.market:
            low, high = object_.low, object_.high
            for order in self.orders:
                if order.is_resolvable(key, low, high):
                    if self.wallets.check_token_balance(order.give_symbol, order.give_amount + ORDER_FEE * order.give_amount):
                        order.execute()
                        self._remove_from_orders(order.id)
                        self._order_history.append(order)

                        dict_ = {order.get_symbol: order.get_amount,
                                 order.give_symbol: (0 - (order.give_amount + ORDER_FEE * order.give_amount))}
                        self.wallets.resolve_balance_from_dict(dict_)

    @property
    def market(self):
        return self._market.pairs

    @market.setter
    def market(self, market_update):
        for key, object_ in self.market.pairs:
            if key in market_update.pairs.keys:
                object_.low = market_update.pairs[key].low
                object_.high = market_update.pairs[key].high
