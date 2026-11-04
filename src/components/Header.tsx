import { Bell, ChevronDown, MoonStar, Search, SunMedium } from "lucide-react";
import { useEffect, useRef } from "react";

interface HeaderProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onSearchSubmit: () => void;
  dateRange: string;
  onDateRangeChange: (value: string) => void;
  isLightMode: boolean;
  onToggleTheme: () => void;
}

export default function Header({
  searchQuery,
  onSearchChange,
  onSearchSubmit,
  dateRange,
  onDateRangeChange,
  isLightMode,
  onToggleTheme,
}: HeaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <header className="topbar">
      <label className="global-search">
        <Search size={17} />
        <input
          ref={inputRef}
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              onSearchSubmit();
            }
          }}
          placeholder="Quyu, region və ya göstərici axtar..."
        />
        <kbd>Ctrl K</kbd>
      </label>
      <div className="topbar-actions">
        <label className="date-select">
          <span>◷</span>
          <select value={dateRange} onChange={(e) => onDateRangeChange(e.target.value)}>
            <option value="7">Son 7 gün</option>
            <option value="30">Son 30 gün</option>
            <option value="90">Son 90 gün</option>
          </select>
          <ChevronDown size={14} />
        </label>
        <button className="icon-button theme-toggle" aria-label={isLightMode ? "Dark mode" : "Light mode"} onClick={onToggleTheme}>
          {isLightMode ? <MoonStar size={18} /> : <SunMedium size={18} />}
        </button>
        <button className="icon-button notification-button" aria-label="Bildirişlər"><Bell size={18} /><i /></button>
      </div>
    </header>
  );
}