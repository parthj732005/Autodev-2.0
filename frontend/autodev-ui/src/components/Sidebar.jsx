import { NavLink, useNavigate } from "react-router-dom";
import ThemeToggle from "./ThemeToggle";
import { useAuth } from "../hooks/useAuth";

const links = [
  { to: "/", label: "Home", icon: "🏠" },
  { to: "/generate", label: "Generate", icon: "⚡" },
  { to: "/projects", label: "Projects", icon: "📁" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="w-56 flex-shrink-0 bg-surface border-r border-border flex flex-col h-screen sticky top-0">
      <NavLink to="/" className="px-5 py-5 border-b border-border block hover:bg-surface-3 transition-colors">
        <span className="text-primary font-bold text-lg tracking-tight">AutoDev</span>
        <span className="ml-1 text-xs text-slate-500 font-mono">v2.0</span>
      </NavLink>

      <nav className="flex-1 p-3 space-y-1">
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-slate-400 hover:text-slate-100 hover:bg-surface-3"
              }`
            }
          >
            <span className="text-base">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-border space-y-1">
        <ThemeToggle />
      </div>

      <div className="p-4 border-t border-border space-y-2">
        {user && (
          <p className="text-xs text-slate-500 truncate" title={user.email}>
            {user.email}
          </p>
        )}
        <button
          onClick={handleLogout}
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}
