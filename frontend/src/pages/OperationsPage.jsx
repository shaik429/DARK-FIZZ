import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { clean, operationApi } from "../api";
import { Badge, Button, Card, Loading, Table, fmt, inputClass } from "../components/ui";

const TABS = [
  ["", "All"],
  ["receipt", "Receipts"],
  ["delivery", "Deliveries"],
  ["internal", "Internal"],
  ["adjustment", "Adjustments"],
  ["history", "Move history"],
];

export default function OperationsPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("");
  const [status, setStatus] = useState("");
  const [rows, setRows] = useState(null);

  function changeTab(next) {
    setRows(null);
    setTab(next);
  }

  function changeStatus(next) {
    setRows(null);
    setStatus(next);
  }

  useEffect(() => {
    const request =
      tab === "history" ? operationApi.moves({ limit: 200 }) : operationApi.list(clean({ type: tab, status }));
    request.then(setRows).catch(() => setRows([]));
  }, [tab, status]);

  const opColumns = [
    { key: "reference", label: "Reference", render: (o) => <span className="font-mono text-xs font-semibold">{o.reference}</span> },
    { key: "type", label: "Type", render: (o) => <span className="capitalize">{o.type}</span> },
    { key: "from", label: "From", render: (o) => o.source_location },
    { key: "to", label: "To", render: (o) => o.dest_location },
    { key: "partner", label: "Partner", render: (o) => o.partner || "—" },
    { key: "status", label: "Status", render: (o) => <Badge value={o.status} /> },
  ];

  const moveColumns = [
    { key: "done_at", label: "Date", render: (m) => new Date(m.done_at + "Z").toLocaleString() },
    { key: "reference", label: "Reference", render: (m) => <span className="font-mono text-xs">{m.reference}</span> },
    { key: "product", label: "Product" },
    { key: "from_location", label: "From" },
    { key: "to_location", label: "To" },
    { key: "quantity", label: "Qty", render: (m) => fmt(m.quantity) },
    { key: "done_by", label: "By" },
  ];

  return (
    <Card title="Operations" actions={<Button onClick={() => navigate("/operations/new")}>+ New operation</Button>}>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {TABS.map(([key, label]) => (
          <button
            key={key}
            onClick={() => changeTab(key)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium ${tab === key ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}
          >
            {label}
          </button>
        ))}
        {tab !== "history" && (
          <select className={`${inputClass} ml-auto w-40`} value={status} onChange={(e) => changeStatus(e.target.value)}>
            <option value="">All statuses</option>
            {["draft", "waiting", "ready", "done", "canceled"].map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        )}
      </div>
      {!rows ? (
        <Loading />
      ) : tab === "history" ? (
        <Table rows={rows} columns={moveColumns} empty="No stock has moved yet. Validate an operation to see the ledger." />
      ) : (
        <Table
          rows={rows}
          columns={opColumns}
          onRowClick={(o) => navigate(`/operations/${o.id}`)}
          empty={<span>No operations yet. <Link className="text-teal-700" to="/operations/new">Create one</Link>.</span>}
        />
      )}
    </Card>
  );
}
