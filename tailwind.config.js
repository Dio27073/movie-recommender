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
          primary: '#13151a',
          secondary: '#0f172a',
          text: '#ffffff'
        },
        light: {
          primary: '#fcfcfc',
          secondary: '#f5f5f7',
          text: '#1f2937'
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}