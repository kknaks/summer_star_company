"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { login } from "@/lib/api/auth";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(password);
      router.replace("/logs");
    } catch (err) {
      const ax = err as AxiosError<{ detail: string }>;
      setError(ax.response?.data?.detail ?? "로그인 실패");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex-1 flex items-center justify-center p-6">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm space-y-4 bg-white p-6 rounded-lg border border-neutral-200 shadow-sm"
      >
        <h1 className="text-xl font-semibold">관리자 로그인</h1>
        <Input
          type="password"
          placeholder="비밀번호"
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={submitting || !password} className="w-full">
          {submitting ? "..." : "로그인"}
        </Button>
      </form>
    </main>
  );
}
