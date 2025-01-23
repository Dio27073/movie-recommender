/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          primary: '#1a1a1a',
          secondary: '#2d2d2d',
          text: '#ffffff'
        },
        light: {
          primary: '#ffffff',
          secondary: '#f3f4f6',
          text: '#000000'
        }
      }
    },
  },
  plugins: [],
}