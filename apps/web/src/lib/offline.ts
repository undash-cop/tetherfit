const CACHE_PREFIX = "tetherfit:offline:";
const QUEUE_KEY = `${CACHE_PREFIX}queue`;

export type OfflineQueuedMutation = {
  id: string;
  url: string;
  method: string;
  body?: string;
  createdAt: string;
};

export function cacheJson(key: string, value: unknown) {
  try {
    localStorage.setItem(`${CACHE_PREFIX}${key}`, JSON.stringify({ at: Date.now(), value }));
  } catch {
    /* quota */
  }
}

export function readCachedJson<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(`${CACHE_PREFIX}${key}`);
    if (!raw) return null;
    return (JSON.parse(raw) as { value: T }).value;
  } catch {
    return null;
  }
}

export function enqueueMutation(item: Omit<OfflineQueuedMutation, "id" | "createdAt">) {
  const queue = readQueue();
  queue.push({
    ...item,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
  });
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

export function readQueue(): OfflineQueuedMutation[] {
  try {
    return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]") as OfflineQueuedMutation[];
  } catch {
    return [];
  }
}

export function clearQueue() {
  localStorage.setItem(QUEUE_KEY, "[]");
}

export async function flushQueue(getToken: () => string | undefined) {
  if (!navigator.onLine) return { flushed: 0 };
  const queue = readQueue();
  if (!queue.length) return { flushed: 0 };
  let flushed = 0;
  const remaining: OfflineQueuedMutation[] = [];
  for (const item of queue) {
    try {
      const token = getToken();
      const res = await fetch(item.url, {
        method: item.method,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: item.body,
      });
      if (res.ok) flushed += 1;
      else remaining.push(item);
    } catch {
      remaining.push(item);
    }
  }
  localStorage.setItem(QUEUE_KEY, JSON.stringify(remaining));
  return { flushed, remaining: remaining.length };
}
