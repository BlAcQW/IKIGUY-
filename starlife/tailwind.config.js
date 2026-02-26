/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#003366',
          dark: '#002244',
          light: '#004488',
        },
        gold: {
          DEFAULT: '#c8a951',
          light: '#d4ba6a',
        },
        'blue-accent': '#0693e3',
        'light-bg': '#f7f8fa',
      },
      fontFamily: {
        poppins: ['Poppins', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.8s ease-in-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'chat-open': 'chatOpen 300ms ease-out',
        'bounce-dot': 'bounceDot 1.2s infinite ease-in-out',
        'call-pulse': 'callPulse 2s ease-in-out infinite',
        'call-connecting': 'callConnecting 1.5s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', maxHeight: '0' },
          '100%': { opacity: '1', maxHeight: '500px' },
        },
        slideUp: {
          '0%': { opacity: '1', maxHeight: '500px' },
          '100%': { opacity: '0', maxHeight: '0' },
        },
        chatOpen: {
          '0%': { opacity: '0', transform: 'scale(0.95) translateY(10px)' },
          '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        bounceDot: {
          '0%, 80%, 100%': { transform: 'translateY(0)' },
          '40%': { transform: 'translateY(-6px)' },
        },
        callPulse: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.3' },
          '50%': { transform: 'scale(1.15)', opacity: '0.15' },
        },
        callConnecting: {
          '0%, 100%': { transform: 'scale(0.95)', opacity: '0.4' },
          '50%': { transform: 'scale(1.1)', opacity: '0.2' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
