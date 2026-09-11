type EmptyStateProps = { title: string; description?: string };

export function EmptyState({ title, description }: EmptyStateProps) {
  return <div className="pf-empty-state"><strong>{title}</strong>{description ? <p>{description}</p> : null}</div>;
}
