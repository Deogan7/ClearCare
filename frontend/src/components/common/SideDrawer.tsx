import { useEffect, useRef, type ReactNode } from "react";

interface SideDrawerProps {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  width?: number;
}

export default function SideDrawer({
  open,
  title,
  children,
  onClose,
  width = 460,
}: SideDrawerProps) {
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    panelRef.current?.focus();
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div className="drawer-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="drawer-panel card"
        style={{ width: `min(${width}px, 92vw)` }}
        onClick={(event) => event.stopPropagation()}
        ref={panelRef}
        tabIndex={-1}
      >
        <div className="card-header">
          <strong>{title}</strong>
          <button className="button ghost" onClick={onClose}>
            Close
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
