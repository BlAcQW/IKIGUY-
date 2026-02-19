/**
 * Currency selector component with custom rate support.
 *
 * Allows users to select their preferred currency and override exchange rates.
 */

import { Banknote, RefreshCw } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCurrencies, useExchangeRates, setCustomExchangeRate, currencyKeys } from "@/hooks/use-currencies";
import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

interface CurrencySelectorProps {
  value?: string;
  onValueChange?: (currency: string) => void;
}

export function CurrencySelector({ value = "USD", onValueChange }: CurrencySelectorProps) {
  const { data: currencies, isLoading } = useCurrencies();
  const { data: exchangeRates } = useExchangeRates();
  const [selectedCurrency, setSelectedCurrency] = useState(value);
  const [customRate, setCustomRate] = useState<string>("");
  const queryClient = useQueryClient();

  useEffect(() => {
    setSelectedCurrency(value);
  }, [value]);

  // Update local custom rate state when currency or rates change
  useEffect(() => {
    if (exchangeRates && selectedCurrency) {
      const rate = exchangeRates.rates[selectedCurrency];
      setCustomRate(rate ? rate.toString() : "");
    }
  }, [exchangeRates, selectedCurrency]);

  const handleCurrencyChange = (newValue: string) => {
    setSelectedCurrency(newValue);
    onValueChange?.(newValue);
  };

  const handleRateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVal = e.target.value;
    setCustomRate(newVal);

    // Debounce or save
    const numVal = parseFloat(newVal);
    if (!isNaN(numVal) && numVal > 0) {
      setCustomExchangeRate(selectedCurrency, numVal);
      // Invalidate queries to trigger re-render of prices
      queryClient.invalidateQueries({ queryKey: currencyKeys.rates() });
    }
  };

  const currentCurrencySymbol = currencies?.find(c => c.code === selectedCurrency)?.symbol || "$";

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="icon" className="h-9 w-9 rounded-full bg-background/50 backdrop-blur-sm border-primary/20 hover:border-primary/50 text-primary">
          <Banknote className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-4" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold leading-none">Currency Settings</h4>
            <Banknote className="h-4 w-4 text-primary" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="currency">Display Currency</Label>
            <Select value={selectedCurrency} onValueChange={handleCurrencyChange}>
              <SelectTrigger id="currency">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {currencies?.map((currency) => (
                  <SelectItem key={currency.code} value={currency.code}>
                    <span className="font-medium mr-2">{currency.symbol}</span>
                    {currency.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedCurrency !== "USD" && (
            <div className="space-y-2">
              <Label htmlFor="rate">Exchange Rate (1 USD = )</Label>
              <div className="relative">
                <Input
                  id="rate"
                  type="number"
                  value={customRate}
                  onChange={handleRateChange}
                  className="pl-8"
                />
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
                  {currentCurrencySymbol}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                  onClick={() => {
                    // Reset to default mock rate logic or refetch? 
                    // For now, just clear custom rate and reload context
                    localStorage.removeItem('estateflow_custom_rates');
                    queryClient.invalidateQueries({ queryKey: currencyKeys.rates() });
                  }}
                  title="Reset Rates"
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
