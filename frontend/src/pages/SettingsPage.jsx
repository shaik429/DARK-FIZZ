import { useEffect, useState } from "react";
import { masterApi, productApi } from "../api";
import { useAuth } from "../context/AuthContext";
import { toast } from "../components/Toast";
import { Button, Card, Field, Table, fmt, inputClass } from "../components/ui";

export default function SettingsPage() {
  const { user, isManager } = useAuth();
  const [warehouses, setWarehouses] = useState([]);
  const [locations, setLocations] = useState([]);
  const [rules, setRules] = useState([]);
  const [products, setProducts] = useState([]);
  const [wh, setWh] = useState({ name: "", code: "" });
  const [loc, setLoc] = useState({ name: "", warehouse_id: "" });
  const [rule, setRule] = useState({ product_id: "", warehouse_id: "", min_qty: "", max_qty: "" });

  const load = () => {
    masterApi.warehouses().then(setWarehouses).catch(() => {});
    masterApi.locations().then(setLocations).catch(() => {});
    masterApi.reorderRules().then(setRules).catch(() => {});
  };
  useEffect(() => {
    load();
    productApi.list().then(setProducts).catch(() => {});
  }, []);

  async function submit(e, action, message, reset) {
    e.preventDefault();
    try {
      await action();
      toast(message);
      reset();
      load();
    } catch {
      /* message already shown */
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title="My profile">
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <dt className="text-slate-500">Name</dt><dd className="font-medium">{user?.name}</dd>
          <dt className="text-slate-500">Email</dt><dd className="font-medium">{user?.email}</dd>
          <dt className="text-slate-500">Role</dt><dd className="font-medium capitalize">{user?.role}</dd>
        </dl>
      </Card>

      <Card title="Warehouses">
        <Table rows={warehouses} columns={[{ key: "code", label: "Code" }, { key: "name", label: "Name" }]} />
        {isManager && (
          <form
            className="mt-4 flex items-end gap-2"
            noValidate
            onSubmit={(e) => {
              if (!wh.name.trim() || !/^[A-Za-z0-9]{1,10}$/.test(wh.code)) {
                e.preventDefault();
                return toast("Enter a name and a short code (letters/numbers, max 10).", "error");
              }
              submit(e, () => masterApi.createWarehouse(wh), "Warehouse added.", () => setWh({ name: "", code: "" }));
            }}
          >
            <Field label="Name"><input className={inputClass} value={wh.name} onChange={(e) => setWh({ ...wh, name: e.target.value })} /></Field>
            <Field label="Code"><input className={`${inputClass} w-24`} value={wh.code} onChange={(e) => setWh({ ...wh, code: e.target.value })} /></Field>
            <Button>Add</Button>
          </form>
        )}
      </Card>

      <Card title="Locations">
        <Table
          rows={locations}
          columns={[
            { key: "full_name", label: "Location" },
            { key: "type", label: "Type", render: (l) => <span className="capitalize">{l.type}</span> },
          ]}
        />
        {isManager && (
          <form
            className="mt-4 flex items-end gap-2"
            noValidate
            onSubmit={(e) => {
              if (!loc.name.trim() || !loc.warehouse_id) {
                e.preventDefault();
                return toast("Choose a warehouse and enter a location name.", "error");
              }
              submit(e, () => masterApi.createLocation({ ...loc, warehouse_id: Number(loc.warehouse_id) }), "Location added.", () => setLoc({ name: "", warehouse_id: "" }));
            }}
          >
            <Field label="Warehouse">
              <select className={inputClass} value={loc.warehouse_id} onChange={(e) => setLoc({ ...loc, warehouse_id: e.target.value })}>
                <option value="">Choose…</option>
                {warehouses.map((w) => <option key={w.id} value={w.id}>{w.code}</option>)}
              </select>
            </Field>
            <Field label="Name"><input className={inputClass} value={loc.name} onChange={(e) => setLoc({ ...loc, name: e.target.value })} /></Field>
            <Button>Add</Button>
          </form>
        )}
      </Card>

      <Card title="Reordering rules">
        <Table
          rows={rules}
          empty="No reordering rules yet."
          columns={[
            { key: "product", label: "Product" },
            { key: "warehouse", label: "Warehouse" },
            { key: "min_qty", label: "Min", render: (r) => fmt(r.min_qty) },
            { key: "max_qty", label: "Max", render: (r) => fmt(r.max_qty) },
          ]}
        />
        {isManager && (
          <form
            className="mt-4 grid grid-cols-2 gap-2"
            noValidate
            onSubmit={(e) => {
              const min = Number(rule.min_qty), max = Number(rule.max_qty);
              if (!rule.product_id || !rule.warehouse_id || rule.min_qty === "" || rule.max_qty === "" || min < 0 || min > max) {
                e.preventDefault();
                return toast("Choose product and warehouse; 0 ≤ min ≤ max.", "error");
              }
              submit(
                e,
                () => masterApi.saveReorderRule({ product_id: Number(rule.product_id), warehouse_id: Number(rule.warehouse_id), min_qty: min, max_qty: max }),
                "Reordering rule saved.",
                () => setRule({ product_id: "", warehouse_id: "", min_qty: "", max_qty: "" })
              );
            }}
          >
            <select className={inputClass} value={rule.product_id} onChange={(e) => setRule({ ...rule, product_id: e.target.value })}>
              <option value="">Product…</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
            </select>
            <select className={inputClass} value={rule.warehouse_id} onChange={(e) => setRule({ ...rule, warehouse_id: e.target.value })}>
              <option value="">Warehouse…</option>
              {warehouses.map((w) => <option key={w.id} value={w.id}>{w.code}</option>)}
            </select>
            <input className={inputClass} type="number" min="0" placeholder="Min qty" value={rule.min_qty} onChange={(e) => setRule({ ...rule, min_qty: e.target.value })} />
            <input className={inputClass} type="number" min="0" placeholder="Max qty" value={rule.max_qty} onChange={(e) => setRule({ ...rule, max_qty: e.target.value })} />
            <Button className="col-span-2">Save rule</Button>
          </form>
        )}
      </Card>
    </div>
  );
}
