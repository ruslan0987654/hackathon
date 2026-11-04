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
  const [searchQuery, setSearchQuery] = useState("");

  const renderPage = () => {
    switch (activePage) {
      case "wells": return <Wells searchQuery={searchQuery} onSearchChange={setSearchQuery} />;
      case "analytics": return <Analytics searchQuery={searchQuery} />;
      case "insights": return <Insights searchQuery={searchQuery} />;
      case "alerts": return <Alerts searchQuery={searchQuery} onSearchChange={setSearchQuery} />;
      default: return <Dashboard searchQuery={searchQuery} onNavigate={setActivePage} />;
    }
  };

  return (
    <div className="app-shell" data-theme={isLightMode ? "light" : "dark"}>
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <main className="main-content">
        <Header
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onSearchSubmit={() => setActivePage("wells")}
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