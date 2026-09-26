import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { name: "Dashboard", path: "/" },
  { name: "Products", path: "/products" },
  { name: "Operations", path: "/operations" },
  { name: "Settings", path: "/settings" },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="pt-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight">
          Stock<span className="text-teal-600">Sense</span>
        </h1>
        <p className="mt-1 text-sm text-slate-500">Inventory Management System</p>

        <div className="mx-auto mt-6 flex w-fit flex-wrap items-center justify-center gap-3">
          <nav className="flex items-center gap-1 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
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
          <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm">
            <span className="font-medium">{user?.name}</span>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs capitalize text-slate-600">{user?.role}</span>
            <button
              className="rounded-lg px-2 py-1 text-rose-600 hover:bg-rose-50"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto mt-8 w-full max-w-7xl px-6 pb-12">
        <Outlet />
      </main>
    </div>
  );
}
