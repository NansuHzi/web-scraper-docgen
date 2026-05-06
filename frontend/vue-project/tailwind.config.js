/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geist', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'monospace'],
      },
      colors: {
        'neon-green': '#39FF14',
        'neon-green-dim': '#2BCC0F',
        'cyan-blue': '#00E5FF',
        'amber-warm': '#F59E0B',
        'base': '#060608',
        'surface': '#0E0E15',
        'elevated': '#14141F',
        'border': '#1E1E2E',
        'border-hover': '#2A2A3C',
        'muted': '#8B8B9E',
      },
      boxShadow: {
        'glow-green': '0 0 30px rgba(57, 255, 20, 0.15), 0 0 60px rgba(57, 255, 20, 0.06)',
        'glow-amber': '0 0 30px rgba(245, 158, 11, 0.12), 0 0 60px rgba(245, 158, 11, 0.04)',
        'glow-sm': '0 0 12px rgba(57, 255, 20, 0.2)',
        'card': '0 1px 2px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.3)',
        'card-hover': '0 2px 4px rgba(0,0,0,0.5), 0 8px 32px rgba(0,0,0,0.4)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out both',
        'slide-up': 'slideUp 0.5s ease-out both',
        'slide-down': 'slideDown 0.4s ease-out both',
        'scale-in': 'scaleIn 0.3s ease-out both',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(57, 255, 20, 0.1)' },
          '50%': { boxShadow: '0 0 40px rgba(57, 255, 20, 0.2)' },
        },
      },
    },
  },
  plugins: [],
}
