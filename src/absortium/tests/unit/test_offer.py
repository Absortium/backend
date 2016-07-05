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

    def random_amount(self):
        amount = -1

        while amount < constants.DEPOSIT_AMOUNT_MIN_VALUE:
            amount = decimal.Decimal('%d.%d' % (random.randint(0, self.before_dot), random.randint(0, self.after_dot)))
        return amount

    def test_calculation_accuracy(self, *args, **kwargs):
        account = self.get_account('btc')
        n = 20
        amounts = [self.random_amount() for _ in range(0, n)]

        should_be = 0
        for amount in amounts:
            should_be += amount

            self.make_deposit(account, amount=amount)
            self.check_account_amount(account=account, amount=amount)
            self.create_exchange(amount=str(amount), price="0.1", status="init")
            self.check_offer(amount=should_be, price="0.1")

    def test_different_price(self, *args, **kwargs):
        self.make_deposit(self.get_account('btc'), amount="999999.0")

        self.create_exchange(amount="1.0", price="1", status="init")
        self.create_exchange(amount="1.0", price="2", status="init")

        self.check_offer(amount="1.0", price="1.0")
        self.check_offer(amount="1.0", price="2.0")

    def test_offer_deletion(self, *args, **kwargs):
        self.make_deposit(self.get_account('btc'), amount="999999.0")
        self.make_deposit(self.get_account('eth'), amount="999999.0")
        self.create_exchange(amount="1.0", price="1.0", status="init")
        self.check_offer(amount="1.0", price="1.0")

        # Create some another user
        User = get_user_model()
        some_user = User(username="some_user")
        some_user.save()

        self.client.force_authenticate(some_user)
        self.make_deposit(self.get_account('btc'), amount="999999.0")
        self.make_deposit(self.get_account('eth'), amount="999999.0")

        self.create_exchange(from_currency="eth", to_currency="btc", amount="1.0", price="3.0", status="init")
        self.check_offer(from_currency="eth", to_currency="btc", amount="1.0", price="3.0")

        self.create_exchange(from_currency="eth", to_currency="btc", amount="1.0", price="1.0", status="completed")
        self.check_offer(amount="1.0", price="1.0", should_exist=False)

    def test_offer_deletion_complex(self, *args, **kwargs):
        self.make_deposit(self.get_account('btc'), amount="999999.0")
        self.make_deposit(self.get_account('eth'), amount="999999.0")

        self.create_exchange(amount="1.0", price="2.0", status="init")
        self.create_exchange(amount="1.0", price="2.0", status="init")
        self.create_exchange(amount="1.0", price="2.0", status="init")

        self.check_offer(amount="3.0", price="2.0")

        # Create some another user
        User = get_user_model()
        some_user = User(username="some_user")
        some_user.save()

        self.client.force_authenticate(some_user)
        self.make_deposit(self.get_account('btc'), amount="999999.0")
        self.make_deposit(self.get_account('eth'), amount="999999.0")

        self.create_exchange(from_currency="eth", to_currency="btc", amount="2.0", price="0.5", status="completed")
        self.create_exchange(from_currency="eth", to_currency="btc", amount="2.0", price="0.5", status="completed")
        self.create_exchange(from_currency="eth", to_currency="btc", amount="1.0", price="0.5", status="completed")

        self.check_offer(amount="0.5", price="2.0")

        self.create_exchange(from_currency="eth", to_currency="btc", amount="1.0", price="0.5", status="completed")

        self.check_offer(amount="0.5", price="2.0", should_exist=False)

    def test_with_two_exchanges_with_diff_price(self):
        """
            Create create two exchanges with different price and then one opposite with smaller price
            and check that offers are not exist
        """

        self.make_deposit(self.get_account('btc'), amount="10.0")

        self.create_exchange(price="2.0", amount="5.0", status="init")
        self.create_exchange(price="1.0", amount="5.0", status="init")
        self.check_account_amount(self.get_account('btc'), amount="0.0")
        self.check_account_amount(self.get_account('eth'), amount="0.0")

        # Create some another user
        User = get_user_model()
        some_user = User(username="some_user")
        some_user.save()
        self.client.force_authenticate(some_user)
        self.make_deposit(self.get_account('eth'), amount="20.0")

        self.create_exchange(from_currency="eth", to_currency="btc", price="0.5", amount="15.0", status="completed")
        self.check_account_amount(self.get_account('eth'), amount="5.0")
        self.check_account_amount(self.get_account('btc'), amount="10.0")

        self.client.force_authenticate(self.user)
        self.check_account_amount(self.get_account('btc'), amount="0.0")
        self.check_account_amount(self.get_account('eth'), amount="15.0")

        self.check_offers_empty()

    def test_poloniex_update(self):
        """
            For example Poloniex Sync service subscribed on topic BTC_ETH.
            When we receive update with order_type="newTrade" and offer_type="buy" it means
            that someone create ETH buy order. == BTC-> ETH exchange.
        """
        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_CREATED,
                                                             offer_type="buy",
                                                             price="1",
                                                             amount="1"))
        self.check_offer(price="1",
                         amount="1",
                         system="poloniex")

    def test_poloniex_two_updates(self):
        """
            For example Poloniex Sync service subscribed on topic BTC_ETH.
            When we receive update with order_type="newTrade" and offer_type="buy" it means
            that someone create ETH buy order. == BTC-> ETH exchange.
        """
        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_CREATED,
                                                             offer_type="buy",
                                                             price="1",
                                                             amount="1"))

        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_MODIFIED,
                                                             offer_type="ask",
                                                             price="1",
                                                             amount="2"))

        self.check_offer(price="1",
                         amount="2",
                         system="poloniex")

    def test_poloniex_offer_remove(self):
        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_CREATED,
                                                             offer_type="buy",
                                                             price="1",
                                                             amount="1"))

        self.check_offer(price="1",
                         amount="1",
                         system="poloniex")

        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_REMOVED,
                                                             offer_type="buy",
                                                             price="1"))

        self.check_offer(price="1",
                         amount="2",
                         system="poloniex",
                         should_exist=False)

    def test_poloniex_offer_remove_without_creating(self):
        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_REMOVED,
                                                             offer_type="buy",
                                                             price="1"))

        self.check_offer(price="1",
                         amount="2",
                         system="poloniex",
                         should_exist=False)

    def test_poloniex_notification(self):
        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_CREATED,
                                                             offer_type="buy",
                                                             price="1",
                                                             amount="1"))
        self.assertEqual(len(self.get_publishments("offers_btc_eth")), 1)

    def test_usual_notification(self):
        self.make_deposit(self.get_account('btc'), amount="1.0")
        self.create_exchange(price="1.0", amount="1.0", status="init")
        self.assertEqual(len(self.get_publishments("offers_btc_eth")), 1)

    def test_notification_offer_amount_accumulation(self):
        """
            Create offers from different system and check that amount from different offers are accumulated into one.
        """
        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_CREATED,
                                                             offer_type="buy",
                                                             price="1",
                                                             amount="1"))

        self.make_deposit(self.get_account('btc'), amount="1.0")
        self.create_exchange(price="1.0", amount="1.0", status="init")

        publishments = self.get_publishments("offers_btc_eth")

        self.assertEqual(len(publishments), 2)
        self.assertEqual(decimal.Decimal(publishments[1]['amount']), 2)

    def test_poloniex_offer_sync(self):
        PoloniexApp.updates_handler(**create_poloniex_update(order_type=constants.POLONIEX_OFFER_CREATED,
                                                             offer_type="buy",
                                                             price="1",
                                                             amount="1"))

        order_book_data = create_order_book(
            asks=[
                ["1", "2"]
            ],
            bids=[
                ["1", "1"]
            ],
        )
        PoloniexApp.synchronize_offers(order_book_data)

        self.check_offer(price="1",
                         amount="2",
                         system="poloniex")

    def test_malformed(self):
        malformed_from_currency = "asdasd907867t67g"
        with self.assertRaises(AssertionError):
            self.check_offer(from_currency=malformed_from_currency, amount="1.0", price="2.0")

        malformed_to_currency = "asdasd907867t67g"
        with self.assertRaises(AssertionError):
            self.check_offer(to_currency=malformed_to_currency, amount="1.0", price="2.0")
