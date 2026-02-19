/**
 * Currency selector component.
 *
 * Allows users to select their preferred currency for viewing prices.
 */

import { Globe } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCurrencies } from "@/hooks/use-currencies";
import { useState } from "react";

interface CurrencySelectorProps {
  value?: string;
  onValueChange?: (currency: string) => void;
}

export function CurrencySelector({ value = "USD", onValueChange }: CurrencySelectorProps) {
  const { data: currencies, isLoading } = useCurrencies();
  const [selectedCurrency, setSelectedCurrency] = useState(value);

  const handleValueChange = (newValue: string) => {
    setSelectedCurrency(newValue);
    onValueChange?.(newValue);
  };

  // Get the current currency symbol
  const currentCurrency = currencies?.find(c => c.code === selectedCurrency);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Globe className="h-4 w-4 animate-pulse" />
      </div>
    );
  }

  if (!currencies || currencies.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Globe className="h-4 w-4" />
        <span>$</span>
      </div>
    );
  }

  return (
    <Select value={selectedCurrency} onValueChange={handleValueChange}>
      <SelectTrigger className="w-[80px]">
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4" />
          <span className="font-medium">{currentCurrency?.symbol || "$"}</span>
        </div>
      </SelectTrigger>
      <SelectContent>
        {currencies.map((currency) => (
          <SelectItem key={currency.code} value={currency.code}>
            <span className="font-medium text-base">{currency.symbol}</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
