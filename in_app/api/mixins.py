import environ
from django.conf import settings
from twilio.rest import Client
import random


class MessageHandler:
    def __init__(self, phoneNumber, otp) -> None:
        self.phoneNumber = phoneNumber
        self.otp = otp

    def send_otp_to_a_phone(self):

        client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)

        message = client.messages.create(
            body=f'You\'re otp is {self.otp}',
            messaging_service_sid='MG89ee673dffa4021256a66b687092f4de',
            to=self.phoneNumber
        )
