type LoadingProps = { label?: string };

export function Loading({ label = "正在加载…" }: LoadingProps) {
  return <div className="pf-loading" role="status" aria-live="polite"><span aria-hidden="true" />{label}</div>;
}
