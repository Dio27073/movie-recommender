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
          primary: '#09090b',    // Almost black
          secondary: '#18181b',  // Very dark gray
          text: '#fafafa'        // Pure white
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