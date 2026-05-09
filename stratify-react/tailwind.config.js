/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      colors: {
        'app-bg': '#050505',
        'app-surface': 'rgba(0,0,0,0.40)',
        'app-card': 'rgba(0,0,0,0.60)',
        'app-border': 'rgba(255,255,255,0.10)',
        'app-muted': '#71717A',
        'app-sub': '#A1A1AA',
        'app-accent': '#6366F1',
        'app-orange': '#F97316',
        'app-blue': '#5A93FF',
        'app-green': '#47D46B',
        'app-red': '#FF6A63',
        'app-yellow': '#FFC72C',
      },
      animation: {
        'fade-in': 'pageFadeIn 0.18s ease-out',
      },
      keyframes: {
        pageFadeIn: {
          from: { opacity: '0.82', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

