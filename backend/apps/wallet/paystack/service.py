import logging
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings
import hmac, hashlib
    

logger = logging.getLogger(__name__)

_TIMEOUT = (5, 30)

class PaystackError(Exception):
    """Raised when Paystack returns an error response."""

    def __init__(self, message: str, status_code: int = 0, raw: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.raw = raw or {}


class PaystackService:

    def __init__(self):
        self._base_paystack_url = settings.PAYSTACK_BASE_URL.rstrip("/")
        self._secret_key = settings.PAYSTACK_SECRET_KEY
        self._session = requests.Session()
        self._base_url = settings.BASE_URL.rstrip("/")
        self._paystack_channels = settings.PAYSTACK_CHANNELS
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._secret_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        return f"{self._base_paystack_url}/{path.lstrip('/')}"

    
    def _callback_url(self, reference: str):
        return f"{self._base_url}/api/v1/verify-deposit/?reference={reference.lstrip("/")}/"
        
    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """
        Parse and validate a Paystack response.
        Raises PaystackError on HTTP or business-logic failures.
        """
        try:
            data = response.json()
        except ValueError:
            raise PaystackError(
                f"Non-JSON response from Paystack (HTTP {response.status_code})",
                status_code=response.status_code,
            )

        if not response.ok:
            message = data.get("message", "Unknown Paystack error")
            logger.error(
                "Paystack API error | status=%s | message=%s | body=%s",
                response.status_code,
                message,
                data,
            )
            raise PaystackError(message, status_code=response.status_code, raw=data)

        if not data.get("status"):
            message = data.get("message", "Paystack returned status=false")
            raise PaystackError(message, raw=data)

        return data

    @staticmethod
    def _to_kobo(amount: Decimal) -> int:
        """Convert Naira (Decimal) to kobo (int) for Paystack."""
        return int(amount * 100)

    def _verify_signature(self, request: requests.Request):

        signature = request.headers.get("X-Paystack-Signature", "")
        expected = hmac.new(
            self._secret_key.encode('utf-8'),
            request.body,
            hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def initialize_deposit(self, amount, user, reference):
        amount_kobo = self._to_kobo(amount)

        payload = {
            "amount": amount_kobo,
            "email": user.email,
            'channels': self._paystack_channels,
            "currency": "NGN",
            "reference": reference,
            "callback_url": self._callback_url(reference)
        }

        try:
            response = self._session.post(
                self._url("/transaction/initialize"),
                json=payload,
                timeout=_TIMEOUT,
            )
        except requests.Timeout:
            raise PaystackError("Paystack request timed out while creating recipient")
        except requests.ConnectionError as exc:
            raise PaystackError(f"Network error contacting Paystack: {exc}")

        data = self._handle_response(response)
        return data

    def verify_deposit(self, reference):
        
        try:
            response = self._session.get(
                url=self._url(f"/transaction/verify/{reference}"),
                timeout=_TIMEOUT
            )

        except requests.Timeout:
            raise PaystackError("Paystack request timed out while creating recipient")
        except requests.ConnectionError as exc:
            raise PaystackError(f"Network error contacting Paystack: {exc}")
        
        data = self._handle_response(response)
        return data
    
    def ressolve_bank(self, account_number, bank_code):

        path = self._url(f"/bank/resolve?account_number={account_number}&bank_code={bank_code}")
        try:
            response = self._session.get(
                path, timeout=_TIMEOUT
            )
        except requests.Timeout:
            raise PaystackError("Paystack request timed out while ressolving bank account")
        except requests.ConnectionError as exc:
            raise PaystackError(f"Network error contacting Paystack: {exc}")
        
        data = self._handle_response(response)
        return data

    def create_transfer_recipient(
        self,
        account_name: str,
        account_number: str,
        bank_code: str,
        currency: str = "NGN",
        type: str = 'nuban'
    ) -> dict[str, Any]:
  
        payload = {
            "type": type,
            "name": account_name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": currency,
        }

        logger.info(
            "Creating Paystack transfer recipient account_number=%s | bank_code=%s",
            account_number,
            bank_code,
        )

        try:
            response = self._session.post(
                self._url("/transferrecipient"),
                json=payload,
                timeout=_TIMEOUT,
            )
        except requests.Timeout:
            raise PaystackError("Paystack request timed out while creating recipient", status_code=500)
        except requests.ConnectionError as exc:
            raise PaystackError(f"Network error contacting Paystack: {exc}", status_code=500)

        data = self._handle_response(response)
        return data

    def initiate_transfer(
        self,
        amount: Decimal,
        recipient_code: str,
        reference: str,
        reason: str = "Wallet withdrawal",
        currency: str = "NGN",
    ) -> dict[str, Any]:
        
        amount_kobo = self._to_kobo(amount)

        payload = {
            "source": "balance",
            "amount": amount_kobo,
            "recipient": recipient_code,
            "reference": reference,
            "reason": reason,
            "currency": currency,
        }

        logger.info(
            "Initiating Paystack transfer | reference=%s | amount_kobo=%s | recipient=%s",
            reference,
            amount_kobo,
            recipient_code,
        )

        try:
            response = self._session.post(
                self._url("/transfer"),
                json=payload,
                timeout=_TIMEOUT,
            )
        except requests.Timeout:
            raise PaystackError("Paystack request timed out while initiating transfer")
        except requests.ConnectionError as exc:
            raise PaystackError(f"Network error contacting Paystack: {exc}")

        data = self._handle_response(response)
        return data
