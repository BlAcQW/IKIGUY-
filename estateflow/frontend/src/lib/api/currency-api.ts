/**
 * Currency API client for EstateFlow.
 *
 * Provides functions to interact with currency endpoints.
 */

import { buildApiUrl, getDefaultHeaders, API_ENDPOINTS } from "../api-config";
import type { Currency, ExchangeRates } from "../types/property";

/**
 * List supported currencies.
 *
 * @returns Promise<Currency[]>
 */
export async function listCurrencies(): Promise<Currency[]> {
  const url = buildApiUrl(API_ENDPOINTS.currencies.list);

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to fetch currencies" }));
    throw new Error(error.detail || "Failed to fetch currencies");
  }

  return response.json();
}

/**
 * Get current exchange rates.
 *
 * @param forceRefresh - Force API refresh even if cache is valid
 * @returns Promise<ExchangeRates>
 */
export async function getExchangeRates(forceRefresh = false): Promise<ExchangeRates> {
  const params = forceRefresh ? "?force_refresh=true" : "";
  const url = buildApiUrl(`${API_ENDPOINTS.currencies.rates}${params}`);

  const response = await fetch(url, {
    method: "GET",
    headers: getDefaultHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to fetch exchange rates" }));
    throw new Error(error.detail || "Failed to fetch exchange rates");
  }

  return response.json();
}

/**
 * Convert price from USD to target currency.
 *
 * @param priceUSD - Price in USD
 * @param targetCurrency - Target currency code
 * @param rates - Exchange rates object
 * @returns Converted price
 */
export function convertPrice(
  priceUSD: number,
  targetCurrency: string,
  rates: ExchangeRates
): number {
  if (targetCurrency === "USD") return priceUSD;

  const rate = rates.rates[targetCurrency];
  if (!rate) return priceUSD;

  return Math.round(priceUSD * rate * 100) / 100;
}

/**
 * Format price with currency symbol.
 *
 * @param price - Price amount
 * @param currency - Currency object
 * @returns Formatted price string
 */
export function formatPrice(price: number, currency: Currency): string {
  const formatted = price.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });

  return `${currency.symbol}${formatted}`;
}
