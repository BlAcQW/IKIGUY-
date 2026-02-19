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

interface BibleTranslation {
  id: string;
  name: string;
}

interface BibleVersionComboboxProps {
  translations: BibleTranslation[];
  value: string;
  onValueChange: (value: string) => void;
}

export function BibleVersionCombobox({
  translations,
  value,
  onValueChange,
}: BibleVersionComboboxProps) {
  const [open, setOpen] = useState(false);

  const selectedTranslation = translations.find((t) => t.id === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full md:w-72 justify-between"
        >
          {selectedTranslation ? selectedTranslation.name : "Select Bible version..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full md:w-72 p-0" align="start">
        <Command>
          <CommandInput placeholder="Search Bible versions..." />
          <CommandList>
            <CommandEmpty>No Bible version found.</CommandEmpty>
            <CommandGroup>
              {translations.map((translation) => (
                <CommandItem
                  key={translation.id}
                  value={translation.name}
                  onSelect={() => {
                    onValueChange(translation.id);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === translation.id ? "opacity-100" : "opacity-0"
                    )}
                  />
                  {translation.name}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
