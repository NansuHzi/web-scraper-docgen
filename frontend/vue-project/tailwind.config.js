/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'neon-green': '#39FF14',
        'cyan-blue': '#00FFFF',
        'dark-bg': '#0f0f0f',
        'dark-surface': '#1a1a1a',
        'dark-card': '#242424',
        'dark-border': '#3a3a3a',
      },
      boxShadow: {
        'neon-green': '0 0 20px rgba(57, 255, 20, 0.4), 0 0 40px rgba(57, 255, 20, 0.2)',
        'neon-blue': '0 0 20px rgba(0, 255, 255, 0.4), 0 0 40px rgba(0, 255, 255, 0.2)',
        'neon-sm': '0 0 10px rgba(57, 255, 20, 0.3)',
      },
    },
  },
  plugins: [],
}
