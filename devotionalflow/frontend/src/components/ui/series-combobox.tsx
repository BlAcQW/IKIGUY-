import * as React from "react";
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

interface Series {
	id: string;
	name: string;
}

interface SeriesComboboxProps {
	series: Series[];
	value: string | null;
	onValueChange: (value: string | null) => void;
	placeholder?: string;
	isLoading?: boolean;
}

export function SeriesCombobox({
	series,
	value,
	onValueChange,
	placeholder = "Select series...",
	isLoading = false,
}: SeriesComboboxProps) {
	const [open, setOpen] = React.useState(false);

	const selectedSeries = series.find((s) => s.id === value);

	return (
		<Popover open={open} onOpenChange={setOpen} modal={false}>
			<PopoverTrigger asChild>
				<Button
					variant="outline"
					role="combobox"
					aria-expanded={open}
					className="w-full justify-between"
					disabled={isLoading}
				>
					{selectedSeries ? selectedSeries.name : placeholder}
					<ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
				</Button>
			</PopoverTrigger>
			<PopoverContent 
				className="w-[400px] p-0" 
				align="start" 
				sideOffset={4}
			>
				<Command>
					<CommandInput placeholder="Search series..." />
					<CommandList>
						<CommandEmpty>No series found.</CommandEmpty>
						<CommandGroup>
							{/* Option to create new series */}
							<CommandItem
								value="__new__"
								onSelect={() => {
									onValueChange(null);
									setOpen(false);
								}}
							>
								<Check
									className={cn(
										"mr-2 h-4 w-4",
										value === null ? "opacity-100" : "opacity-0"
									)}
								/>
								Create New Series
							</CommandItem>

							{/* Existing series */}
							{series.map((seriesItem) => (
								<CommandItem
									key={seriesItem.id}
									value={seriesItem.name}
									onSelect={() => {
										onValueChange(seriesItem.id);
										setOpen(false);
									}}
								>
									<Check
										className={cn(
											"mr-2 h-4 w-4",
											value === seriesItem.id ? "opacity-100" : "opacity-0"
										)}
									/>
									{seriesItem.name}
								</CommandItem>
							))}
						</CommandGroup>
					</CommandList>
				</Command>
			</PopoverContent>
		</Popover>
	);
}
