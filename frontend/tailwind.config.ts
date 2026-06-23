import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0f0ff",
          100: "#e4e3fe",
          500: "#534AB7",
          600: "#3C3489",
          900: "#1a1654",
        },
      },
    },
  },
  plugins: [],
};

export default config;