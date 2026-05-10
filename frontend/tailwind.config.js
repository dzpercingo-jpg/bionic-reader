/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        reader: ['Lexend', 'Inter', 'system-ui', 'sans-serif'],
        ui: ['Inter', 'system-ui', 'sans-serif'],
        dyslexic: ['"OpenDyslexic"', 'Lexend', 'sans-serif'],
        atkinson: ['"Atkinson Hyperlegible"', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
