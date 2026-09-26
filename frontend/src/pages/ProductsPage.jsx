import { useCallback, useEffect, useState } from "react";
import { clean, masterApi, productApi } from "../api";
import { useAuth } from "../context/AuthContext";
import { toast } from "../components/Toast";
import { Badge, Button, Card, Field, Loading, Table, fmt, inputClass } from "../components/ui";

const EMPTY = { sku: "", name: "", category_id: "", uom_id: "", initial_qty: "", initial_location_id: "" };

export default function ProductsPage() {
  const { isManager } = useAuth();
  const [products, setProducts] = useState(null);
  const [q, setQ] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [categories, setCategories] = useState([]);
  const [uoms, setUoms] = useState([]);
  const [locations, setLocations] = useState([]);
  const [selected, setSelected] = useState(null);
  const [stock, setStock] = useState([]);
  const [form, setForm] = useState(null); // null = closed, {...} = create/edit
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    productApi.list(clean({ q, category_id: categoryId })).then(setProducts).catch(() => setProducts([]));
  }, [q, categoryId]);

  useEffect(() => {
    const t = setTimeout(load, 250); // debounce search
    return () => clearTimeout(t);
  }, [load]);

  useEffect(() => {
    masterApi.categories().then(setCategories).catch(() => {});
    masterApi.uoms().then(setUoms).catch(() => {});
    masterApi.locations({ type: "internal" }).then(setLocations).catch(() => {});
  }, []);

  function openStock(p) {
    setSelected(p);
    productApi.stock(p.id).then(setStock).catch(() => setStock([]));
  }

  async function save(e) {
    e.preventDefault();
    const editing = Boolean(form.id);
    if (!form.name.trim() || (!editing && !form.sku.trim()) || !form.category_id || !form.uom_id) {
      toast("SKU, name, category and unit are required.", "error");
      return;
    }
    if (form.initial_qty && Number(form.initial_qty) < 0) {
      toast("Initial stock can't be negative.", "error");
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await productApi.update(form.id, {
          name: form.name,
          category_id: Number(form.category_id),
          uom_id: Number(form.uom_id),
        });
        toast("Product updated.");
      } else {
        await productApi.create({
          sku: form.sku,
          name: form.name,
          category_id: Number(form.category_id),
          uom_id: Number(form.uom_id),
          initial_qty: form.initial_qty ? Number(form.initial_qty) : null,
          initial_location_id: form.initial_location_id ? Number(form.initial_location_id) : null,
        });
        toast("Product created.");
      }
      setForm(null);
      load();
    } catch {
      /* message already shown */
    } finally {
      setSaving(false);
    }
  }

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <Card
          title="Products"
          actions={isManager && <Button onClick={() => setForm(EMPTY)}>+ New product</Button>}
        >
          <div className="mb-4 flex gap-3">
            <input className={inputClass} placeholder="Search by SKU or name…" value={q} onChange={(e) => setQ(e.target.value)} />
            <select className={`${inputClass} w-48`} value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">All categories</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          {!products ? (
            <Loading />
          ) : (
            <Table
              rows={products}
              empty="No products match your search."
              onRowClick={openStock}
              columns={[
                { key: "sku", label: "SKU", render: (p) => <span className="font-mono text-xs">{p.sku}</span> },
                { key: "name", label: "Name" },
                { key: "category", label: "Category" },
                { key: "on_hand", label: "On hand", render: (p) => `${fmt(p.on_hand)} ${p.uom}` },
                { key: "stock_status", label: "Stock", render: (p) => <Badge value={p.stock_status} /> },
                ...(isManager
                  ? [{
                      key: "edit",
                      label: "",
                      render: (p) => (
                        <button
                          className="text-xs font-semibold text-teal-700"
                          onClick={(e) => {
                            e.stopPropagation();
                            setForm({ ...EMPTY, ...p });
                          }}
                        >
                          Edit
                        </button>
                      ),
                    }]
                  : []),
              ]}
            />
          )}
        </Card>
      </div>

      <div className="space-y-6">
        {form && (
          <Card title={form.id ? `Edit ${form.sku}` : "New product"}>
            <form onSubmit={save} className="space-y-3" noValidate>
              {!form.id && (
                <Field label="SKU / Code">
                  <input className={inputClass} value={form.sku} onChange={set("sku")} />
                </Field>
              )}
              <Field label="Name">
                <input className={inputClass} value={form.name} onChange={set("name")} />
              </Field>
              <Field label="Category">
                <select className={inputClass} value={form.category_id} onChange={set("category_id")}>
                  <option value="">Choose…</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </Field>
              <Field label="Unit of measure">
                <select className={inputClass} value={form.uom_id} onChange={set("uom_id")}>
                  <option value="">Choose…</option>
                  {uoms.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
                </select>
              </Field>
              {!form.id && (
                <>
                  <Field label="Initial stock (optional)">
                    <input className={inputClass} type="number" min="0" value={form.initial_qty} onChange={set("initial_qty")} />
                  </Field>
                  {form.initial_qty && (
                    <Field label="Initial stock location">
                      <select className={inputClass} value={form.initial_location_id} onChange={set("initial_location_id")}>
                        <option value="">Choose…</option>
                        {locations.map((l) => <option key={l.id} value={l.id}>{l.full_name}</option>)}
                      </select>
                    </Field>
                  )}
                </>
              )}
              <div className="flex gap-2 pt-2">
                <Button disabled={saving}>{saving ? "Saving…" : "Save"}</Button>
                <Button type="button" variant="secondary" onClick={() => setForm(null)}>Cancel</Button>
              </div>
            </form>
          </Card>
        )}

        <Card title={selected ? `Stock: ${selected.name}` : "Stock by location"}>
          {!selected ? (
            <p className="text-sm text-slate-500">Click a product to see where its stock is.</p>
          ) : (
            <Table
              rows={stock.map((s) => ({ ...s, id: s.location_id }))}
              empty="No stock at any location yet."
              columns={[
                { key: "location", label: "Location" },
                { key: "quantity", label: "Quantity", render: (s) => `${fmt(s.quantity)} ${selected.uom}` },
              ]}
            />
          )}
        </Card>
      </div>
    </div>
  );
}
