"use client";

import { useState } from "react";
import { useAuth } from "@/app/components/AuthProvider";

export function AuthForm({ onClose }: { onClose?: () => void }) {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (mode === "signup" && password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setSubmitting(true);
    setError(null);

    const { error } = mode === "signin" ? await signIn(email, password) : await signUp(email, password);

    if (error) {
      setError(error);
      setSubmitting(false);
      return;
    }

    setSubmitting(false);
    onClose?.();
  };

  const inputClass =
    "rounded border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-900 outline-none focus:border-neutral-500";

  return (
    <form onSubmit={handleSubmit} className="flex w-72 flex-col gap-4">
      <h2 className="text-lg font-semibold text-neutral-900">
        {mode === "signin" ? "Sign in" : "Create an account"}
      </h2>
      <label className="flex flex-col gap-1 text-sm text-neutral-900">
        Email
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className={inputClass}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-neutral-900">
        Password
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={6}
          className={inputClass}
        />
      </label>
      {mode === "signup" && (
        <label className="flex flex-col gap-1 text-sm text-neutral-900">
          Confirm password
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={6}
            className={inputClass}
          />
        </label>
      )}
      {error && (
        <span role="alert" className="text-sm text-red-600">
          {error}
        </span>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-black px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {mode === "signin" ? "Sign in" : "Sign up"}
      </button>
      <button
        type="button"
        onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
        className="text-center text-sm text-neutral-900 underline underline-offset-2"
      >
        {mode === "signin" ? "Need an account? Sign up" : "Have an account? Sign in"}
      </button>
    </form>
  );
}
