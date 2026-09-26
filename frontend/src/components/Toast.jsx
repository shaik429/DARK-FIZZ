import { useEffect, useState } from "react";

// Shows any message sent with:  window.dispatchEvent(new CustomEvent("toast", { detail: { type, message } }))
// eslint-disable-next-line react-refresh/only-export-components
export function toast(message, type = "success") {
  window.dispatchEvent(new CustomEvent("toast", { detail: { type, message } }));
}

export default function ToastHost() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    const onToast = (e) => {
      const id = Date.now() + Math.random();
      setItems((list) => [...list.slice(-3), { id, ...e.detail }]);
      setTimeout(() => setItems((list) => list.filter((t) => t.id !== id)), 4500);
    };
    window.addEventListener("toast", onToast);
    return () => window.removeEventListener("toast", onToast);
  }, []);

  return (
    <div className="fixed right-4 bottom-4 z-50 flex w-80 flex-col gap-2">
      {items.map((t) => (
        <div
          key={t.id}
          role="alert"
          className={`rounded-xl px-4 py-3 text-sm font-medium shadow-lg ${
            t.type === "error" ? "bg-rose-600 text-white" : "bg-emerald-600 text-white"
          }`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
