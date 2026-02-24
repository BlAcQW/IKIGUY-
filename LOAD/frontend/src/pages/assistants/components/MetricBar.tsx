interface MetricBarProps {
  label: string;
  value: string;
  percent: number;
  color: 'green' | 'yellow' | 'blue' | 'red';
}

const colorMap = {
  green: 'bg-emerald-500',
  yellow: 'bg-yellow-500',
  blue: 'bg-blue-500',
  red: 'bg-red-500',
};

const bgColorMap = {
  green: 'bg-emerald-500/15',
  yellow: 'bg-yellow-500/15',
  blue: 'bg-blue-500/15',
  red: 'bg-red-500/15',
};

export function MetricBar({ label, value, percent, color }: MetricBarProps) {
  return (
    <div className="flex items-center gap-3 min-w-0">
      <span className="text-[10px] text-muted-foreground whitespace-nowrap">{label}</span>
      <div className={`flex-1 h-1.5 rounded-full ${bgColorMap[color]} min-w-[40px]`}>
        <div
          className={`h-full rounded-full ${colorMap[color]} transition-all duration-300`}
          style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
        />
      </div>
      <span className="text-[10px] font-mono text-muted-foreground whitespace-nowrap">{value}</span>
    </div>
  );
}
