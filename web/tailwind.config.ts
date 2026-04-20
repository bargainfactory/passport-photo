import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        deep: {
          DEFAULT: "#050A14",
          50: "#0A1421",
          100: "#0D1B2A",
          200: "#112240",
          300: "#162D50",
          400: "#1E3A5F",
          500: "#1E4976",
        },
        accent: {
          DEFAULT: "#00D4FF",
          50: "rgba(0, 212, 255, 0.06)",
          100: "rgba(0, 212, 255, 0.12)",
          200: "rgba(0, 212, 255, 0.2)",
          300: "#00D4FF",
          400: "#00A8E8",
          500: "#3B82F6",
          600: "#2563EB",
        },
        navy: {
          50: "#E7ECF3",
          100: "#C5D0E0",
          200: "#8BA1C1",
          300: "#5173A2",
          400: "#1B3A6B",
          500: "#0F2847",
          600: "#0A2540",
          700: "#081D33",
          800: "#061526",
          900: "#040E19",
          950: "#02070D",
        },
        teal: {
          50: "rgba(0, 212, 255, 0.06)",
          100: "rgba(0, 212, 255, 0.12)",
          200: "rgba(0, 212, 255, 0.2)",
          300: "#4DE3FF",
          400: "#00D4FF",
          500: "#00A8E8",
          600: "#0087C4",
          700: "#006A9E",
          800: "#004D77",
          900: "#003050",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
        glow: "glow 3s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
        float: "float 6s ease-in-out infinite",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "gradient-shift": "gradientShift 12s ease infinite",
        "border-glow": "borderGlow 3s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        glow: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(0, 212, 255, 0.2)" },
          "50%": { boxShadow: "0 0 40px rgba(0, 212, 255, 0.45)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        gradientShift: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        borderGlow: {
          "0%, 100%": { borderColor: "rgba(0, 212, 255, 0.1)" },
          "50%": { borderColor: "rgba(0, 212, 255, 0.3)" },
        },
      },
      boxShadow: {
        glass: "0 8px 32px rgba(0, 0, 0, 0.3)",
        "glass-lg": "0 16px 48px rgba(0, 0, 0, 0.4)",
        "glow-sm": "0 0 15px rgba(0, 212, 255, 0.15)",
        "glow-teal": "0 0 30px rgba(0, 212, 255, 0.25)",
        "glow-teal-lg": "0 0 60px rgba(0, 212, 255, 0.35)",
        "glow-btn": "0 4px 20px rgba(0, 212, 255, 0.3), 0 0 40px rgba(0, 212, 255, 0.1)",
        "glow-btn-hover": "0 6px 30px rgba(0, 212, 255, 0.5), 0 0 80px rgba(0, 212, 255, 0.15)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

export default config;
