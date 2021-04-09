import uuid

from rl_trader.engine.rl_environment.types.env_market_types import Market
from rl_trader.engine.rl_environment.account_api.types.account_types import Wallets, Order, TokenWallet
from rl_trader.engine.rl_environment.account_api.types.account_types import AccountAPI


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
        if self.wallets[token_symbol] >= amount_symbol:
            return True
        else:
            return False

    def resolve_balance_from_dict(self, dict_: dict):
        for key, value in dict_:
            self.wallets[key] += value


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
    _market: Market

    def __init__(self, symbols, fake_usd_start=20):
        super(FakeAPI, self).__init__([], order_history=[])
        self.wallets = FakeWallets(symbols, fake_usd_start)

    def init_market(self, market_obj: Market):
        self._market = market_obj

    def create_order(self, pair, order_type, price, amount):
        order_id = uuid.uuid1()
        order = FakeOrder(order_id, pair, order_type, price, amount)
        self._orders.append(order)
        return 'order_id'

    def cancel_order(self, order_id):
        order = self._remove_from_orders(order_id)
        order.update(status='cancelled')
        self._order_history.append(order)

    def step(self):
        """
        :returns:
            wallets: dict = {pair: balance}
            open_orders: list of {'order_id': str, 'pair': str, 'order_type': str, 'price': float,'amount': float},
            total_balance: int
        }
        """
        self._resolve_orders()
        return self.wallets.wallets, self.open_orders, self._compute_total_balance()

    def _compute_total_balance(self):
        # if pair is always equals to 'xYYYUSD' then we can compute the total_balance of all
        # With self.wallets.wallets and self.markets
        # Compute value in USD of a symbol: market[pair].close * symbol_balance
        b: float = self.wallets.wallets['USD']
        for pair, obj_ in self.market:
            symbol_balance = self.wallets.wallets[pair[1:4]]
            b += symbol_balance * obj_.close
        return b

    def _remove_from_orders(self, order_id):
        return self._orders.pop(next(i for i, o in enumerate(self.orders) if order_id == o.id))

    def _resolve_orders(self):
        ORDER_FEE = 2e-3  # 0.2%
        for pair, object_ in self.market:
            low, high = object_.low, object_.high
            for _, order in self.orders:
                if order.is_resolvable(pair, low, high):
                    if self.wallets.check_token_balance(order.give_symbol,
                                                        order.give_amount + ORDER_FEE * order.give_amount):
                        order.execute()
                        self._remove_from_orders(order.id)
                        self._order_history.append(order)

                        dict_ = {order.get_symbol: order.get_amount,
                                 order.give_symbol: (0 - (order.give_amount + ORDER_FEE * order.give_amount))}
                        self.wallets.resolve_balance_from_dict(dict_)

    @property
    def market(self):
        return self._market.pairs
