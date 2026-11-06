/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/messaging/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        primary: "#137fec",
        secondary: "#8b5cf6"
      },
      fontFamily: {
        display: ["Manrope", "sans-serif"]
      }
    }
  },
  plugins: [],
}
