interface TableEmptyStateProps {
  message?: string;
}

export default function TableEmptyState({ message = "No records yet." }: TableEmptyStateProps) {
  return <div className="table-empty">{message}</div>;
}
