from absortium import constants
from absortium.celery import tasks
from freezegun import freeze_time

from core.utils.logging import getLogger
from absortium.tests.base import AbsoritumUnitTest

__author__ = "andrew.shvv@gmail.com"

logger = getLogger(__name__)


class MarketInfoTest(AbsoritumUnitTest):
    def setUp(self):
        super().setUp()
        self.publishments_flush()

    def test_without_data(self):
        tasks.calculate_market_info.delay()
        last_info_btc_eth = self.get_market_info()

        self.assertEqual(self.to_dec(last_info_btc_eth["rate"]), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["volume_24h"]), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_max"]), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_min"]), 0.0)

    def test_market_info_changes(self, *args, **kwargs):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        # I want to buy ethereum == sell bitcoin, with price for 1 ETH = 0.5 BTC. total - amount of bitcoins I want to sell.
        self.create_order(order_type=constants.ORDER_BUY, total="1.0", price="0.5", status="init")

        # I want to sell ethereum == buy bitcoin, with price for 1 ETH = 0.5 BTC. total - amount of bitcoins I want to buy.
        self.create_order(order_type=constants.ORDER_SELL, total="1.0", price="0.5", status="completed")

        tasks.calculate_market_info.delay()
        last_info = self.get_market_info()

        self.assertEqual(self.to_dec(last_info["rate"]), 0.5)
        self.assertEqual(self.to_dec(last_info["volume_24h"]), 2.0)
        self.assertEqual(self.to_dec(last_info["rate_24h_max"]), 0.5)
        self.assertEqual(self.to_dec(last_info["rate_24h_min"]), 0.5)

        # Create second order and check market info changes
        self.create_order(order_type=constants.ORDER_BUY, total="1.0", price="1.0", status="init")
        self.create_order(order_type=constants.ORDER_SELL, total="1.0", price="1.0", status="completed")

        tasks.calculate_market_info.delay()
        last_info = self.get_market_info()

        self.assertEqual(self.to_dec(last_info["rate"]), 0.75)
        self.assertEqual(self.to_dec(last_info["volume_24h"]), 4.0)
        self.assertEqual(self.to_dec(last_info["rate_24h_max"]), 1.0)
        self.assertEqual(self.to_dec(last_info["rate_24h_min"]), 0.5)

    def test_not_expired(self):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        with freeze_time("2012-01-14 00:00:00"):
            self.create_order(order_type=constants.ORDER_BUY, total="1.0", price="1.0", status="init")
            self.create_order(order_type=constants.ORDER_SELL, total="1.0", price="1.0", status="completed")
            tasks.calculate_market_info.delay()

        with freeze_time("2012-01-15 00:00:00"):
            self.create_order(order_type=constants.ORDER_BUY, total="1.0", price="2.0", status="init")
            self.create_order(order_type=constants.ORDER_SELL, total="1.0", price="2.0", status="completed")
            tasks.calculate_market_info.delay()

            last_info_btc_eth = self.get_market_info()

            self.assertEqual(self.to_dec(last_info_btc_eth["volume_24h"]), 4.0)
            self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_max"]), 2.0)
            self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_min"]), 1.0)

    def test_expired(self):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        with freeze_time("2012-01-14 00:00:00"):
            self.create_order(order_type=constants.ORDER_BUY, total="1.0", price="1.0", status="init")
            self.create_order(order_type=constants.ORDER_SELL, total="1.0", price="1.0", status="completed")
            tasks.calculate_market_info.delay()

        with freeze_time("2012-01-15 00:00:01"):
            self.create_order(order_type=constants.ORDER_BUY, total="1.0", price="2.0", status="init")
            self.create_order(order_type=constants.ORDER_SELL, total="1.0", price="2.0", status="completed")
            tasks.calculate_market_info.delay()

            last_info_btc_eth = self.get_market_info()

            self.assertEqual(self.to_dec(last_info_btc_eth["volume_24h"]), 2.0)
            self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_max"]), 2.0)
            self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_min"]), 2.0)

    def test_price_when_order_expired(self):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        with freeze_time("2012-01-14 00:00:00"):
            self.create_order(order_type=constants.ORDER_BUY, total="1.0", price="1.0", status="init")
            self.create_order(order_type=constants.ORDER_SELL, total="1.0", price="1.0", status="completed")

        with freeze_time("2012-01-16 00:00:00"):
            tasks.calculate_market_info.delay()
            last_info = self.get_market_info()
            self.assertEqual(self.to_dec(last_info["rate"]), 1.0)

    def test_notification(self):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        self.create_order(order_type=constants.ORDER_BUY, total="1.0", price="1.0", status="init")
        self.create_order(order_type=constants.ORDER_SELL, total="1.0", price="1.0", status="completed")
        tasks.calculate_market_info.delay()

        publishments = self.get_publishments(constants.TOPIC_MARKET_INFO)
        self.assertEqual(len(publishments), 1)
        p = publishments[0]

        self.assertEqual(self.to_dec(p["rate"]), 1.0)
        self.assertEqual(self.to_dec(p["volume_24h"]), 2.0)
        self.assertEqual(self.to_dec(p["rate_24h_max"]), 1.0)
        self.assertEqual(self.to_dec(p["rate_24h_min"]), 1.0)

