// Small shared UI pieces.

const STATUS_COLORS = {
  draft: "bg-slate-100 text-slate-700",
  waiting: "bg-amber-100 text-amber-800",
  ready: "bg-sky-100 text-sky-800",
  done: "bg-emerald-100 text-emerald-800",
  canceled: "bg-rose-100 text-rose-700",
  ok: "bg-emerald-100 text-emerald-800",
  low: "bg-amber-100 text-amber-800",
  out: "bg-rose-100 text-rose-700",
};

export function Badge({ value }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${STATUS_COLORS[value] || "bg-slate-100"}`}>
      {value}
    </span>
  );
}

export function Card({ title, children, actions }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      {(title || actions) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          {title && <h3 className="text-lg font-semibold">{title}</h3>}
          <div className="flex gap-2">{actions}</div>
        </div>
      )}
      {children}
    </section>
  );
}

export function Field({ label, error, children }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-rose-600">{error}</span>}
    </label>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100";

export function Button({ variant = "primary", className = "", ...props }) {
  const styles = {
    primary: "bg-teal-600 text-white hover:bg-teal-700",
    secondary: "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
    danger: "bg-rose-600 text-white hover:bg-rose-700",
  };
  return (
    <button
      className={`rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`}
      {...props}
    />
  );
}

export function Table({ columns, rows, empty = "Nothing here yet.", onRowClick }) {
  if (!rows.length) return <p className="py-8 text-center text-sm text-slate-500">{empty}</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
          <tr>{columns.map((c) => <th key={c.key} className="px-3 py-2">{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={row.id ?? i}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`border-b border-slate-100 ${onRowClick ? "cursor-pointer hover:bg-slate-50" : ""}`}
            >
              {columns.map((c) => (
                <td key={c.key} className="px-3 py-2.5">{c.render ? c.render(row) : row[c.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Loading() {
  return <p className="py-8 text-center text-sm text-slate-500">Loading…</p>;
}

// eslint-disable-next-line react-refresh/only-export-components
export const fmt = (n) => Number(n).toLocaleString(undefined, { maximumFractionDigits: 3 });
