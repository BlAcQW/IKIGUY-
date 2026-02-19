"""Outbound call manager for Demo 20 with Twilio/Vonage and MongoDB."""

from __future__ import annotations

import os
import re
from typing import Optional

from pymongo import MongoClient
import requests
from pydantic import BaseModel


class CallRecord(BaseModel):
    """Represents a single outbound call."""

    id: str
    phone_number: str
    message: str
    status: str
    opted_out: bool = False


class OutboundCallManager:
    """Schedule outbound calls and process webhook updates."""

    TWILIO_API = "https://api.twilio.com/2010-04-01"
    VONAGE_API = "https://api.nexmo.com/v1/calls"

    def __init__(
        self,
        provider: str,
        from_number: str,
        mongo_uri: str = "mongodb://localhost:27017",
        db_name: str = "voice_engine",
        **creds: str,
    ) -> None:
        """Initialize the manager.

        Args:
            provider: Telephony provider (``"twilio"`` or ``"vonage"``).
            from_number: Verified caller ID.
            mongo_uri: MongoDB connection URI.
            db_name: Database name for call records.
            **creds: Provider-specific credentials.
        """

        self.provider = provider
        self.from_number = from_number
        self._calls = MongoClient(mongo_uri)[db_name]["calls"]

        if provider == "twilio":
            self.account_sid = creds["account_sid"]
            self.auth_token = creds["auth_token"]
        elif provider == "vonage":
            self.api_key = creds["api_key"]
            self.api_secret = creds["api_secret"]
        else:
            raise ValueError("provider must be 'twilio' or 'vonage'")

    def schedule_call(self, phone_number: str, message: str) -> str:
        """Dial a phone number with a message.

        Args:
            phone_number: Destination number in E.164 format.
            message: Message to speak on the call.

        Returns:
            Provider-specific call ID.

        Raises:
            ValueError: If inputs are invalid.
            requests.HTTPError: If the provider API returns an error.
        """

        if not re.fullmatch(r"\+[1-9]\d{7,14}", phone_number):
            raise ValueError("phone_number must be E.164 format")
        if not message.strip():
            raise ValueError("message must not be empty")

        if self.provider == "twilio":
            twiml = f"<Response><Say>{message}</Say></Response>"
            url = f"{self.TWILIO_API}/Accounts/{self.account_sid}/Calls.json"
            resp = requests.post(
                url,
                data={"To": phone_number, "From": self.from_number, "Twiml": twiml},
                auth=(self.account_sid, self.auth_token),
                timeout=10,
            )
            resp.raise_for_status()
            call_id = resp.json()["sid"]
        else:  # vonage
            payload = {
                "to": [{"type": "phone", "number": phone_number}],
                "from": {"type": "phone", "number": self.from_number},
                "ncco": [{"action": "talk", "text": message}],
            }
            resp = requests.post(
                self.VONAGE_API,
                json=payload,
                auth=(self.api_key, self.api_secret),
                timeout=10,
            )
            resp.raise_for_status()
            call_id = resp.json()["uuid"]

        self._calls.insert_one(
            {
                "_id": call_id,
                "phone_number": phone_number,
                "message": message,
                "status": "queued",
                "opted_out": False,
            }
        )

        return call_id

    def handle_webhook(
        self, call_id: str, status: str, digits: Optional[str] = None
    ) -> None:
        """Persist status updates from provider webhooks.

        Args:
            call_id: Provider call identifier from :meth:`schedule_call`.
            status: New status (``completed``, ``failed``, etc.).
            digits: DTMF digits entered by the callee. ``"9"`` marks opt-out.
        """

        opted_out = digits == "9"
        final_status = "opted_out" if opted_out else status

        self._calls.update_one(
            {"_id": call_id},
            {"$set": {"status": final_status, "opted_out": opted_out}},
        )

    def get_call(self, call_id: str) -> Optional[CallRecord]:
        """Fetch a call record from the database."""

        doc = self._calls.find_one({"_id": call_id})
        if doc is None:
            return None
        return CallRecord(
            id=call_id,
            phone_number=doc["phone_number"],
            message=doc["message"],
            status=doc["status"],
            opted_out=bool(doc["opted_out"]),
        )


def create_manager_from_env() -> OutboundCallManager:
    """Create an :class:`OutboundCallManager` using environment variables.

    Environment Variables:
        OUTBOUND_PROVIDER: ``"twilio"`` or ``"vonage"``.
        OUTBOUND_MONGO_URI: MongoDB URI (optional, default ``mongodb://localhost:27017``).
        TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER:
            Credentials and caller ID for Twilio.
        VONAGE_API_KEY / VONAGE_API_SECRET / VONAGE_FROM_NUMBER:
            Credentials and caller ID for Vonage.

    Returns:
        OutboundCallManager: Configured manager instance.

    Raises:
        KeyError: If required environment variables are missing.
        ValueError: If ``OUTBOUND_PROVIDER`` is not supported.
    """

    provider = os.environ["OUTBOUND_PROVIDER"].lower()
    mongo_uri = os.getenv("OUTBOUND_MONGO_URI", "mongodb://localhost:27017")

    if provider == "twilio":
        return OutboundCallManager(
            "twilio",
            os.environ["TWILIO_FROM_NUMBER"],
            mongo_uri=mongo_uri,
            account_sid=os.environ["TWILIO_ACCOUNT_SID"],
            auth_token=os.environ["TWILIO_AUTH_TOKEN"],
        )

    if provider == "vonage":
        return OutboundCallManager(
            "vonage",
            os.environ["VONAGE_FROM_NUMBER"],
            mongo_uri=mongo_uri,
            api_key=os.environ["VONAGE_API_KEY"],
            api_secret=os.environ["VONAGE_API_SECRET"],
        )

    raise ValueError("OUTBOUND_PROVIDER must be 'twilio' or 'vonage'")
