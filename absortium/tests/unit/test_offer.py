import decimal
import random

from django.contrib.auth import get_user_model

from absortium import constants
from absortium.poloniexsync import PoloniexApp
from absortium.tests.base import AbsoritumUnitTest
from absortium.tests.data.poloniex import create_poloniex_update, create_order_book
from core.utils.logging import getLogger

__author__ = 'andrew.shvv@gmail.com'

logger = getLogger(__name__)


class OfferTest(AbsoritumUnitTest):
    before_dot = 10 ** (constants.MAX_DIGITS - constants.DECIMAL_PLACES) - 1
    after_dot = 10 ** constants.DECIMAL_PLACES - 1

    def setUp(self):
        super().setUp()
        self.publishments_flush()

        self.make_deposit(self.get_account('btc'), amount="999999.0")
        self.make_deposit(self.get_account('eth'), amount="999999.0")

        User = get_user_model()
        self.some_user = User(username="some_user")
        self.some_user.save()

        self.make_deposit(self.get_account('btc', self.some_user), amount="999999.0")
        self.make_deposit(self.get_account('eth', self.some_user), amount="999999.0")

        self.client.force_authenticate(self.user)

    def random_amount(self):
        amount = -1

        while amount < constants.DEPOSIT_AMOUNT_MIN_VALUE:
            amount = decimal.Decimal('%d.%d' % (random.randint(0, self.before_dot), random.randint(0, self.after_dot)))
        return amount

    def test_simple(self, *args, **kwargs):
        self.create_order(order_type=constants.ORDER_BUY, amount="2", price="1", status=constants.ORDER_INIT)
        self.check_offer(amount="2", price="1")

    def test_multiple(self, *args, **kwargs):
        self.create_order(order_type=constants.ORDER_BUY, amount="1", price="1", status=constants.ORDER_INIT)
        self.create_order(order_type=constants.ORDER_BUY, amount="1", price="1", status=constants.ORDER_INIT)

        self.check_offer(amount="2", price="1")

    def test_calculation_accuracy(self, *args, **kwargs):
        User = get_user_model()
        another_user = User(username="another_user")
        another_user.save()
        self.client.force_authenticate(another_user)

        n = 20
        amounts = [self.random_amount() for _ in range(0, n)]

        should_be = decimal.Decimal(0)
        for amount in amounts:
            should_be += amount

            self.make_deposit(self.get_account('btc'), amount=amount)
            self.create_order(amount=str(amount), price="1", status=constants.ORDER_INIT)
            self.check_offer(amount=should_be, price="1")

    def test_different_price(self, *args, **kwargs):
        self.create_order(amount="1.0", price="1", status=constants.ORDER_INIT)
        self.create_order(amount="1.0", price="2", status=constants.ORDER_INIT)

        self.check_offer(amount="1.0", price="1.0")
        self.check_offer(amount="1.0", price="2.0")

    def test_offer_deletion(self, *args, **kwargs):
        self.create_order(amount="1.0", price="1.0", status=constants.ORDER_INIT)
        self.check_offer(amount="1.0", price="1.0")

        self.client.force_authenticate(self.some_user)

        self.create_order(order_type=constants.ORDER_SELL, amount="1.0", price="3.0", status=constants.ORDER_INIT)
        self.check_offer(order_type=constants.ORDER_SELL, amount="1.0", price="3.0")

        self.create_order(order_type=constants.ORDER_SELL, amount="1.0", price="1.0", status="completed")
        self.check_offer(amount="1.0", price="1.0", should_exist=False)

    def test_offer_deletion_complex(self, *args, **kwargs):

        self.create_order(order_type=constants.ORDER_BUY, amount="1.0", price="1.0", status=constants.ORDER_INIT)
        self.create_order(order_type=constants.ORDER_BUY, amount="1.0", price="1.0", status=constants.ORDER_INIT)
        self.create_order(order_type=constants.ORDER_BUY, amount="1.0", price="1.0", status=constants.ORDER_INIT)
        self.check_offer(order_type=constants.ORDER_BUY, amount="3.0", price="1.0")

        self.client.force_authenticate(self.some_user)

        self.create_order(order_type=constants.ORDER_SELL, amount="1.0", price="1")
        self.create_order(order_type=constants.ORDER_SELL, amount="1.0", price="1")
        self.check_offer(order_type=constants.ORDER_BUY, amount="1.0", price="1.0")
        self.create_order(order_type=constants.ORDER_SELL, amount="1.0", price="1.0")
        self.check_offers_empty()

    def test_creation_notification(self):
        self.create_order(order_type=constants.ORDER_SELL, status=constants.ORDER_INIT)
        self.create_order(order_type=constants.ORDER_SELL, status=constants.ORDER_INIT)

        self.assertEqual(len(self.get_publishments("offers_btc_eth_sell")), 2)

    def test_creation_and_deletion_notification(self):
        self.create_order(user=self.some_user, order_type=constants.ORDER_SELL, status=constants.ORDER_INIT)
        self.create_order(user=self.user, order_type=constants.ORDER_BUY, status=constants.ORDER_COMPLETED)

        self.assertEqual(len(self.get_publishments("offers_btc_eth_sell")), 2)
        self.assertEqual(len(self.get_publishments("offers_btc_eth_buy")), 2)

    def test_update_order(self):
        order = self.create_order(order_type=constants.ORDER_SELL, amount="1.0", price="1.0",
                                  status=constants.ORDER_INIT)
        self.update_order(pk=order['pk'], amount="2.0")

    def test_cancel_order(self):
        order = self.create_order(order_type=constants.ORDER_SELL, status=constants.ORDER_INIT)
        self.cancel_order(order['pk'])
        self.check_offers_empty()

    def test_poloniex_update(self):
        """
            For example Poloniex Sync service subscribed on topic PAIR_BTC_ETH.
            When we receive update with order_type="newTrade" and offer_type="buy" it means
            that someone create ETH buy order. == BTC-> ETH order.
        """
        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             order_type="bid",
                                                             price="1",
                                                             amount="1"))
        self.check_offer(order_type=constants.ORDER_BUY, price="1", amount="1")

    def test_poloniex_two_updates(self):
        """
            For example Poloniex Sync service subscribed on topic PAIR_BTC_ETH.
            When we receive update with order_type="newTrade" and offer_type="buy" it means
            that someone create ETH buy order. == BTC-> ETH order.
        """
        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             order_type="bid",
                                                             price="1",
                                                             amount="1"))

        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             order_type="bid",
                                                             price="1",
                                                             amount="2"))

        self.check_offer(order_type=constants.ORDER_BUY, price="1", amount="2")

    def test_poloniex_offer_remove(self):
        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             order_type="bid",
                                                             price="1",
                                                             amount="1"))

        self.check_offer(order_type=constants.ORDER_BUY, price="1", amount="1")

        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_REMOVED,
                                                             order_type="bid",
                                                             price="1"))

        self.check_offers_empty()

    def test_poloniex_offer_remove_without_creating(self):
        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_REMOVED,
                                                             order_type="bid",
                                                             price="1"))

        self.check_offers_empty()

    def test_poloniex_notification(self):
        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             order_type="ask",
                                                             price="1",
                                                             amount="1"))
        self.assertEqual(len(self.get_publishments("offers_btc_eth_sell")), 1)

    def test_notification_offer_amount_accumulation(self):
        """
            Create offers from different system and check that amount from different offers are accumulated into one.
        """
        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             order_type="bid",
                                                             price="1",
                                                             amount="1"))

        self.make_deposit(self.get_account('btc'), amount="1.0")
        self.create_order(order_type=constants.ORDER_BUY, price="1.0", amount="1.0", status=constants.ORDER_INIT)

        publishments = self.get_publishments("offers_btc_eth_buy")

        self.assertEqual(len(publishments), 2)
        self.assertEqual(decimal.Decimal(publishments[1]['amount']), 2)

    def test_poloniex_offer_sync(self):
        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             order_type="bid",
                                                             price="1",
                                                             amount="1"))

        order_book_data = create_order_book(
            asks=[
                ["1", "1"]
            ],
            bids=[
                ["1", "2"]
            ],
        )
        PoloniexApp.synchronize_offers(order_book_data)

        self.check_offer(order_type=constants.ORDER_BUY, price="1", amount="2")

    def test_offer_sum(self):
        PoloniexApp.updates_handler(**create_poloniex_update(update_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             order_type="bid",
                                                             price="1",
                                                             amount="1"))

        self.make_deposit(self.get_account('btc'), amount="1.0")
        self.create_order(price="1.0", amount="1.0", status=constants.ORDER_INIT)

        self.check_offer(price="1", amount="2")

    def test_malformed_pair(self):
        malformed_pair = "asdasd907867t67g"
        with self.assertRaises(AssertionError):
            self.check_offer(pair=malformed_pair)

    def test_malformed_type(self):
        malformed_type = "asdasd907867t67g"
        with self.assertRaises(AssertionError):
            self.check_offer(order_type=malformed_type)
