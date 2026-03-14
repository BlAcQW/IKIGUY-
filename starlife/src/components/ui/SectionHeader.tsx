import { cn } from '@/lib/utils';

interface SectionHeaderProps {
  overline?: string;
  title: string;
  dark?: boolean;
  className?: string;
}

export function SectionHeader({
  overline,
  title,
  dark = false,
  className,
}: SectionHeaderProps) {
  return (
    <div className={cn('mb-12 text-center', className)}>
      {overline && (
        <p
          className={cn(
            'mb-2 text-sm font-semibold uppercase tracking-widest',
            dark ? 'text-gold' : 'text-gold',
          )}
        >
          {overline}
        </p>
      )}
      <h2
        className={cn(
          'text-3xl font-bold md:text-4xl',
          dark ? 'text-white' : 'text-navy',
        )}
      >
        {title}
      </h2>
      <div className="mx-auto mt-4 h-1 w-16 rounded bg-gold" />
    </div>
  );
}
