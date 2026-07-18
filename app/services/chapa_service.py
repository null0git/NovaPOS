"""
Chapa payment gateway integration.

Chapa (chapa.co) is an Ethiopian payment gateway. Flow:
  1. We POST to /v1/transaction/initialize with a unique tx_ref and amount,
     Chapa responds with a hosted checkout_url (and we can derive a QR from it).
  2. The customer completes payment on that page.
  3. Chapa calls our webhook (`/api/v1/payments/chapa/webhook`) to notify us,
     which we verify (signature) then confirm via /v1/transaction/verify/{tx_ref}
     before trusting the result.

Configure via environment variables:
  CHAPA_SECRET_KEY, CHAPA_BASE_URL (defaults to https://api.chapa.co),
  CHAPA_WEBHOOK_SECRET (used to verify the webhook signature).
"""
import hashlib
import hmac
import os
import uuid

import requests

from app.core.middleware.error_handler import AppError


class ChapaService:
    def __init__(self):
        self.secret_key = os.environ.get("CHAPA_SECRET_KEY", "")
        self.base_url = os.environ.get("CHAPA_BASE_URL", "https://api.chapa.co")
        self.webhook_secret = os.environ.get("CHAPA_WEBHOOK_SECRET", "")

    def _headers(self):
        return {"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/json"}

    def generate_tx_ref(self):
        return f"novapos-{uuid.uuid4().hex[:16]}"

    def initialize_session(self, sale, callback_url, return_url, customer_email=None, customer_name=None):
        """Create a Chapa hosted checkout session for `sale`. Returns (tx_ref, checkout_url)."""
        tx_ref = self.generate_tx_ref()

        if not self.secret_key:
            # No gateway configured (e.g. local/dev environment): return a
            # placeholder so the rest of the flow (QR generation, webhook
            # wiring) can still be exercised without live credentials.
            return tx_ref, f"{self.base_url}/checkout/placeholder/{tx_ref}"

        payload = {
            "amount": str(sale.total_amount),
            "currency": "ETB",
            "tx_ref": tx_ref,
            "callback_url": callback_url,
            "return_url": return_url,
            "customization": {"title": "NovaPOS Payment", "description": f"Sale {sale.receipt_number}"},
        }
        if customer_email:
            payload["email"] = customer_email
        if customer_name:
            parts = customer_name.split(" ", 1)
            payload["first_name"] = parts[0]
            if len(parts) > 1:
                payload["last_name"] = parts[1]

        try:
            resp = requests.post(
                f"{self.base_url}/v1/transaction/initialize",
                json=payload, headers=self._headers(), timeout=10,
            )
            data = resp.json()
        except requests.RequestException as exc:
            raise AppError(f"Could not reach Chapa: {exc}", status_code=502, error_code="CHAPA_UNREACHABLE")

        if resp.status_code != 200 or data.get("status") != "success":
            raise AppError(
                f"Chapa initialization failed: {data.get('message', 'unknown error')}",
                status_code=502, error_code="CHAPA_INIT_FAILED",
            )

        checkout_url = data["data"]["checkout_url"]
        return tx_ref, checkout_url

    def verify_transaction(self, tx_ref):
        """Confirm a transaction's real status directly with Chapa (never trust the webhook alone)."""
        if not self.secret_key:
            # Dev/placeholder mode: treat as successful so the flow can be tested end-to-end.
            return {"status": "success", "tx_ref": tx_ref}

        try:
            resp = requests.get(
                f"{self.base_url}/v1/transaction/verify/{tx_ref}",
                headers=self._headers(), timeout=10,
            )
            data = resp.json()
        except requests.RequestException as exc:
            raise AppError(f"Could not reach Chapa: {exc}", status_code=502, error_code="CHAPA_UNREACHABLE")

        return data.get("data", {})

    def verify_webhook_signature(self, raw_body: bytes, signature_header: str) -> bool:
        if not self.webhook_secret:
            # No secret configured: accept but caller should still verify with verify_transaction().
            return True
        computed = hmac.new(self.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature_header or "")
