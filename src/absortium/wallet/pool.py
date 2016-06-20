from absortium.model.models import Account
from absortium.wallet.base import get_wallet_client

__author__ = 'andrew.shvv@gmail.com'


class AccountPool():
    def __init__(self, currency):
        self.currency = currency
        self.client = get_wallet_client(currency=currency)

    def __len__(self):
        return len(Account.objects.filter(currency=self.currency, owner__isnull=True))

    def assign_account(self, user_pk):
        try:
            account = Account.objects.filter(currency=self.currency, owner__isnull=True)[0]
            account.update(owner_id=user_pk)
            return account

        except IndexError:
            account = self.create_account()
            account.owner_id = user_pk
            account.save()
            return account

    def create_account(self):
        account = Account(address=self.client.create_address(),
                          currency=self.currency)
        account.save()
        return account
