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
  getWellnessChecks,
  getDriverNotifications,
} from "../services/weatherService";
import type {
  StormModeStatus,
  WellnessCheckSummary,
  DriverNotificationSummary,
} from "../types/weather";

interface StormModeContextType {
  isActive: boolean;
  status: StormModeStatus | null;
  loading: boolean;
  wellnessSummary: WellnessCheckSummary | null;
  driverNotifications: DriverNotificationSummary | null;
  activate: (windowHours?: number) => Promise<number>;
  deactivate: () => Promise<void>;
  refresh: () => Promise<void>;
  refreshWellness: () => Promise<void>;
}

const StormModeContext = createContext<StormModeContextType | null>(null);

export function StormModeProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<StormModeStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [wellnessSummary, setWellnessSummary] =
    useState<WellnessCheckSummary | null>(null);
  const [driverNotifications, setDriverNotifications] =
    useState<DriverNotificationSummary | null>(null);

  const refresh = useCallback(async () => {
    try {
      const data = await getStormModeStatus();
      setStatus(data);
    } catch {
      // Silently fail — storm mode status is non-critical
    }
  }, []);

  const refreshWellness = useCallback(async () => {
    if (!status?.is_active) {
      setWellnessSummary(null);
      setDriverNotifications(null);
      return;
    }
    try {
      const [wc, dn] = await Promise.allSettled([
        getWellnessChecks(),
        getDriverNotifications(),
      ]);
      if (wc.status === "fulfilled") setWellnessSummary(wc.value);
      if (dn.status === "fulfilled") setDriverNotifications(dn.value);
    } catch {
      // Non-critical
    }
  }, [status?.is_active]);

  // Poll storm mode status every 30s
  useEffect(() => {
    void refresh();
    const interval = setInterval(() => void refresh(), 30_000);
    return () => clearInterval(interval);
  }, [refresh]);

  // Poll wellness data every 10s when storm mode is active
  useEffect(() => {
    if (status?.is_active) {
      void refreshWellness();
      const interval = setInterval(() => void refreshWellness(), 10_000);
      return () => clearInterval(interval);
    } else {
      setWellnessSummary(null);
      setDriverNotifications(null);
    }
  }, [status?.is_active, refreshWellness]);

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
      // Start polling wellness data after a short delay
      setTimeout(() => void refreshWellness(), 5_000);
      return result.converted_count;
    } finally {
      setLoading(false);
    }
  }, [refresh, refreshWellness]);

  const deactivate = useCallback(async () => {
    setLoading(true);
    try {
      await apiDeactivate();
      await refresh();
      setWellnessSummary(null);
      setDriverNotifications(null);
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  const isActive = status?.is_active ?? false;

  return (
    <StormModeContext.Provider
      value={{
        isActive,
        status,
        loading,
        wellnessSummary,
        driverNotifications,
        activate,
        deactivate,
        refresh,
        refreshWellness,
      }}
    >
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
