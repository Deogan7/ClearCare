import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  action?: ReactNode;
}

export default function Card({ title, action, children, className = "", ...rest }: CardProps) {
  return (
    <div className={`card ${className}`.trim()} {...rest}>
      {title ? (
        <div className="card-header">
          <strong>{title}</strong>
          {action}
        </div>
      ) : null}
      {children}
    </div>
  );
}
