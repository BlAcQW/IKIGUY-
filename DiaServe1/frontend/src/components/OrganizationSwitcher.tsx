/**
 * Organization Switcher Component.
 *
 * Allows admin users to switch between organizations.
 */

import { Building2, Check, ChevronsUpDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { useOrganization } from '@/contexts/OrganizationContext';
import { useState } from 'react';
import { cn } from '@/lib/utils';

export function OrganizationSwitcher() {
  const { organizations, currentOrganization, switchOrganization, isAdmin, loading } = useOrganization();
  const [open, setOpen] = useState(false);

  // Debug logging
  console.log('OrganizationSwitcher:', { isAdmin, loading, organizationsCount: organizations.length, currentOrganization });

  // Show loading state
  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
        <Building2 className="h-4 w-4 animate-pulse" />
        <span>Loading organizations...</span>
      </div>
    );
  }

  // Don't show switcher if not admin
  if (!isAdmin) {
    return null;
  }

  // Show single organization (no dropdown needed)
  if (organizations.length <= 1) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
        <Building2 className="h-4 w-4" />
        <span>{currentOrganization?.name || 'My Organization'}</span>
      </div>
    );
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="soft"
          role="combobox"
          aria-expanded={open}
          aria-label="Select organization"
          className="w-full justify-between hover:bg-primary/20 transition-all"
        >
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary/20 to-secondary/20">
              <Building2 className="h-4 w-4 text-primary" />
            </div>
            <span className="truncate font-medium">
              {currentOrganization?.name || 'Select organization...'}
            </span>
          </div>
          <ChevronsUpDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[280px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Search organization..." />
          <CommandEmpty>No organization found.</CommandEmpty>
          <CommandGroup heading="Organizations" className="p-2">
            {organizations.map((org) => (
              <CommandItem
                key={org.id}
                value={org.id}
                onSelect={() => {
                  switchOrganization(org.id);
                  setOpen(false);
                }}
              >
                <div className="flex w-full items-center gap-2">
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1 truncate">
                    <div className="font-medium">{org.name}</div>
                    {org.email && (
                      <div className="text-xs text-muted-foreground">{org.email}</div>
                    )}
                  </div>
                  <Check
                    className={cn(
                      'ml-auto h-4 w-4',
                      currentOrganization?.id === org.id
                        ? 'opacity-100'
                        : 'opacity-0'
                    )}
                  />
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
