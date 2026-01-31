import type { ReactNode } from "react";

interface DrawerProps {
  open: boolean;
  title?: string;
  children: ReactNode;
  onClose: () => void;
}

export default function Drawer({ open, title, children, onClose }: DrawerProps) {
  if (!open) return null;

  return (
    <div className="drawer-overlay" role="dialog" aria-modal="true">
      <div className="drawer-panel card">
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
