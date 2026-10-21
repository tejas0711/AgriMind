/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        forest: {
          50: "#f3f7f4",
          100: "#e4ede7",
          200: "#cbded1",
          300: "#a4c4ae",
          400: "#74a484",
          500: "#4f8661",
          600: "#3a6b4c",
          700: "#2f553d",
          800: "#264432",
          900: "#18392b", // Primary deep forest green
          950: "#0e2219",
        },
        leaf: {
          400: "#7fae4f",
          500: "#5c8f37",
          600: "#456b28",
          700: "#31501d",
        },
        soil: {
          50: "#faf7f2",
          100: "#f1eae0",
          200: "#e2d5c2",
          300: "#cbb69c",
          400: "#b09375",
          500: "#8a6b4e",
          600: "#6e5239",
          700: "#543c29",
          800: "#3d2b1d",
          900: "#24180f",
        },
        wheat: {
          50: "#fdfbf3",
          100: "#f9f5e3",
          200: "#f2e8c2",
          300: "#e8d697",
          400: "#dcbf68",
          500: "#cfa541",
          600: "#b08431",
        },
        canvas: "#faf8f4",
      },
      fontFamily: {
        display: ["'Fraunces'", "Georgia", "serif"],
        body: ["'Inter'", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        soft: "0 2px 8px -1px rgba(24, 57, 43, 0.05), 0 1px 3px -1px rgba(24, 57, 43, 0.03)",
        card: "0 4px 16px -2px rgba(24, 57, 43, 0.06), 0 2px 6px -1px rgba(24, 57, 43, 0.03)",
        elevated: "0 12px 28px -4px rgba(24, 57, 43, 0.08), 0 4px 10px -2px rgba(24, 57, 43, 0.04)",
      },
    },
  },
  plugins: [],
}
