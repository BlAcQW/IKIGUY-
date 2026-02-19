"""
Currency service for multi-currency support in EstateFlow.

Provides real-time exchange rate fetching, caching, and currency conversion.
Uses exchangerate-api.io for fetching current rates.
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class Currency(BaseModel):
    """
    Currency information model.

    Attributes:
        code: ISO 4217 currency code (USD, EUR, GHS, etc.)
        name: Currency full name
        symbol: Currency symbol ($, €, ¢, etc.)
    """
    code: str
    name: str
    symbol: str


class ExchangeRate(BaseModel):
    """
    Exchange rate information.

    Attributes:
        base_currency: Base currency code (always USD)
        rates: Dictionary of currency codes to exchange rates
        last_updated: When rates were last fetched
        source: Source API name
    """
    base_currency: str = "USD"
    rates: Dict[str, float]
    last_updated: datetime
    source: str = "exchangerate-api"


# Supported currencies with symbols
SUPPORTED_CURRENCIES = [
    Currency(code="USD", name="US Dollar", symbol="$"),
    Currency(code="EUR", name="Euro", symbol="€"),
    Currency(code="GBP", name="British Pound", symbol="£"),
    Currency(code="GHS", name="Ghanaian Cedi", symbol="GH¢"),
    Currency(code="NGN", name="Nigerian Naira", symbol="₦"),
    Currency(code="ZAR", name="South African Rand", symbol="R"),
    Currency(code="KES", name="Kenyan Shilling", symbol="KSh"),
    Currency(code="CAD", name="Canadian Dollar", symbol="C$"),
    Currency(code="AUD", name="Australian Dollar", symbol="A$"),
    Currency(code="JPY", name="Japanese Yen", symbol="¥"),
    Currency(code="CNY", name="Chinese Yuan", symbol="¥"),
    Currency(code="INR", name="Indian Rupee", symbol="₹"),
]


class CurrencyService:
    """
    Service for currency operations.

    Provides exchange rate fetching, caching, and conversion functionality.
    Implements 1-hour cache TTL to minimize API calls and costs.
    """

    def __init__(self, database: AsyncIOMotorDatabase, api_key: Optional[str] = None):
        """
        Initialize currency service.

        Args:
            database: MongoDB database instance
            api_key: Exchange rate API key (optional, free tier works without key)
        """
        self.db = database
        self.api_key = api_key
        self.cache_ttl_hours = 1  # Cache exchange rates for 1 hour
        self.base_url = "https://api.exchangerate-api.com/v4/latest"  # Free API (no key required)

        # If API key provided, use paid tier with better limits
        if api_key:
            self.base_url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest"

    async def get_supported_currencies(self) -> List[Currency]:
        """
        Get list of supported currencies.

        Returns:
            List[Currency]: List of supported currency objects
        """
        return SUPPORTED_CURRENCIES

    async def get_exchange_rates(self, force_refresh: bool = False) -> ExchangeRate:
        """
        Get current exchange rates from cache or API.

        Implements caching strategy:
        1. Check cache for rates less than 1 hour old
        2. If cache miss or expired, fetch from API
        3. Store new rates in cache

        Args:
            force_refresh: Force API fetch even if cache is valid

        Returns:
            ExchangeRate: Exchange rate data

        Raises:
            httpx.HTTPError: If API request fails
        """
        # Reason: Check cache first to minimize API calls and cost
        if not force_refresh:
            cached_rates = await self._get_cached_rates()
            if cached_rates:
                logger.info(f"Using cached exchange rates from {cached_rates.last_updated}")
                return cached_rates

        # Fetch fresh rates from API
        logger.info("Fetching fresh exchange rates from API")
        rates = await self._fetch_rates_from_api()

        # Store in cache
        await self._cache_rates(rates)

        return rates

    async def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        force_refresh: bool = False
    ) -> float:
        """
        Get exchange rate between two currencies.

        Args:
            from_currency: Source currency code (USD, EUR, etc.)
            to_currency: Target currency code
            force_refresh: Force API fetch even if cache is valid

        Returns:
            float: Exchange rate (to_currency per from_currency)

        Raises:
            ValueError: If currency codes are invalid
            httpx.HTTPError: If API request fails

        Example:
            rate = await service.get_exchange_rate("USD", "EUR")
            # If rate is 0.85, then 1 USD = 0.85 EUR
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Validate currency codes
        valid_codes = {c.code for c in SUPPORTED_CURRENCIES}
        if from_currency not in valid_codes or to_currency not in valid_codes:
            raise ValueError(f"Invalid currency code. Supported: {', '.join(valid_codes)}")

        # If same currency, rate is 1.0
        if from_currency == to_currency:
            return 1.0

        # Get all rates (base USD)
        exchange_rates = await self.get_exchange_rates(force_refresh)

        # Reason: Convert via USD as base currency
        # If from_currency is USD, directly use the rate
        if from_currency == "USD":
            return exchange_rates.rates.get(to_currency, 1.0)

        # If to_currency is USD, return inverse of from_currency rate
        if to_currency == "USD":
            from_rate = exchange_rates.rates.get(from_currency, 1.0)
            return 1.0 / from_rate if from_rate != 0 else 1.0

        # For other currency pairs, convert via USD
        # Formula: (1 USD -> to_currency) / (1 USD -> from_currency)
        to_rate = exchange_rates.rates.get(to_currency, 1.0)
        from_rate = exchange_rates.rates.get(from_currency, 1.0)

        return to_rate / from_rate if from_rate != 0 else 1.0

    async def convert_price(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        force_refresh: bool = False
    ) -> float:
        """
        Convert amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            force_refresh: Force API fetch even if cache is valid

        Returns:
            float: Converted amount

        Example:
            converted = await service.convert_price(100.0, "USD", "EUR")
            # Returns approximately 85.0 EUR (based on current rates)
        """
        rate = await self.get_exchange_rate(from_currency, to_currency, force_refresh)
        return round(amount * rate, 2)

    async def convert_property_price(
        self,
        price_usd: float,
        target_currency: str,
        force_refresh: bool = False
    ) -> Dict[str, float]:
        """
        Convert property price from USD to target currency.

        Returns both the converted price and the exchange rate used.

        Args:
            price_usd: Property price in USD
            target_currency: Target currency code
            force_refresh: Force API fetch

        Returns:
            dict: {
                "price": converted price,
                "currency": target currency code,
                "exchange_rate": rate used,
                "base_price_usd": original USD price
            }
        """
        rate = await self.get_exchange_rate("USD", target_currency, force_refresh)
        converted_price = round(price_usd * rate, 2)

        return {
            "price": converted_price,
            "currency": target_currency,
            "exchange_rate": rate,
            "base_price_usd": price_usd
        }

    async def _fetch_rates_from_api(self) -> ExchangeRate:
        """
        Fetch exchange rates from external API.

        Uses exchangerate-api.com (free tier or paid with API key).

        Returns:
            ExchangeRate: Fresh exchange rate data

        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use base URL (free or paid tier)
                url = f"{self.base_url}/USD"

                logger.info(f"Fetching exchange rates from {url}")
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()

                # Parse response (format differs slightly between free and paid)
                if "rates" in data:
                    rates = data["rates"]
                elif "conversion_rates" in data:
                    rates = data["conversion_rates"]
                else:
                    raise ValueError("Unexpected API response format")

                # Filter to only supported currencies
                supported_codes = {c.code for c in SUPPORTED_CURRENCIES}
                filtered_rates = {
                    code: rate
                    for code, rate in rates.items()
                    if code in supported_codes
                }

                return ExchangeRate(
                    base_currency="USD",
                    rates=filtered_rates,
                    last_updated=datetime.utcnow(),
                    source="exchangerate-api"
                )

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            # Return fallback rates if API fails
            return await self._get_fallback_rates()
        except Exception as e:
            logger.error(f"Unexpected error fetching rates: {e}")
            return await self._get_fallback_rates()

    async def _get_cached_rates(self) -> Optional[ExchangeRate]:
        """
        Get exchange rates from cache if available and not expired.

        Returns:
            Optional[ExchangeRate]: Cached rates or None if cache miss/expired
        """
        try:
            collection = self.db["exchange_rates"]

            # Find most recent rate document
            doc = await collection.find_one(
                {"base_currency": "USD"},
                sort=[("last_updated", -1)]
            )

            if not doc:
                return None

            # Check if cache is still valid (less than 1 hour old)
            last_updated = doc["last_updated"]
            cache_age = datetime.utcnow() - last_updated

            if cache_age > timedelta(hours=self.cache_ttl_hours):
                logger.info(f"Cache expired (age: {cache_age})")
                return None

            return ExchangeRate(
                base_currency=doc["base_currency"],
                rates=doc["rates"],
                last_updated=last_updated,
                source=doc.get("source", "exchangerate-api")
            )

        except Exception as e:
            logger.error(f"Error reading cached rates: {e}")
            return None

    async def _cache_rates(self, rates: ExchangeRate) -> None:
        """
        Store exchange rates in cache.

        Args:
            rates: Exchange rate data to cache
        """
        try:
            collection = self.db["exchange_rates"]

            doc = {
                "base_currency": rates.base_currency,
                "rates": rates.rates,
                "last_updated": rates.last_updated,
                "source": rates.source
            }

            # Insert new cache entry
            await collection.insert_one(doc)

            logger.info(f"Cached {len(rates.rates)} exchange rates")

        except Exception as e:
            logger.error(f"Error caching rates: {e}")

    async def _get_fallback_rates(self) -> ExchangeRate:
        """
        Get fallback exchange rates when API is unavailable.

        Uses approximate rates as a last resort.

        Returns:
            ExchangeRate: Fallback exchange rates
        """
        logger.warning("Using fallback exchange rates (API unavailable)")

        # Reason: Provide approximate rates to keep system functional
        # These are rough estimates and should be updated via API ASAP
        fallback_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "GHS": 15.50,
            "NGN": 1650.0,
            "ZAR": 18.50,
            "KES": 155.0,
            "CAD": 1.38,
            "AUD": 1.53,
            "JPY": 150.0,
            "CNY": 7.25,
            "INR": 83.0,
        }

        return ExchangeRate(
            base_currency="USD",
            rates=fallback_rates,
            last_updated=datetime.utcnow(),
            source="fallback"
        )

    async def update_exchange_rates(self) -> ExchangeRate:
        """
        Force update exchange rates from API.

        This should be called periodically (e.g., hourly) by a background job.

        Returns:
            ExchangeRate: Updated exchange rates
        """
        logger.info("Running scheduled exchange rate update")
        return await self.get_exchange_rates(force_refresh=True)
