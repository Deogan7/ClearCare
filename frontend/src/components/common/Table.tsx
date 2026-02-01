import type { ReactNode } from "react";
import TableEmptyState from "./TableEmptyState";

interface TableProps {
  headers?: string[];
  children?: ReactNode;
  emptyMessage?: string;
}

export default function Table({ headers, children, emptyMessage }: TableProps) {
  const hasRows = Boolean(children);
  const hasHeaders = Array.isArray(headers) && headers.length > 0;

  return (
    <div>
      <table className="table">
        {hasHeaders ? (
          <thead>
            <tr>
              {headers.map((header) => (
                <th key={header}>{header}</th>
              ))}
            </tr>
          </thead>
        ) : null}
        <tbody>{children}</tbody>
      </table>
      {!hasRows ? <TableEmptyState message={emptyMessage} /> : null}
    </div>
  );
}
