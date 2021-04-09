from rl_trader.engine.data.context_datasets import get_context_ds

path = 'datasets'
pair = 'tETHUSD'
time_frame = '1m'
time_period = 1

context_ds, mean_std_ds = get_context_ds(
    pair=pair,
    time_period=1
)
print(context_ds.head())
print(mean_std_ds.head())
