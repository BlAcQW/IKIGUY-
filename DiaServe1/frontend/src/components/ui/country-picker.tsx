import { useState } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  PRIORITY_COUNTRIES,
  ALL_COUNTRIES,
  type Country,
} from "@/lib/constants/countries";

interface CountryPickerProps {
  value: string;
  onValueChange: (value: string) => void;
}

function findCountry(name: string): Country | undefined {
  return (
    PRIORITY_COUNTRIES.find((c) => c.name === name) ??
    ALL_COUNTRIES.find((c) => c.name === name)
  );
}

export function CountryPicker({ value, onValueChange }: CountryPickerProps) {
  const [open, setOpen] = useState(false);
  const selected = findCountry(value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between h-11 font-normal"
        >
          {selected ? (
            <span>
              {selected.flag} {selected.name}
            </span>
          ) : (
            <span className="text-muted-foreground">Select country...</span>
          )}
          <ChevronsUpDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-[--radix-popover-trigger-width] p-0"
        align="start"
      >
        <Command>
          <CommandInput placeholder="Search country..." />
          <CommandList>
            <CommandEmpty>No country found.</CommandEmpty>
            <CommandGroup heading="Popular">
              {PRIORITY_COUNTRIES.map((country) => (
                <CommandItem
                  key={`priority-${country.code}`}
                  value={country.name}
                  onSelect={() => {
                    onValueChange(country.name);
                    setOpen(false);
                  }}
                >
                  <span className="mr-2">{country.flag}</span>
                  {country.name}
                  <Check
                    className={cn(
                      "ml-auto h-4 w-4",
                      value === country.name ? "opacity-100" : "opacity-0",
                    )}
                  />
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandGroup heading="All Countries">
              {ALL_COUNTRIES.map((country) => (
                <CommandItem
                  key={`all-${country.code}`}
                  value={country.name}
                  onSelect={() => {
                    onValueChange(country.name);
                    setOpen(false);
                  }}
                >
                  <span className="mr-2">{country.flag}</span>
                  {country.name}
                  <Check
                    className={cn(
                      "ml-auto h-4 w-4",
                      value === country.name ? "opacity-100" : "opacity-0",
                    )}
                  />
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
