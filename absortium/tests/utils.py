from absortium.utils import random_string

from absortium.tests.data.coinbase import payment_notification

__author__ = 'andrew.shvv@gmail.com'


def create_btc_notification(address, amount):
    payment_notification["data"]["address"] = address
    payment_notification["additional_data"]["amount"]["amount"] = amount

    return payment_notification


def create_eth_notification(address, amount):
    return {
        'amount': str(amount),
        'address': address,
        'tx_hash': random_string()
    }
