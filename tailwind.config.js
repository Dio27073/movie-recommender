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
          secondary: '#121217',  // Very dark gray
          text: '#fafafa'        // Pure white
        },
        light: {
          primary: '#fcfcfc',
          secondary: '#f5f5f7',
          text: '#1f2937'
        }
      },
      animation: {
        'blob': "blob 7s infinite",
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'gradient': 'gradient 15s ease infinite',
      },
      keyframes: {
        blob: {
          "0%": {
            transform: "translate(0px, 0px) scale(1)",
          },
          "33%": {
            transform: "translate(30px, -50px) scale(1.1)",
          },
          "66%": {
            transform: "translate(-20px, 20px) scale(0.9)",
          },
          "100%": {
            transform: "translate(0px, 0px) scale(1)",
          },
        },
        gradient: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          },
        }
      },
      transitionDuration: {
        '2000': '2000ms',
        '3000': '3000ms',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glow': '0 0 15px rgba(155, 89, 182, 0.5)',
        'glow-lg': '0 0 25px rgba(155, 89, 182, 0.5)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}