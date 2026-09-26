import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { name: "Dashboard", path: "/" },
  { name: "Products", path: "/products" },
  { name: "Operations", path: "/operations" },
  { name: "Settings", path: "/settings" },
];

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="pt-10 text-center">
        <h1 className="text-4xl font-bold tracking-tight">
          Stock<span className="text-teal-600">Stack</span>
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          Inventory Management System
        </p>

        <nav className="mx-auto mt-8 flex w-fit items-center gap-1 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `rounded-xl px-5 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-gradient-to-r from-teal-600 to-blue-600 text-white shadow-sm"
                    : "text-slate-600 hover:bg-sky-50 hover:text-teal-700"
                }`
              }
            >
              {item.name}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto mt-10 w-full max-w-7xl px-6 pb-12">
        <Outlet />
      </main>
    </div>
  );
}