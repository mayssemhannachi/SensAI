// components/ui/Badge.tsx
export default function Badge({
  children,
  className = "bg-blue-100 text-blue-700",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-block rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider ${className}`}
    >
      {children}
    </span>
  );
}
