import { useStormMode } from "../../context/StormModeContext";

/**
 * CSS-only snowfall overlay. Rendered once at app root level.
 * Only visible when storm-active class is on <html>.
 */
export default function Snowfall() {
  const { isActive } = useStormMode();
  if (!isActive) return null;

  return (
    <div className="snowfall-container">
      {Array.from({ length: 20 }, (_, i) => (
        <div key={i} className="snowflake" />
      ))}
    </div>
  );
}
