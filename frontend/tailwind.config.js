/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Syne', 'sans-serif'],
      },
      colors: {
        background: '#E6E1D8',
        card: '#E6E1D8',
        border: '#C4BDB5',
        text: '#2D2926',
        muted: '#7A7571',
        primary: {
          light: '#F8DED9',
          DEFAULT: '#F05A3F',
          dark: '#D84930',
        },
        danger: '#DC2626',
        warning: '#F59E0B',
        caution: '#D97706'
      }
    },
  },
  plugins: [],
}
