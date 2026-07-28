import { getToken } from "@/lib/auth/keycloak";

const API_URL = import.meta.env.VITE_API_URL ?? "";

/** Open printable GST invoice HTML in a new tab (auth required; not payment-gated). */
export async function openGstInvoice(invoiceId: string): Promise<void> {
  if (!API_URL) {
    throw new Error("VITE_API_URL is not configured");
  }

  // Open synchronously so popup blockers don't swallow the tab after await.
  const win = window.open("about:blank", "_blank");
  if (!win) {
    throw new Error("Popup blocked — allow popups for this site to view invoices");
  }
  win.document.write("<p style='font-family:sans-serif;padding:1.5rem'>Loading GST invoice…</p>");

  try {
    const res = await fetch(`${API_URL}/api/v1/invoices/${invoiceId}/gst-invoice`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    const body = await res.text();
    if (!res.ok) {
      win.document.open();
      win.document.write(
        `<pre style="font-family:sans-serif;padding:1.5rem;white-space:pre-wrap">Could not load GST invoice (${res.status}).\n${body}</pre>`,
      );
      win.document.close();
      return;
    }
    win.document.open();
    win.document.write(body);
    win.document.close();
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    win.document.open();
    win.document.write(
      `<pre style="font-family:sans-serif;padding:1.5rem;white-space:pre-wrap">Could not load GST invoice.\n${message}</pre>`,
    );
    win.document.close();
  }
}
