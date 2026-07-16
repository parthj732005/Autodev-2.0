import { useCallback, useEffect, useState } from "react";
import { ThemeContext } from "./themeContext";

const THEME_KEY = "autodev_theme";

function getInitialTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  return stored === "light" || stored === "dark" ? stored : "dark";
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(getInitialTheme);

  // Applying the theme is a direct DOM attribute write, not a class/prop
  // threaded through the component tree — so switching themes never
  // re-renders (let alone remounts) unrelated pages like Generate, and
  // can never interrupt an in-flight WebSocket generation, touch auth
  // state, or reset any in-progress text/logs.
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
