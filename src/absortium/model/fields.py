__author__ = 'andrew.shvv@gmail.com'

from django.db import models

class BTCAddressField(models.Field):

    description = "A hand of cards (bridge style)"

    def get_address(self):
        return

    def __init__(self, *args, **kwargs):

        kwargs['address'] = 104
        super(BTCAddressField, self).__init__(*args, **kwargs)