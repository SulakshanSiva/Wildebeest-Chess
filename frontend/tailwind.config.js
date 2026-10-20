/** @type {import('tailwindcss').Config} */

// Every colour is a CSS variable (see src/Styles/theme.css) holding space-separated
// RGB channels, so a theme change is one file and Tailwind opacity modifiers still work.
const token = (name) => `rgb(var(--color-${name}) / <alpha-value>)`

module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        felt: token('felt'),
        'felt-raised': token('felt-raised'),
        ink: token('ink'),
        gold: token('gold'),
        'gold-light': token('gold-light'),
        cream: token('cream'),
      },
      fontFamily:{
        cinzel: ['Cinzel', 'serif']
      }
    },
  },
  plugins: [],
}
