__author__ = "andrew.shvv@gmail.com"

from freezegun import freeze_time

from absortium import constants
from absortium.celery import tasks
from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class MarketInfoTest(AbsoritumUnitTest):
    def setUp(self):
        super().setUp()
        self.pubsliments_flush()

    def count_of_pairs(self):
        currencies = constants.AVAILABLE_CURRENCIES.values()
        return len([(fc, tc) for fc in currencies for tc in currencies if fc != tc])

    def test_without_data(self):
        tasks.calculate_market_info.delay()
        last_info_btc_eth = self.get_market_info("btc", "eth")
        last_info_eth_btc = self.get_market_info("eth", "btc")

        self.assertEqual(self.to_dec(last_info_btc_eth["rate"]), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["volume_24h"]), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_max"]), 0.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_min"]), 0.0)

        self.assertEqual(self.to_dec(last_info_eth_btc["rate"]), 0.0)
        self.assertEqual(self.to_dec(last_info_eth_btc["volume_24h"]), 0.0)
        self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_max"]), 0.0)
        self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_min"]), 0.0)

    def test_without_specifying_currency(self):
        tasks.calculate_market_info.delay()
        all_info = self.get_market_info(debug=True)
        self.assertEqual(len(all_info), 2)

    def test_market_info_changes(self, *args, **kwargs):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        # Create first exchange and check info
        self.create_exchange(amount="1.0", price="2.0", status="init")
        self.check_offer(amount="1.0", price="2.0")

        self.create_exchange(amount="2.0", price="0.5", status="completed",
                             from_currency="eth",
                             to_currency="btc")

        tasks.calculate_market_info.delay()
        last_info_btc_eth = self.get_market_info("btc", "eth")
        last_info_eth_btc = self.get_market_info("eth", "btc")

        self.assertEqual(self.to_dec(last_info_btc_eth["rate"]), 2.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["volume_24h"]), 1.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_max"]), 2.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_min"]), 2.0)

        self.assertEqual(self.to_dec(last_info_eth_btc["rate"]), 0.5)
        self.assertEqual(self.to_dec(last_info_eth_btc["volume_24h"]), 2.0)
        self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_max"]), 0.5)
        self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_min"]), 0.5)

        # Create second exchange and check market info changes
        self.create_exchange(amount="1.0", price="1.0", status="init")
        self.check_offer(amount="1.0", price="1.0")

        self.create_exchange(amount="1.0", price="1.0", status="completed",
                             from_currency="eth",
                             to_currency="btc")

        tasks.calculate_market_info.delay()
        last_info_btc_eth = self.get_market_info("btc", "eth")
        last_info_eth_btc = self.get_market_info("eth", "btc")

        self.assertEqual(self.to_dec(last_info_btc_eth["rate"]), 1.5)
        self.assertEqual(self.to_dec(last_info_btc_eth["volume_24h"]), 2.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_max"]), 2.0)
        self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_min"]), 1.0)

        self.assertEqual(self.to_dec(last_info_eth_btc["rate"]), 0.75)
        self.assertEqual(self.to_dec(last_info_eth_btc["volume_24h"]), 3.0)
        self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_max"]), 1.0)
        self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_min"]), 0.5)

    def test_expired(self):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        with freeze_time("2012-01-14 00:00:00"):
            self.create_exchange(amount="1.0", price="1.0", status="init")
            self.check_offer(amount="1.0", price="1.0")

            self.create_exchange(amount="1.0", price="1.0", status="completed",
                                 from_currency="eth",
                                 to_currency="btc")
            tasks.calculate_market_info.delay()

        with freeze_time("2012-01-15 00:00:00"):
            self.create_exchange(amount="1.0", price="2.0", status="init")
            self.check_offer(amount="1.0", price="2.0")

            self.create_exchange(amount="2.0", price="0.5", status="completed",
                                 from_currency="eth",
                                 to_currency="btc")

            tasks.calculate_market_info.delay()

            last_info_btc_eth = self.get_market_info("btc", "eth")
            last_info_eth_btc = self.get_market_info("eth", "btc")

            self.assertEqual(self.to_dec(last_info_btc_eth["volume_24h"]), 1.0)
            self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_max"]), 2.0)
            self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_min"]), 2.0)

            self.assertEqual(self.to_dec(last_info_eth_btc["volume_24h"]), 2.0)
            self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_max"]), 0.5)
            self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_min"]), 0.5)

    def test_second_before_expired(self):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        with freeze_time("2012-01-14 00:00:00"):
            self.create_exchange(amount="1.0", price="1.0", status="init")
            self.check_offer(amount="1.0", price="1.0")

            self.create_exchange(amount="1.0", price="1.0", status="completed",
                                 from_currency="eth",
                                 to_currency="btc")
            tasks.calculate_market_info.delay()

        with freeze_time("2012-01-14 23:59:59"):
            self.create_exchange(amount="1.0", price="2.0", status="init")
            self.check_offer(amount="1.0", price="2.0")

            self.create_exchange(amount="2.0", price="0.5", status="completed",
                                 from_currency="eth",
                                 to_currency="btc")

            tasks.calculate_market_info.delay()
            last_info_btc_eth = self.get_market_info("btc", "eth")
            last_info_eth_btc = self.get_market_info("eth", "btc")

            self.assertEqual(self.to_dec(last_info_btc_eth["volume_24h"]), 2.0)
            self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_max"]), 2.0)
            self.assertEqual(self.to_dec(last_info_btc_eth["rate_24h_min"]), 1.0)

            self.assertEqual(self.to_dec(last_info_eth_btc["volume_24h"]), 3.0)
            self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_max"]), 1.0)
            self.assertEqual(self.to_dec(last_info_eth_btc["rate_24h_min"]), 0.5)

    def test_price_when_exchange_expired(self):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        with freeze_time("2012-01-14 00:00:00"):
            self.create_exchange(amount="1.0", price="1.0", status="init")
            self.check_offer(amount="1.0", price="1.0")

            self.create_exchange(amount="1.0", price="1.0", status="completed",
                                 from_currency="eth",
                                 to_currency="btc")

        with freeze_time("2012-01-16 00:00:00"):
            tasks.calculate_market_info.delay()
            last_info_btc_eth = self.get_market_info("btc", "eth")
            last_info_eth_btc = self.get_market_info("eth", "btc")

            self.assertEqual(self.to_dec(last_info_btc_eth["rate"]), 1.0)
            self.assertEqual(self.to_dec(last_info_eth_btc["rate"]), 1.0)

    def test_notification(self):
        self.make_deposit(self.get_account("btc"), amount="999999.0")
        self.make_deposit(self.get_account("eth"), amount="999999.0")

        self.create_exchange(amount="1.0", price="2.0", status="init")
        self.check_offer(amount="1.0", price="2.0")

        self.create_exchange(amount="2.0", price="0.5", status="completed",
                             from_currency="eth",
                             to_currency="btc")

        tasks.calculate_market_info.delay()

        publishments = self.get_publishments(constants.TOPIC_MARKET_INFO)
        self.assertEqual(len(publishments), 2)

        for p in publishments:
            if p["from_currency"] == "btc":
                self.assertEqual(self.to_dec(p["rate"]), 2.0)
                self.assertEqual(self.to_dec(p["volume_24h"]), 1.0)
                self.assertEqual(self.to_dec(p["rate_24h_max"]), 2.0)
                self.assertEqual(self.to_dec(p["rate_24h_min"]), 2.0)
            elif p["from_currency"] == "eth":
                self.assertEqual(self.to_dec(p["rate"]), 0.5)
                self.assertEqual(self.to_dec(p["volume_24h"]), 2.0)
                self.assertEqual(self.to_dec(p["rate_24h_max"]), 0.5)
                self.assertEqual(self.to_dec(p["rate_24h_min"]), 0.5)
            else:
                raise Exception("Bad currency {}".format(p["from_currency"]))
