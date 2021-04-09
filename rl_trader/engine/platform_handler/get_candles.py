from bfxapi import Client
import asyncio


def get_candles(
        start_time, end_time,
        pair='tETHUSD', time_frame='1m'
):
    """
    Attributes:
        start_time: int
        end_time: int
        pair: str
        time_frame: str = corresponds to candlestick time frame : 1m, 5m, 1h, 1d...
    """
    bfx = Client(logLevel='DEBUG')

    async def log_historical_candles():
        return await bfx.rest.get_public_candles(
            pair,
            start_time,
            end_time,
            limit=1440,
            tf=time_frame
        )

    async def run():
        return await log_historical_candles()

    t = asyncio.ensure_future(run())
    candles = asyncio.get_event_loop().run_until_complete(t)

    return candles
