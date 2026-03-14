/**
 * React Query hooks for currency operations.
 */

import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { listCurrencies, getExchangeRates } from "@/lib/api/currency-api";
import type { Currency, ExchangeRates } from "@/lib/types/property";

/**
 * Query keys for React Query cache management.
 */
export const currencyKeys = {
  all: ["currencies"] as const,
  list: () => [...currencyKeys.all, "list"] as const,
  rates: (forceRefresh?: boolean) => [...currencyKeys.all, "rates", forceRefresh] as const,
};

/**
 * Hook to list supported currencies.
 *
 * @param options - React Query options
 * @returns Query result
 */
export function useCurrencies(
  options?: Omit<UseQueryOptions<Currency[], Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: currencyKeys.list(),
    queryFn: listCurrencies,
    staleTime: Infinity, // Currencies don't change often
    ...options,
  });
}

/**
 * Hook to get current exchange rates.
 *
 * Exchange rates include admin overrides when set server-side.
 *
 * @param forceRefresh - Force API refresh
 * @param options - React Query options
 * @returns Query result
 */
export function useExchangeRates(
  forceRefresh = false,
  options?: Omit<UseQueryOptions<ExchangeRates, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: currencyKeys.rates(forceRefresh),
    queryFn: () => getExchangeRates(forceRefresh),
    staleTime: 1000 * 60 * 60, // 1 hour
    ...options,
  });
}
