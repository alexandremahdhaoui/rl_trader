class TokenWallet:
    """
    Type for the balance of a single token
    Please provide getter and setter for self._balance when implementing that type
    """

    def __init__(self, symbol, balance=0):
        self._balance = balance
        self.symbol = symbol

    def update(self, update):
        try:
            self.balance = update
            return f'Balance of token {self.symbol} successfully updated: {self.balance}'
        except:
            return f'Error while trying to update the balance of token {self.symbol}'

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, b):
        self._balance = b


class Wallets:
    """
    Type for Balance objects
    Please provide GETTER and SETTER for self._tokens when implementing that type
    -> self._tokens has to return a list of object of TokenBalance type.
    """

    def __init__(self):
        self._tokens = []
        self.history_log = []

    def update(self, updates):
        for symbol, update in updates.items:
            token_wallet = self.tokens[symbol]
            log = token_wallet.update(update)
            self.history_log.append(log)

    @property
    def tokens(self):
        # Return a dict
        return {t.symbol: t for t in self._tokens}

    @property
    def balances(self):
        return {t.symbol: t.balance for t in self._tokens}


class Order:
    """
    Arguments:
        order_id,
        pair,
        order_type,
        price,
        amount
    Attributes:
        order_id,
        pair,
        order_type,
        price,
        amount,
        status,
        get_symbol,
        give_symbol,
        get_amount,
        give_amount
    """
    def __init__(self,  order_id, pair, order_type, price, amount, status='created'):
        self.order_id = order_id
        self.pair = pair
        self.order_type = order_type
        self.price = price
        self.amount = amount
        self.status = status
        self._get_give_symbols()

    def update(self, **kwargs):
        authorized_kwargs = ['id', 'pair', 'order_type', 'price', 'status']
        for key, value in kwargs.items():
            if key not in authorized_kwargs:
                raise ValueError(f'key {key} is not a valid keyword argument')
            self.__dict__[key] = value

    def _get_give_symbols(self):
        if self.order_type == 'buy':
            self.get_symbol, self.give_symbol = self.pair[1:4], self.pair[4:7]
        if self.order_type == 'sell':
            self.give_symbol, self.get_symbol = self.pair[1:4], self.pair[4:7]

    @property
    def get_amount(self):
        return self.amount

    @property
    def give_amount(self):
        if self.order_type == 'buy':
            return self.amount * self.price
        if self.order_type == 'sell':
            return self.amount * (1/self.price)
