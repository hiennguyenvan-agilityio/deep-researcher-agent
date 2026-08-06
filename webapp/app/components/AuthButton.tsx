"use client";

import { useRef } from "react";
import { useAuth } from "@/app/components/AuthProvider";
import { AuthForm } from "@/app/components/AuthForm";

export function AuthButton() {
  const { user, loading, signOut } = useAuth();
  const dialogRef = useRef<HTMLDialogElement>(null);

  if (loading) return null;

  if (user) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <span>{user.email}</span>
        <button onClick={() => signOut()} className="text-neutral-900 underline underline-offset-2">
          Sign out
        </button>
      </div>
    );
  }

  return (
    <>
      <button
        onClick={() => dialogRef.current?.showModal()}
        className="rounded bg-black px-3 py-1.5 text-sm font-medium text-white"
      >
        Sign in
      </button>
      <dialog
        ref={dialogRef}
        className="fixed inset-0 m-auto rounded-lg bg-white p-6 shadow-xl backdrop:bg-black/40"
        onClick={(e) => {
          if (e.target === dialogRef.current) dialogRef.current?.close();
        }}
      >
        <AuthForm onClose={() => dialogRef.current?.close()} />
      </dialog>
    </>
  );
}
