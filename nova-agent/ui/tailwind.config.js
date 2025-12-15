/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        neonPink: "#ff00ff",
        neonBlue: "#00eaff",
        neonPurple: "#9d4edd",
      },
    },
  },
  plugins: [],
};
