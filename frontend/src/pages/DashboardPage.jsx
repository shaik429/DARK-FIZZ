import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { clean, dashboardApi, masterApi, operationApi } from "../api";
import { Badge, Card, Loading, Table, fmt, inputClass } from "../components/ui";

const KPIS = [
  ["total_products_in_stock", "Products in stock"],
  ["low_stock", "Low stock"],
  ["out_of_stock", "Out of stock"],
  ["pending_receipts", "Pending receipts"],
  ["pending_deliveries", "Pending deliveries"],
  ["internal_scheduled", "Transfers scheduled"],
];

export default function DashboardPage() {
  const [filters, setFilters] = useState({ warehouse_id: "", category_id: "", type: "", status: "" });
  const [kpis, setKpis] = useState(null);
  const [low, setLow] = useState([]);
  const [ops, setOps] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    masterApi.warehouses().then(setWarehouses).catch(() => {});
    masterApi.categories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    const { warehouse_id, category_id, type, status } = filters;
    dashboardApi.kpis(clean({ warehouse_id, category_id })).then(setKpis).catch(() => {});
    dashboardApi.lowStock(clean({ warehouse_id })).then(setLow).catch(() => {});
    operationApi.list(clean({ warehouse_id, type, status })).then((r) => setOps(r.slice(0, 8))).catch(() => {});
  }, [filters]);

  const set = (key) => (e) => setFilters({ ...filters, [key]: e.target.value });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3">
        <select className={`${inputClass} w-44`} value={filters.warehouse_id} onChange={set("warehouse_id")}>
          <option value="">All warehouses</option>
          {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
        <select className={`${inputClass} w-44`} value={filters.category_id} onChange={set("category_id")}>
          <option value="">All categories</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select className={`${inputClass} w-44`} value={filters.type} onChange={set("type")}>
          <option value="">All document types</option>
          <option value="receipt">Receipts</option>
          <option value="delivery">Deliveries</option>
          <option value="internal">Internal transfers</option>
          <option value="adjustment">Adjustments</option>
        </select>
        <select className={`${inputClass} w-40`} value={filters.status} onChange={set("status")}>
          <option value="">All statuses</option>
          {["draft", "waiting", "ready", "done", "canceled"].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {!kpis ? (
        <Loading />
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          {KPIS.map(([key, label]) => (
            <div key={key} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium text-slate-500">{label}</p>
              <p className={`mt-2 text-3xl font-bold ${key === "low_stock" && kpis[key] ? "text-amber-600" : key === "out_of_stock" && kpis[key] ? "text-rose-600" : ""}`}>
                {kpis[key]}
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Low stock alerts & reorder suggestions">
          <Table
            empty="All products are above their reorder minimum."
            rows={low.map((r) => ({ ...r, id: r.product_id }))}
            columns={[
              { key: "sku", label: "SKU" },
              { key: "product", label: "Product" },
              { key: "on_hand", label: "On hand", render: (r) => fmt(r.on_hand) },
              { key: "min_qty", label: "Min", render: (r) => fmt(r.min_qty) },
              { key: "suggested_order_qty", label: "Order", render: (r) => <b className="text-teal-700">{fmt(r.suggested_order_qty)}</b> },
            ]}
          />
        </Card>
        <Card title="Recent operations" actions={<Link className="text-sm font-semibold text-teal-700" to="/operations">View all →</Link>}>
          <Table
            empty="No operations match these filters."
            rows={ops}
            columns={[
              { key: "reference", label: "Reference", render: (o) => <Link className="font-medium text-teal-700" to={`/operations/${o.id}`}>{o.reference}</Link> },
              { key: "type", label: "Type", render: (o) => <span className="capitalize">{o.type}</span> },
              { key: "status", label: "Status", render: (o) => <Badge value={o.status} /> },
            ]}
          />
        </Card>
      </div>
    </div>
  );
}
