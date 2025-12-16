/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        // Design system colors
        cream: '#fffaf5',
        charcoal: '#121111',
        // Knowledge Area colors
        'ka-planning': '#3B82F6',
        'ka-elicitation': '#10B981',
        'ka-rlcm': '#F59E0B',
        'ka-strategy': '#EF4444',
        'ka-radd': '#8B5CF6',
        'ka-solution': '#EC4899',
      },
      borderRadius: {
        'DEFAULT': '14px',
        'card': '14px',
        'lg': '22px',
      },
      spacing: {
        '22': '5.5rem',
        // Section spacing scale
        '80px': '5rem',
        '120px': '7.5rem',
        '160px': '10rem',
      },
      fontSize: {
        // Hero headline responsive scale
        'hero-sm': ['3.5rem', { lineHeight: '1.1', fontWeight: '600' }],
        'hero-md': ['4.5rem', { lineHeight: '1.1', fontWeight: '600' }],
        'hero-lg': ['5.5rem', { lineHeight: '1.05', fontWeight: '600' }],
        // Section header scale
        'section-sm': ['2.25rem', { lineHeight: '1.2', fontWeight: '500' }],
        'section-md': ['2.75rem', { lineHeight: '1.2', fontWeight: '500' }],
      },
      maxWidth: {
        'content': '1200px',
      },
      boxShadow: {
        'glass': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        'glass-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
        'card': '0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.08), 0 8px 24px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  plugins: [],
}
