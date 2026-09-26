import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { masterApi, operationApi, productApi } from "../api";
import { toast } from "../components/Toast";
import { Badge, Button, Card, Field, Loading, Table, fmt, inputClass } from "../components/ui";

// ONE form for all 4 operation types. The type decides which fields appear.
const TYPES = {
  receipt: { label: "Receipt (incoming)", source: false, dest: true, partner: "supplier", qty: "Quantity received" },
  delivery: { label: "Delivery (outgoing)", source: true, dest: false, partner: "customer", qty: "Quantity to deliver" },
  internal: { label: "Internal transfer", source: true, dest: true, partner: null, qty: "Quantity to move" },
  adjustment: { label: "Stock adjustment", source: false, dest: true, partner: null, qty: "Counted quantity" },
};

export default function OperationFormPage() {
  const { id } = useParams();
  return id ? <OperationDetail id={id} /> : <NewOperation />;
}

function NewOperation() {
  const navigate = useNavigate();
  const [type, setType] = useState("receipt");
  const [locations, setLocations] = useState([]);
  const [partners, setPartners] = useState([]);
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({ source_location_id: "", dest_location_id: "", partner_id: "", scheduled_date: "" });
  const [lines, setLines] = useState([{ product_id: "", quantity: "" }]);
  const [saving, setSaving] = useState(false);
  const cfg = TYPES[type];

  useEffect(() => {
    masterApi.locations({ type: "internal" }).then(setLocations).catch(() => {});
    productApi.list().then(setProducts).catch(() => {});
  }, []);

  useEffect(() => {
    if (cfg.partner) masterApi.partners(cfg.partner).then(setPartners).catch(() => {});
  }, [cfg.partner]);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });
  const setLine = (i, key) => (e) => setLines(lines.map((l, j) => (j === i ? { ...l, [key]: e.target.value } : l)));

  async function save(e) {
    e.preventDefault();
    const filled = lines.filter((l) => l.product_id);
    if (!filled.length) return toast("Add at least one product.", "error");
    if (filled.some((l) => l.quantity === "" || Number(l.quantity) < 0 || (type !== "adjustment" && Number(l.quantity) <= 0)))
      return toast(type === "adjustment" ? "Counted quantity can't be negative." : "Quantity must be greater than zero.", "error");
    if (cfg.source && !form.source_location_id) return toast("Choose the source location.", "error");
    if (cfg.dest && !form.dest_location_id) return toast("Choose the destination location.", "error");
    if (type === "internal" && form.source_location_id === form.dest_location_id)
      return toast("Source and destination must be different.", "error");

    setSaving(true);
    try {
      const op = await operationApi.create({
        type,
        source_location_id: cfg.source ? Number(form.source_location_id) : null,
        dest_location_id: cfg.dest ? Number(form.dest_location_id) : null,
        partner_id: form.partner_id ? Number(form.partner_id) : null,
        scheduled_date: form.scheduled_date || null,
        lines: filled.map((l) => ({ product_id: Number(l.product_id), quantity: Number(l.quantity) })),
      });
      toast(`${op.reference} created as draft.`);
      navigate(`/operations/${op.id}`);
    } catch {
      /* message already shown */
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card title="New operation">
      <form onSubmit={save} className="space-y-5" noValidate>
        <div className="grid gap-4 md:grid-cols-3">
          <Field label="Type">
            <select
              className={inputClass}
              value={type}
              onChange={(e) => {
                setType(e.target.value);
                setPartners([]);
                setForm({ ...form, partner_id: "" });
              }}
            >
              {Object.entries(TYPES).map(([key, t]) => <option key={key} value={key}>{t.label}</option>)}
            </select>
          </Field>
          {cfg.source && (
            <Field label="From location">
              <select className={inputClass} value={form.source_location_id} onChange={set("source_location_id")}>
                <option value="">Choose…</option>
                {locations.map((l) => <option key={l.id} value={l.id}>{l.full_name}</option>)}
              </select>
            </Field>
          )}
          {cfg.dest && (
            <Field label={type === "adjustment" ? "Location counted" : "To location"}>
              <select className={inputClass} value={form.dest_location_id} onChange={set("dest_location_id")}>
                <option value="">Choose…</option>
                {locations.map((l) => <option key={l.id} value={l.id}>{l.full_name}</option>)}
              </select>
            </Field>
          )}
          {cfg.partner && (
            <Field label={cfg.partner === "supplier" ? "Supplier" : "Customer"}>
              <select className={inputClass} value={form.partner_id} onChange={set("partner_id")}>
                <option value="">None</option>
                {partners.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </Field>
          )}
          <Field label="Scheduled date">
            <input className={inputClass} type="date" value={form.scheduled_date} onChange={set("scheduled_date")} />
          </Field>
        </div>

        <div>
          <p className="mb-2 text-sm font-semibold text-slate-700">Products</p>
          <div className="space-y-2">
            {lines.map((line, i) => (
              <div key={i} className="flex gap-2">
                <select className={inputClass} value={line.product_id} onChange={setLine(i, "product_id")}>
                  <option value="">Choose product…</option>
                  {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name} ({fmt(p.on_hand)} {p.uom} on hand)</option>)}
                </select>
                <input
                  className={`${inputClass} w-40`}
                  type="number"
                  min="0"
                  step="any"
                  placeholder={cfg.qty}
                  value={line.quantity}
                  onChange={setLine(i, "quantity")}
                />
                {lines.length > 1 && (
                  <Button type="button" variant="secondary" onClick={() => setLines(lines.filter((_, j) => j !== i))}>✕</Button>
                )}
              </div>
            ))}
          </div>
          <button type="button" className="mt-2 text-sm font-semibold text-teal-700" onClick={() => setLines([...lines, { product_id: "", quantity: "" }])}>
            + Add product
          </button>
          {type === "adjustment" && (
            <p className="mt-2 text-xs text-slate-500">Enter what you physically counted. The system moves only the difference and logs it.</p>
          )}
        </div>

        <div className="flex gap-2">
          <Button disabled={saving}>{saving ? "Saving…" : "Create draft"}</Button>
          <Button type="button" variant="secondary" onClick={() => navigate("/operations")}>Cancel</Button>
        </div>
      </form>
    </Card>
  );
}

function OperationDetail({ id }) {
  const navigate = useNavigate();
  const [op, setOp] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    operationApi.get(id).then(setOp).catch(() => navigate("/operations"));
  }, [id, navigate]);

  async function act(action, message) {
    setBusy(true);
    try {
      const updated = await operationApi[action](id);
      setOp(updated);
      toast(message(updated));
    } catch {
      operationApi.get(id).then(setOp).catch(() => {});
    } finally {
      setBusy(false);
    }
  }

  if (!op) return <Loading />;
  const open = ["draft", "waiting", "ready"].includes(op.status);

  return (
    <Card
      title={
        <span className="flex items-center gap-3">
          <span className="font-mono">{op.reference}</span> <Badge value={op.status} />
        </span>
      }
      actions={
        <>
          {op.status === "draft" && (
            <Button variant="secondary" disabled={busy} onClick={() => act("confirm", (o) => `Marked ${o.status}.`)}>Confirm</Button>
          )}
          {open && (
            <Button disabled={busy} onClick={() => act("validate", () => "Validated. Stock updated.")}>Validate</Button>
          )}
          {open && (
            <Button variant="danger" disabled={busy} onClick={() => act("cancel", () => "Operation canceled.")}>Cancel</Button>
          )}
        </>
      }
    >
      <dl className="mb-5 grid gap-4 text-sm md:grid-cols-4">
        <div><dt className="text-slate-500">Type</dt><dd className="font-medium">{TYPES[op.type].label}</dd></div>
        <div><dt className="text-slate-500">From</dt><dd className="font-medium">{op.source_location}</dd></div>
        <div><dt className="text-slate-500">To</dt><dd className="font-medium">{op.dest_location}</dd></div>
        <div><dt className="text-slate-500">Partner</dt><dd className="font-medium">{op.partner || "—"}</dd></div>
      </dl>
      <Table
        rows={op.lines.map((l) => ({ ...l, id: l.product_id }))}
        columns={[
          { key: "sku", label: "SKU", render: (l) => <span className="font-mono text-xs">{l.sku}</span> },
          { key: "product", label: "Product" },
          { key: "quantity", label: TYPES[op.type].qty, render: (l) => `${fmt(l.quantity)} ${l.uom}` },
          ...(op.type !== "receipt" && open
            ? [{
                key: "available",
                label: op.type === "adjustment" ? "Recorded now" : "Available at source",
                render: (l) => (
                  <span className={op.type !== "adjustment" && l.available < l.quantity ? "font-semibold text-rose-600" : ""}>
                    {fmt(l.available ?? 0)} {l.uom}
                  </span>
                ),
              }]
            : []),
        ]}
      />
      <button className="mt-4 text-sm font-semibold text-teal-700" onClick={() => navigate("/operations")}>← Back to operations</button>
    </Card>
  );
}
