import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        // Purple primary palette (keeping purple-600 as main)
        primary: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
        },
      },
      boxShadow: {
        // Subtle resting states
        'xs': '0 1px 2px 0 rgb(0 0 0 / 0.03)',
        'sm': '0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        // Card shadows (primary UI elements)
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
        'card-hover': '0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.05)',
        // Elevated elements (dropdowns, popovers)
        'elevated': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05)',
        'elevated-lg': '0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.05)',
        // Modal shadows (highest elevation)
        'modal': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
        'modal-lg': '0 30px 60px -15px rgb(0 0 0 / 0.3), 0 0 0 1px rgb(0 0 0 / 0.05)',
        // Focus rings
        'focus': '0 0 0 3px rgb(147 51 234 / 0.15)',
        'focus-blue': '0 0 0 3px rgb(59 130 246 / 0.15)',
        // Button press effect
        'inner': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
      },
      borderRadius: {
        'xl': '0.875rem',
        '2xl': '1rem',
      },
      zIndex: {
        'modal': '50',
        'modal-nested': '60',
        'modal-top': '70',
        'toast': '80',
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'bounce-sm': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      keyframes: {
        'modal-enter': {
          'from': { opacity: '0', transform: 'scale(0.96) translateY(8px)' },
          'to': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        'modal-exit': {
          'from': { opacity: '1', transform: 'scale(1) translateY(0)' },
          'to': { opacity: '0', transform: 'scale(0.96) translateY(8px)' },
        },
        'fade-in': {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
        'slide-up': {
          'from': { opacity: '0', transform: 'translateY(10px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        }
      },
      animation: {
        'modal-enter': 'modal-enter 0.2s ease-smooth',
        'modal-exit': 'modal-exit 0.15s ease-smooth',
        'fade-in': 'fade-in 0.2s ease-out',
        'slide-up': 'slide-up 0.25s ease-smooth',
        'slide-down': 'slide-down 0.3s ease-out'
      },
    },
  },
  plugins: [],
} satisfies Config
