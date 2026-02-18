import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: { 50: "#fef7ee", 100: "#fdedd6", 200: "#f9d7ad", 300: "#f4b978", 400: "#ee9242", 500: "#ea7620", 600: "#db5c16", 700: "#b54414", 800: "#903718", 900: "#742f16", 950: "#3f150a" },
      },
    },
  },
  plugins: [],
};

export default config;
