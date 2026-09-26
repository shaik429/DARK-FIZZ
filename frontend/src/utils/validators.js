// Client-side checks. The backend checks everything again - these just give faster feedback.

export const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim());

export const passwordProblem = (v) =>
  v.length < 8 || !/[A-Za-z]/.test(v) || !/\d/.test(v)
    ? "At least 8 characters with 1 letter and 1 number."
    : "";

export const isOtp = (v) => /^\d{6}$/.test(v);

export const positive = (v) => Number(v) > 0;

export function validate(rules) {
  const errors = {};
  for (const [field, [ok, message]] of Object.entries(rules)) {
    if (!ok) errors[field] = message;
  }
  return errors;
}
