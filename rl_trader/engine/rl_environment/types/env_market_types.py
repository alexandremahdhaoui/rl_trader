class PairMarketValue:
    """
    Arguments:
        pair: str, e.g = 'tETHUSD'
    """
    def __init__(self, pair):
        self.pair = pair


class Market:
    """
    Market is a type for Market objects which represent a list of PairMarketValue
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
