__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED


class CreateAccountMixin():
    def create_account(self, user, currency, with_checks=False, with_authentication=True):
        if with_authentication:
            # Authenticate normal user
            self.client.force_authenticate(user)

        data = {
            'currency': currency
        }

        # Create account
        response = self.client.post('/api/accounts/', data=data, format='json')
        if with_checks:
            self.assertEqual(response.status_code, HTTP_201_CREATED)

        account_pk = response.json()['pk']
        return account_pk, response
