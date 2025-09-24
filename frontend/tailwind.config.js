/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          500: '#1E3A8A', // navy-800
          600: '#1E40AF', // navy-700
          400: '#3730A3', // indigo-700
          300: '#4338CA', // indigo-600
        }
      }
    },
  },
  plugins: [],
}
