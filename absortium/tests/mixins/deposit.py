from decimal import Decimal

__author__ = "andrew.shvv@gmail.com"

from django.conf import settings
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from absortium.model.models import Deposit
from absortium.tests.utils import create_btc_notification, create_eth_notification
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


class CreateDepositMixin():
    def make_deposit(self, account, amount="99999", with_checks=True, debug=False):
        if account["currency"] == "btc":
            data = create_btc_notification(account["address"], str(amount))
            url = "/notifications/{token}/".format(token=settings.BTC_NOTIFICATION_TOKEN)
        elif account["currency"] == "eth":
            data = create_eth_notification(account["address"], str(amount))
            url = "/notifications/{token}/".format(token=settings.ETH_NOTIFICATION_TOKEN)
        else:
            raise Exception("Unexpected currency")

        response = self.client.post(url, data=data, format="json")

        if debug:
            logger.info(response.content)

        self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_204_NO_CONTENT])

        if with_checks:
            deposit = response.json()

            # Check that deposit exist in db
            try:
                obj = Deposit.objects.get(pk=deposit["pk"])
            except Deposit.DoesNotExist:
                self.fail("Deposit object wasn't found in db")

            self.assertEqual(obj.owner_id, self.client.handler._force_user.pk)
            self.assertEqual(Decimal(deposit['amount']), Decimal(amount))
            self.assertEqual(deposit['currency'], account['currency'])

            return deposit
