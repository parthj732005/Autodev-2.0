import { useTheme } from "../hooks/useTheme";

/**
 * compact=true renders an icon-only circular button, for pages with no
 * sidebar (Login/Register). Default renders the full labeled row used in
 * the Sidebar.
 */
export default function ThemeToggle({ compact = false }) {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === "light";

  if (compact) {
    return (
      <button
        onClick={toggleTheme}
        title={isLight ? "Switch to dark theme" : "Switch to light theme"}
        className="w-10 h-10 flex items-center justify-center rounded-full border border-border
                   bg-surface hover:bg-surface-3 transition-colors"
      >
        <span className="text-base">{isLight ? "🌙" : "☀️"}</span>
      </button>
    );
  }

  return (
    <button
      onClick={toggleTheme}
      title={isLight ? "Switch to dark theme" : "Switch to light theme"}
      className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-medium
                 text-slate-400 hover:text-slate-100 hover:bg-surface-3 transition-colors"
    >
      <span className="text-base">{isLight ? "🌙" : "☀️"}</span>
      {isLight ? "Dark mode" : "Light mode"}
    </button>
  );
}
