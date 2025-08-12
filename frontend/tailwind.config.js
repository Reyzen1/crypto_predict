// File: frontend/tailwind.config.js
// Tailwind CSS configuration for CryptoPredict

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Color palette for crypto theme
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))',
        },
        // Custom crypto colors
        crypto: {
          btc: '#f7931a',
          eth: '#627eea',
          ada: '#0033ad',
          dot: '#e6007a',
          link: '#2a5ada',
          green: {
            50: '#f0fdf4',
            100: '#dcfce7',
            200: '#bbf7d0',
            300: '#86efac',
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d',
            800: '#166534',
            900: '#14532d',
          },
          red: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            300: '#fca5a5',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
            800: '#991b1b',
            900: '#7f1d1d',
          },
        },
      },
      // Extended border radius
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      // Custom animations
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'fade-out': 'fadeOut 0.5s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'slide-out': 'slideOut 0.3s ease-out',
        'bounce-in': 'bounceIn 0.6s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'ping-slow': 'ping 3s cubic-bezier(0, 0, 0.2, 1) infinite',
        // Chart specific animations
        'chart-rise': 'chartRise 1s ease-out forwards',
        'chart-fall': 'chartFall 1s ease-out forwards',
        // Toast animations
        'toast-in': 'toastIn 0.3s ease-out',
        'toast-out': 'toastOut 0.2s ease-in forwards',
      },
      // Custom keyframes
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideIn: {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        slideOut: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(100%)' },
        },
        bounceIn: {
          '0%': { transform: 'scale(0.3)', opacity: '0' },
          '50%': { transform: 'scale(1.05)', opacity: '0.8' },
          '70%': { transform: 'scale(0.9)', opacity: '1' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.8)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        chartRise: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        chartFall: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        toastIn: {
          '0%': { transform: 'translateX(100%) scale(0.7)', opacity: '0' },
          '80%': { transform: 'translateX(-5%) scale(1.05)', opacity: '0.9' },
          '100%': { transform: 'translateX(0) scale(1)', opacity: '1' },
        },
        toastOut: {
          '0%': { transform: 'translateX(0) scale(1)', opacity: '1' },
          '100%': { transform: 'translateX(100%) scale(0.7)', opacity: '0' },
        },
      },
      // Extended spacing
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '120': '30rem',
        '144': '36rem',
      },
      // Custom font sizes
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.75rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '3.5rem' }],
        '6xl': ['3.75rem', { lineHeight: '4rem' }],
      },
      // Custom shadows for depth
      boxShadow: {
        'crypto': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(59, 130, 246, 0.1)',
        'crypto-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(59, 130, 246, 0.1)',
        'green': '0 4px 6px -1px rgba(34, 197, 94, 0.2)',
        'red': '0 4px 6px -1px rgba(239, 68, 68, 0.2)',
        'inner-light': 'inset 0 1px 2px rgba(255, 255, 255, 0.1)',
      },
      // Background patterns
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'grid-pattern': 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)',
      },
      // Grid template columns for complex layouts
      gridTemplateColumns: {
        'auto-fit-250': 'repeat(auto-fit, minmax(250px, 1fr))',
        'auto-fill-200': 'repeat(auto-fill, minmax(200px, 1fr))',
      },
      // Custom z-index scale
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
    // Custom plugin for crypto-specific utilities
    function({ addUtilities, addComponents, theme }) {
      // Add custom utilities
      addUtilities({
        '.text-gradient': {
          'background': 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
          '-webkit-background-clip': 'text',
          '-webkit-text-fill-color': 'transparent',
          'background-clip': 'text',
        },
        '.crypto-card-hover': {
          'transition': 'all 0.3s ease',
          '&:hover': {
            'transform': 'translateY(-2px)',
            'box-shadow': '0 10px 25px rgba(0, 0, 0, 0.2)',
          },
        },
        '.glass': {
          'background': 'rgba(255, 255, 255, 0.05)',
          'backdrop-filter': 'blur(10px)',
          'border': '1px solid rgba(255, 255, 255, 0.1)',
        },
      });

      // Add custom components
      addComponents({
        '.btn-crypto': {
          'padding': theme('spacing.2') + ' ' + theme('spacing.4'),
          'border-radius': theme('borderRadius.md'),
          'font-weight': theme('fontWeight.medium'),
          'transition': 'all 0.2s ease',
          'background': 'linear-gradient(135deg, #3b82f6, #1e40af)',
          'color': 'white',
          '&:hover': {
            'background': 'linear-gradient(135deg, #2563eb, #1e3a8a)',
            'transform': 'translateY(-1px)',
          },
        },
        '.card-crypto': {
          'background': theme('colors.gray.800'),
          'border': '1px solid ' + theme('colors.gray.700'),
          'border-radius': theme('borderRadius.lg'),
          'padding': theme('spacing.4'),
          'backdrop-filter': 'blur(10px)',
        },
      });
    },
  ],
};