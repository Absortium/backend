__author__ = 'andrew.shvv@gmail.com'

from absortium import constants
from absortium.celery import tasks
from absortium.model.models import MarketInfo
from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class MarketInfoTest(AbsoritumUnitTest):
    before_dot = 10 ** (constants.MAX_DIGITS - constants.DECIMAL_PLACES) - 1
    after_dot = 10 ** constants.DECIMAL_PLACES - 1

    def count_of_pairs(self):
        currencies = constants.AVAILABLE_CURRENCIES.values()
        return len([(fc, tc) for fc in currencies for tc in currencies if fc != tc])

    def test_without_data(self):
        tasks.calculate_market_info.delay()
        last_info_btc_eth = self.get_market_info("btc", "eth")
        last_info_eth_btc = self.get_market_info("eth", "btc")

        self.assertEqual(self.to_dec(last_info_btc_eth['rate']), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth['volume_24h']), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth['rate_24h_max']), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth['rate_24h_min']), 0.0)

        self.assertEqual(self.to_dec(last_info_eth_btc['rate']), 0.0)
        self.assertEqual(self.to_dec(last_info_eth_btc['volume_24h']), 0.0)
        self.assertEqual(self.to_dec(last_info_eth_btc['rate_24h_max']), 0.0)
        self.assertEqual(self.to_dec(last_info_eth_btc['rate_24h_min']), 0.0)

    def test_market_info_changes(self, *args, **kwargs):
        self.make_deposit(self.get_account('btc'), amount="999999.0")
        self.make_deposit(self.get_account('eth'), amount="999999.0")

        # Create first exchange and check info
        self.create_exchange(amount="1.0", price="2.0", status="init")
        self.check_offer(amount="1.0", price="2.0")

        self.create_exchange(amount="2.0", price="0.5", status="completed",
                             from_currency="eth",
                             to_currency="btc")

        tasks.calculate_market_info.delay()
        last_info_btc_eth = self.get_market_info("btc", "eth")
        last_info_eth_btc = self.get_market_info("eth", "btc")

        self.assertEqual(self.to_dec(last_info_btc_eth['rate']), 2.0)
        self.assertEqual(self.to_dec(last_info_btc_eth['volume_24h']), 1.0)
        self.assertEqual(self.to_dec(last_info_btc_eth['rate_24h_max']), 2.0)
        self.assertEqual(self.to_dec(last_info_btc_eth['rate_24h_min']), 2.0)

        self.assertEqual(self.to_dec(last_info_eth_btc['rate']), 0.5)
        self.assertEqual(self.to_dec(last_info_eth_btc['volume_24h']), 2.0)
        self.assertEqual(self.to_dec(last_info_eth_btc['rate_24h_max']), 0.5)
        self.assertEqual(self.to_dec(last_info_eth_btc['rate_24h_min']), 0.5)

        # Create second exchange and check market info changes
        self.create_exchange(amount="1.0", price="1.0", status="init")
        self.check_offer(amount="1.0", price="1.0")

        self.create_exchange(amount="1.0", price="1.0", status="completed",
                             from_currency="eth",
                             to_currency="btc")

        tasks.calculate_market_info.delay()
        last_info_btc_eth = self.get_market_info("btc", "eth")
        last_info_eth_btc = self.get_market_info("eth", "btc")

        self.assertEqual(self.to_dec(last_info_btc_eth['rate']), 1.5)
        self.assertEqual(self.to_dec(last_info_btc_eth['volume_24h']), 2.0)
        self.assertEqual(self.to_dec(last_info_btc_eth['rate_24h_max']), 2.0)
        self.assertEqual(self.to_dec(last_info_btc_eth['rate_24h_min']), 1.0)

        self.assertEqual(self.to_dec(last_info_eth_btc['rate']), 0.75)
        self.assertEqual(self.to_dec(last_info_eth_btc['volume_24h']), 3.0)
        self.assertEqual(self.to_dec(last_info_eth_btc['rate_24h_max']), 1.0)
        self.assertEqual(self.to_dec(last_info_eth_btc['rate_24h_min']), 0.5)

    def test_old_exchanges(self):
        pass

    # def







        # def test_offer_deletion_complex(self, *args, **kwargs):
        #     self.make_deposit(self.get_account('btc'), amount="999999.0")
        #     self.make_deposit(self.get_account('eth'), amount="999999.0")
        #
        #     self.create_exchange(amount="1.0", price="2.0", status="init")
        #     self.create_exchange(amount="1.0", price="2.0", status="init")
        #     self.create_exchange(amount="1.0", price="2.0", status="init")
        #
        #     self.check_offer(amount="3.0", price="2.0")
        #
        #     # Create some another user
        #     User = get_user_model()
        #     some_user = User(username="some_user")
        #     some_user.save()
        #
        #     self.client.force_authenticate(some_user)
        #     self.make_deposit(self.get_account('btc'), amount="999999.0")
        #     self.make_deposit(self.get_account('eth'), amount="999999.0")
        #
        #     self.create_exchange(from_currency="eth", to_currency="btc", amount="2.0", price="0.5", status="completed")
        #     self.create_exchange(from_currency="eth", to_currency="btc", amount="2.0", price="0.5", status="completed")
        #     self.create_exchange(from_currency="eth", to_currency="btc", amount="1.0", price="0.5", status="completed")
        #
        #     self.check_offer(amount="0.5", price="2.0")
        #
        #     self.create_exchange(from_currency="eth", to_currency="btc", amount="1.0", price="0.5", status="completed")
        #
        #     self.check_offer(amount="0.5", price="2.0", should_exist=False)
