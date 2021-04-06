from rl_trader.engine.rl_environment.account_api.fake_api import FakeAPI
from rl_trader.engine.rl_environment.account_api.platform_api import PlatformAPI


class Environment:
    def __init__(self,
                 pairs,
                 symbols,
                 env_mode='fake', fake_usd_start=20,
                 deployment_api=None):
        if env_mode == 'fake':
            self.training_api = FakeAPI(pairs, symbols, fake_usd_start=fake_usd_start)
            self.test_api = FakeAPI(pairs, symbols, fake_usd_start=fake_usd_start)
        elif env_mode == 'deploy':
            self.training_api = FakeAPI(symbols)
            self.test_api = PlatformAPI(deployment_api=deployment_api)

    def get_next_step(self):
        pass

    def _compute_rewards(self):
        pass
