/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#121212',
        surface: '#1e1e1e',
        border: '#333333',
        primary: '#6366f1',
        secondary: '#10b981',
        accent: '#f59e0b',
      },
    },
  },
  plugins: [],
}