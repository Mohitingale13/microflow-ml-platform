import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Database,
  FlaskConical,
  Brain,
  Archive,
  BarChart3,
  GitBranch,
} from "lucide-react";

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: "Dashboard", path: "/", icon: <LayoutDashboard size={18} /> },
  { label: "Datasets", path: "/datasets", icon: <Database size={18} /> },
  { label: "Experiments", path: "/experiments", icon: <FlaskConical size={18} /> },
  { label: "Training", path: "/training", icon: <Brain size={18} /> },
  { label: "Artifacts", path: "/artifacts", icon: <Archive size={18} /> },
  { label: "Metrics", path: "/metrics", icon: <BarChart3 size={18} /> },
  { label: "Pipeline", path: "/pipeline", icon: <GitBranch size={18} /> },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      <div 
        className={`sidebar-overlay ${isOpen ? "open" : ""}`} 
        onClick={onClose} 
      />
      <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span className="logo-icon">μ</span>
          <span className="logo-text">MicroFlow</span>
        </div>
        <p className="logo-tagline">Machine Learning Operations Platform</p>
      </div>

      <nav className="sidebar-nav">
        <ul>
          {navItems.map(({ label, path, icon }) => (
            <li key={path}>
              <NavLink
                to={path}
                end={path === "/"}
                onClick={onClose}
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link--active" : ""}`
                }
              >
                <span className="nav-icon">{icon}</span>
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <p className="sidebar-version">v1.0.0</p>
      </div>
    </aside>
    </>
  );
}
