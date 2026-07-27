import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";
import { useMe } from "@/hooks/useMe";

type Thread = { id: string; subject: string };
type Message = { id: string; body: string; sender_user_id: string; created_at: string };

export function ChatPage({ mode }: { mode: "trainer" | "client" }) {
  const me = useMe();
  const qc = useQueryClient();
  const [threadId, setThreadId] = useState<string | null>(null);
  const [text, setText] = useState("");

  const threads = useQuery({
    queryKey: ["chat-threads", mode],
    queryFn: () => apiFetch<Thread[]>("/api/v1/chat/threads", { token: getToken() }),
  });

  useEffect(() => {
    if (mode === "client" && !threadId) {
      void apiFetch<Thread>("/api/v1/chat/me/thread", {
        method: "POST",
        token: getToken(),
      }).then((t) => {
        setThreadId(t.id);
        void qc.invalidateQueries({ queryKey: ["chat-threads"] });
      });
    }
  }, [mode, threadId, qc]);

  useEffect(() => {
    if (mode === "trainer" && !threadId && threads.data?.[0]) {
      setThreadId(threads.data[0].id);
    }
  }, [mode, threadId, threads.data]);

  useEffect(() => {
    if (!threadId) return;
    const token = getToken();
    if (!token) return;
    const apiBase = import.meta.env.VITE_API_URL || window.location.origin;
    const wsBase = apiBase.replace(/^http/, "ws");
    const ws = new WebSocket(
      `${wsBase}/api/v1/ws/chat/${threadId}?token=${encodeURIComponent(token)}`,
    );
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data as string) as { type?: string };
        if (data.type === "message") {
          void qc.invalidateQueries({ queryKey: ["chat-messages", threadId] });
        }
      } catch {
        /* ignore */
      }
    };
    return () => ws.close();
  }, [threadId, qc]);

  const messages = useQuery({
    queryKey: ["chat-messages", threadId],
    queryFn: () =>
      apiFetch<Message[]>(`/api/v1/chat/threads/${threadId}/messages`, { token: getToken() }),
    enabled: Boolean(threadId),
    refetchInterval: 15000,
  });

  const send = useMutation({
    mutationFn: () =>
      apiFetch(`/api/v1/chat/threads/${threadId}/messages`, {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ body: text }),
      }),
    onSuccess: () => {
      setText("");
      void qc.invalidateQueries({ queryKey: ["chat-messages", threadId] });
    },
  });

  return (
    <section className="flex min-h-[70dvh] flex-col space-y-3">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Chat</h1>
      {mode === "trainer" && (
        <div className="flex gap-2 overflow-x-auto">
          {(threads.data ?? []).map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setThreadId(t.id)}
              className={`min-h-10 shrink-0 rounded-xl px-3 text-sm font-semibold ${
                threadId === t.id
                  ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                  : "bg-white/70 dark:bg-white/5"
              }`}
            >
              {t.subject}
            </button>
          ))}
        </div>
      )}
      <div className="flex-1 space-y-2 overflow-y-auto rounded-2xl border border-forest/10 p-3 dark:border-sand/10">
        {(messages.data ?? []).map((m) => {
          const mine = m.sender_user_id === me.data?.id;
          return (
            <div
              key={m.id}
              className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                mine
                  ? "ml-auto bg-forest text-sand dark:bg-lime dark:text-ink"
                  : "bg-white/80 dark:bg-white/10"
              }`}
            >
              {m.body}
            </div>
          );
        })}
        {!messages.data?.length && (
          <p className="text-sm text-slate dark:text-sand/60">No messages yet.</p>
        )}
      </div>
      <div className="flex gap-2">
        <Input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Write a message"
        />
        <Button disabled={!text || !threadId || send.isPending} onClick={() => send.mutate()}>
          Send
        </Button>
      </div>
    </section>
  );
}
