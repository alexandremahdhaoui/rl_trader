class PairMarketValue:
    """
    :arg:
        pair: str, e.g = 'tETHUSD'
    :param:
        pair: str
        open: float
        close: float
        high: float
        low: float
        volume: float
    """
    def __init__(self, pair):
        self.pair = pair


class Market:
    """
    Market is a type for Market objects: represent a list of PairMarketValue
    :arg:
        pairs: list(str)
    :param
        _pairs: list( instance( PairMarketValue ) )
        pairs: {p.pair: p for p in self._pairs}
    """
    def __init__(self, pairs):
        self._get_pairs_object(pairs)

    def _get_pairs_object(self, pairs):
        list_ = []
        for pair in pairs:
            list_.append(PairMarketValue(pair))
        self._pairs = list_

    @property
    def pairs(self):
        return {p.pair: p for p in self._pairs}
