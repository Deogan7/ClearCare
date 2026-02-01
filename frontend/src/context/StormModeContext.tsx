import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  getStormModeStatus,
  activateStormMode as apiActivate,
  deactivateStormMode as apiDeactivate,
} from "../services/weatherService";
import type { StormModeStatus } from "../types/weather";

interface StormModeContextType {
  isActive: boolean;
  status: StormModeStatus | null;
  loading: boolean;
  activate: (windowHours?: number) => Promise<number>;
  deactivate: () => Promise<void>;
  refresh: () => Promise<void>;
}

const StormModeContext = createContext<StormModeContextType | null>(null);

export function StormModeProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<StormModeStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const data = await getStormModeStatus();
      setStatus(data);
    } catch {
      // Silently fail — storm mode status is non-critical
    }
  }, []);

  useEffect(() => {
    void refresh();
    const interval = setInterval(() => void refresh(), 30_000);
    return () => clearInterval(interval);
  }, [refresh]);

  // Apply/remove the storm-active class on <html> for the dark theme
  useEffect(() => {
    const html = document.documentElement;
    if (status?.is_active) {
      html.classList.add("storm-active");
    } else {
      html.classList.remove("storm-active");
    }
    return () => html.classList.remove("storm-active");
  }, [status?.is_active]);

  const activate = useCallback(async (windowHours = 48) => {
    setLoading(true);
    try {
      const result = await apiActivate("manual", windowHours);
      await refresh();
      return result.converted_count;
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  const deactivate = useCallback(async () => {
    setLoading(true);
    try {
      await apiDeactivate();
      await refresh();
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  const isActive = status?.is_active ?? false;

  return (
    <StormModeContext.Provider value={{ isActive, status, loading, activate, deactivate, refresh }}>
      {children}
    </StormModeContext.Provider>
  );
}

export function useStormMode() {
  const context = useContext(StormModeContext);
  if (!context) {
    throw new Error("useStormMode must be used within StormModeProvider");
  }
  return context;
}
