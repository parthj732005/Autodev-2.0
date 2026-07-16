import { createContext } from "react";

// Split into its own file (not exported alongside AuthProvider) so Vite's
// Fast Refresh only ever sees component exports from AuthContext.jsx.
export const AuthContext = createContext(null);
