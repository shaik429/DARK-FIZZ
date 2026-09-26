import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { authApi } from "../api";
import { useAuth } from "../context/AuthContext";
import { toast } from "../components/Toast";
import { Button, Field, inputClass } from "../components/ui";
import { isEmail, isOtp, passwordProblem, validate } from "../utils/validators";

const TABS = { login: "Log in", signup: "Sign up", forgot: "Forgot password" };

export default function AuthPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [otpSent, setOtpSent] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", otp: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  function switchMode(next) {
    setMode(next);
    setErrors({});
    setOtpSent(false);
  }

  async function submit(e) {
    e.preventDefault();
    const pw = passwordProblem(form.password);
    const rules = {
      email: [isEmail(form.email), "Enter a valid email address."],
      ...(mode === "signup" && { name: [form.name.trim() !== "", "Name is required."], password: [!pw, pw] }),
      ...(mode === "login" && { password: [form.password !== "", "Password is required."] }),
      ...(mode === "forgot" && otpSent && { otp: [isOtp(form.otp), "Enter the 6-digit code."], password: [!pw, pw] }),
    };
    const found = validate(rules);
    setErrors(found);
    if (Object.keys(found).length) return;

    setLoading(true);
    try {
      if (mode === "login") {
        await login(form.email, form.password);
        navigate("/");
      } else if (mode === "signup") {
        await authApi.signup({ name: form.name, email: form.email, password: form.password });
        toast("Account created. You can log in now.");
        switchMode("login");
      } else if (!otpSent) {
        const res = await authApi.forgotPassword(form.email);
        toast(res.message);
        setOtpSent(true);
      } else {
        const res = await authApi.resetPassword({ email: form.email, otp: form.otp, new_password: form.password });
        toast(res.message);
        switchMode("login");
      }
    } catch (err) {
      // The toast already shows the server's message; also show field errors if any.
      const fieldErrors = {};
      (err.details || []).forEach((d) => (fieldErrors[d.field] = d.message));
      setErrors(fieldErrors);
    } finally {
      setLoading(false);
    }
  }

  const button = { login: "Log in", signup: "Create account", forgot: otpSent ? "Reset password" : "Send code" }[mode];

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-teal-50 p-6">
      <div className="w-full max-w-md">
        <h1 className="text-center text-4xl font-bold tracking-tight">
          Stock<span className="text-teal-600">Sense</span>
        </h1>
        <p className="mt-1 text-center text-sm text-slate-500">Inventory Management System</p>

        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-6 flex gap-1 rounded-xl bg-slate-100 p-1">
            {Object.entries(TABS).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => switchMode(key)}
                className={`flex-1 rounded-lg py-2 text-xs font-semibold ${mode === key ? "bg-white shadow-sm" : "text-slate-500"}`}
              >
                {label}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-4" noValidate>
            {mode === "signup" && (
              <Field label="Name" error={errors.name}>
                <input className={inputClass} value={form.name} onChange={set("name")} />
              </Field>
            )}
            <Field label="Email" error={errors.email}>
              <input className={inputClass} type="email" value={form.email} onChange={set("email")} disabled={otpSent} />
            </Field>
            {mode === "forgot" && otpSent && (
              <Field label="6-digit code from your email" error={errors.otp}>
                <input className={inputClass} inputMode="numeric" maxLength={6} value={form.otp} onChange={set("otp")} />
              </Field>
            )}
            {(mode !== "forgot" || otpSent) && (
              <Field label={mode === "forgot" ? "New password" : "Password"} error={errors.password || errors.new_password}>
                <input className={inputClass} type="password" value={form.password} onChange={set("password")} />
              </Field>
            )}
            <Button className="w-full" disabled={loading}>
              {loading ? "Please wait…" : button}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
