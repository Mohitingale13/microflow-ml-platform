import { useLocation } from "react-router-dom";
import { useHealth } from "@/hooks/useHealth";

const routeLabels: Record<string, string> = {
  "/": "Dashboard",
  "/datasets": "Datasets",
  "/experiments": "Experiments",
  "/training": "Training",
  "/artifacts": "Artifacts",
  "/metrics": "Metrics",
  "/pipeline": "Pipeline",
};

export function Navbar() {
  const { pathname } = useLocation();
  const { data: health, isSuccess } = useHealth();
  const pageTitle = routeLabels[pathname] ?? "MicroFlow";

  return (
    <header className="navbar">
      <div className="navbar-title">
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
