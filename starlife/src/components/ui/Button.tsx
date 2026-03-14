import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

type ButtonVariant = 'gold' | 'outline' | 'blue' | 'white';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
  className?: string;
}

const variantStyles: Record<ButtonVariant, string> = {
  gold: 'bg-gold text-navy-dark hover:bg-gold-light font-semibold',
  outline:
    'border-2 border-white text-white hover:bg-white hover:text-navy font-semibold',
  blue: 'bg-blue-accent text-white hover:bg-blue-600 font-semibold',
  white: 'bg-white text-navy hover:bg-gray-100 font-semibold',
};

export function Button({
  variant = 'gold',
  children,
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded px-6 py-3 text-sm tracking-wide transition-all duration-200',
        variantStyles[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
