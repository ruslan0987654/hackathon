import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Dashboard from "./pages/Dashboard";
import Wells from "./pages/Wells";
import Analytics from "./pages/Analytics";
import Insights from "./pages/Insights";
import Alerts from "./pages/Alerts";
import type { PageKey } from "./types";

export default function App() {
  const [activePage, setActivePage] = useState<PageKey>("dashboard");
  const [dateRange, setDateRange] = useState("30");
  const [isLightMode, setIsLightMode] = useState(false);

  const renderPage = () => {
    switch (activePage) {
      case "wells": return <Wells />;
      case "analytics": return <Analytics />;
      case "insights": return <Insights />;
      case "alerts": return <Alerts />;
      default: return <Dashboard onNavigate={setActivePage} />;
    }
  };

  return (
    <div className="app-shell" data-theme={isLightMode ? "light" : "dark"}>
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <main className="main-content">
        <Header
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
          isLightMode={isLightMode}
          onToggleTheme={() => setIsLightMode((current) => !current)}
        />
        <div className="page-content">{renderPage()}</div>
        <footer className="app-footer"><span>© 2026 SOCAR Smart Analytics</span><span>Demo interfeys · Real data ilə inteqrasiya üçün hazır struktur</span></footer>
      </main>
    </div>
  );
}