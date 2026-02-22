/**
 * Currency selector component.
 *
 * Allows users to toggle between USD and GHS display currencies.
 */

import { Banknote } from "lucide-react";
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
import { Label } from "@/components/ui/label";
import { useCurrencies } from "@/hooks/use-currencies";
import { useState, useEffect } from "react";

interface CurrencySelectorProps {
  value?: string;
  onValueChange?: (currency: string) => void;
}

export function CurrencySelector({ value = "USD", onValueChange }: CurrencySelectorProps) {
  const { data: currencies } = useCurrencies();
  const [selectedCurrency, setSelectedCurrency] = useState(value);

  useEffect(() => {
    setSelectedCurrency(value);
  }, [value]);

  const handleCurrencyChange = (newValue: string) => {
    setSelectedCurrency(newValue);
    onValueChange?.(newValue);
  };

  // Only show USD and GHS
  const filteredCurrencies = currencies?.filter(
    (c) => c.code === "USD" || c.code === "GHS"
  );

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
                {filteredCurrencies?.map((currency) => (
                  <SelectItem key={currency.code} value={currency.code}>
                    <span className="font-medium mr-2">{currency.symbol}</span>
                    {currency.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
