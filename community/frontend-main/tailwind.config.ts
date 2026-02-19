import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./pages/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  safelist: [
    'container', 'mx-auto', 'px-4', 'py-8', 'py-20', 'lg:py-28',
    'grid', 'grid-cols-1', 'grid-cols-2', 'lg:grid-cols-2', 'lg:grid-cols-3', 'md:grid-cols-2', 'md:grid-cols-4',
    'flex', 'items-center', 'justify-center', 'justify-between', 'space-x-3', 'space-y-4', 'space-y-8', 'gap-4', 'gap-6', 'gap-12',
    'text-center', 'text-lg', 'text-xl', 'text-2xl', 'text-3xl', 'text-4xl', 'text-5xl', 'lg:text-6xl', 'font-bold', 'font-medium',
    'bg-white', 'bg-background', 'shadow-lg', 'rounded-lg', 'rounded-xl',
    'max-w-7xl', 'max-w-4xl', 'w-full', 'h-full', 'relative', 'absolute', 'inset-0',
    'z-10', 'z-0', 'overflow-hidden', 'leading-tight',
    'min-h-screen', 'object-cover', 'opacity-20'
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
          glow: "var(--primary-glow)",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Community-specific colors
        community: {
          gold: "hsl(var(--community-gold))",
          silver: "hsl(var(--community-silver))",
          bronze: "hsl(var(--community-bronze))",
        },
        // Quality tier colors
        "tier-1": "hsl(var(--tier-1))",
        "tier-2": "hsl(var(--tier-2))",
        "tier-3": "hsl(var(--tier-3))",
        // Cultural accent colors
        cultural: {
          warm: "hsl(var(--cultural-warm))",
          earth: "hsl(var(--cultural-earth))",
          nature: "hsl(var(--cultural-nature))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: {
            height: "0",
          },
          to: {
            height: "var(--radix-accordion-content-height)",
          },
        },
        "accordion-up": {
          from: {
            height: "var(--radix-accordion-content-height)",
          },
          to: {
            height: "0",
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
