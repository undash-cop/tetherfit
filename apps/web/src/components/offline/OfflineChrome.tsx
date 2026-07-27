import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { flushQueue, readQueue } from "@/lib/offline";
import { getToken } from "@/lib/auth/keycloak";

export function OfflineBanner() {
  const [online, setOnline] = useState(
    typeof navigator === "undefined" ? true : navigator.onLine,
  );
  const [pending, setPending] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const refresh = () => {
      setOnline(navigator.onLine);
      setPending(readQueue().length);
    };
    refresh();
    window.addEventListener("online", refresh);
    window.addEventListener("offline", refresh);
    return () => {
      window.removeEventListener("online", refresh);
      window.removeEventListener("offline", refresh);
    };
  }, []);

  useEffect(() => {
    if (!online) return;
    void (async () => {
      setSyncing(true);
      await flushQueue(getToken);
      setPending(readQueue().length);
      setSyncing(false);
    })();
  }, [online]);

  if (online && pending === 0) return null;

  return (
    <div className="sticky top-14 z-30 mx-auto mb-3 max-w-lg rounded-2xl border border-forest/15 bg-sand/95 px-3 py-2 text-sm dark:border-sand/15 dark:bg-forest/95 md:max-w-3xl">
      {!online ? (
        <p className="font-medium text-ink dark:text-sand">
          You’re offline. Cached data stays available; changes queue for sync.
        </p>
      ) : (
        <div className="flex items-center justify-between gap-2">
          <p className="font-medium">
            {syncing ? "Syncing…" : `${pending} change(s) waiting to sync`}
          </p>
          <Button
            variant="outline"
            className="min-h-9 px-3"
            disabled={syncing}
            onClick={() => {
              setSyncing(true);
              void flushQueue(getToken).then(() => {
                setPending(readQueue().length);
                setSyncing(false);
              });
            }}
          >
            Sync now
          </Button>
        </div>
      )}
    </div>
  );
}

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

export function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (!deferred || hidden) return null;

  return (
    <div className="mb-3 flex items-center justify-between gap-2 rounded-2xl border border-lime/40 bg-forest px-3 py-2 text-sand">
      <p className="text-sm font-medium">Install TetherFit for offline access</p>
      <div className="flex gap-2">
        <Button
          variant="ghost"
          className="min-h-9 px-3 text-sand"
          onClick={() => setHidden(true)}
        >
          Later
        </Button>
        <Button
          className="min-h-9 px-3"
          onClick={() => {
            void deferred.prompt().then(() => setHidden(true));
          }}
        >
          Install
        </Button>
      </div>
    </div>
  );
}
