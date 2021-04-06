class AccountAPI:
    def __init__(self, orders, order_history=None):
        self._orders = orders
        self._order_history = order_history

    @property
    def orders(self):
        return {o.id: o for o in self._orders}

    @property
    def order_history(self):
        return self._order_history
