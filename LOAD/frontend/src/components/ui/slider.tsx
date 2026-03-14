import * as React from "react";
import { cn } from "@/lib/utils";

interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  label?: string;
  showValue?: boolean;
  formatValue?: (value: number) => string;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, value, min, max, step, onChange, label, showValue = true, formatValue, ...props }, ref) => {
    const pct = ((value - min) / (max - min)) * 100;
    const displayValue = formatValue ? formatValue(value) : value.toString();

    return (
      <div className={cn("space-y-2", className)}>
        {(label || showValue) && (
          <div className="flex items-center justify-between">
            {label && <span className="text-sm text-muted-foreground">{label}</span>}
            {showValue && (
              <span className="text-sm font-mono font-medium tabular-nums">{displayValue}</span>
            )}
          </div>
        )}
        <input
          ref={ref}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="w-full h-2 rounded-full appearance-none cursor-pointer bg-secondary
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-4
            [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-primary
            [&::-webkit-slider-thumb]:border-2
            [&::-webkit-slider-thumb]:border-primary
            [&::-webkit-slider-thumb]:shadow-sm
            [&::-webkit-slider-thumb]:transition-transform
            [&::-webkit-slider-thumb]:hover:scale-110
            [&::-moz-range-thumb]:w-4
            [&::-moz-range-thumb]:h-4
            [&::-moz-range-thumb]:rounded-full
            [&::-moz-range-thumb]:bg-primary
            [&::-moz-range-thumb]:border-2
            [&::-moz-range-thumb]:border-primary
            [&::-moz-range-thumb]:shadow-sm"
          style={{
            background: `linear-gradient(to right, hsl(var(--primary)) 0%, hsl(var(--primary)) ${pct}%, hsl(var(--secondary)) ${pct}%, hsl(var(--secondary)) 100%)`,
          }}
          {...props}
        />
        <div className="flex justify-between text-[10px] text-muted-foreground/60">
          <span>{formatValue ? formatValue(min) : min}</span>
          <span>{formatValue ? formatValue(max) : max}</span>
        </div>
      </div>
    );
  }
);
Slider.displayName = "Slider";

export { Slider };
