import { useLocation } from "react-router-dom";
import { useHealth } from "@/hooks/useHealth";
import { Menu } from "lucide-react";

const routeLabels: Record<string, string> = {
  "/": "Dashboard",
  "/datasets": "Datasets",
  "/experiments": "Experiments",
  "/training": "Training",
  "/artifacts": "Artifacts",
  "/metrics": "Metrics",
  "/pipeline": "Pipeline",
};

interface NavbarProps {
  onMenuToggle: () => void;
}

export function Navbar({ onMenuToggle }: NavbarProps) {
  const { pathname } = useLocation();
  const { data: health, isSuccess } = useHealth();
  const pageTitle = routeLabels[pathname] ?? "MicroFlow";

  return (
    <header className="navbar">
      <div className="navbar-title">
        <button className="mobile-menu-btn" onClick={onMenuToggle} aria-label="Toggle menu">
          <Menu size={20} />
        </button>
        <h1>{pageTitle}</h1>
      </div>

      <div className="navbar-status">
        <div className={`status-indicator ${isSuccess && health?.status === "healthy" ? "status-indicator--healthy" : "status-indicator--unknown"}`}>
          <span className="status-dot" />
          <span className="status-label">
            {isSuccess && health?.status === "healthy" ? "Backend · Online" : "Backend · Connecting"}
          </span>
        </div>
      </div>
    </header>
  );
}
