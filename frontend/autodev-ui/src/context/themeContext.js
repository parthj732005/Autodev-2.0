import { createContext } from "react";

// Split into its own file (not exported alongside ThemeProvider) so Vite's
// Fast Refresh only ever sees component exports from ThemeProvider.jsx.
export const ThemeContext = createContext(null);
