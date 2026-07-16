/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Theme-aware tokens — values come from CSS variables in index.css,
        // swapped by the [data-theme] attribute on <html>. Using the
        // rgb(var(...) / <alpha-value>) form preserves opacity modifiers
        // (e.g. bg-surface/10) exactly like Tailwind's own palette.
        page: "rgb(var(--color-page) / <alpha-value>)",
        surface: {
          DEFAULT: "rgb(var(--color-surface) / <alpha-value>)",
          2: "rgb(var(--color-surface-2) / <alpha-value>)",
          3: "rgb(var(--color-surface-3) / <alpha-value>)",
        },
        border: "rgb(var(--color-border) / <alpha-value>)",
        // Overrides Tailwind's built-in slate scale so every existing
        // text-slate-*/border-slate-*/bg-slate-* class across the app
        // automatically re-themes — no component changes needed. The
        // light theme inverts this scale (100<->900-ish) so "100" always
        // means "most prominent text" and "700" always means "most muted",
        // regardless of which theme is active.
        slate: {
          50: "rgb(var(--slate-100) / <alpha-value>)",
          100: "rgb(var(--slate-100) / <alpha-value>)",
          200: "rgb(var(--slate-200) / <alpha-value>)",
          300: "rgb(var(--slate-300) / <alpha-value>)",
          400: "rgb(var(--slate-400) / <alpha-value>)",
          500: "rgb(var(--slate-500) / <alpha-value>)",
          600: "rgb(var(--slate-600) / <alpha-value>)",
          700: "rgb(var(--slate-700) / <alpha-value>)",
          800: "rgb(var(--slate-700) / <alpha-value>)",
          900: "rgb(var(--slate-700) / <alpha-value>)",
        },
        // Accent colors are unchanged across themes — they're used at low
        // opacity (e.g. bg-success/10) and already read fine on both a
        // near-black and a near-white background.
        primary: {
          DEFAULT: "#6366f1",
          hover: "#4f46e5",
        },
        success: "#22c55e",
        warning: "#f59e0b",
        danger: "#ef4444",
      },
    },
  },
  plugins: [],
};
