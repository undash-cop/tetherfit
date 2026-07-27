import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "min-h-11 w-full rounded-xl border border-forest/15 bg-white px-3 text-sm text-ink outline-none ring-moss/30 placeholder:text-slate/60 focus:ring-2 dark:border-sand/15 dark:bg-white/5 dark:text-sand",
        className,
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-24 w-full rounded-xl border border-forest/15 bg-white px-3 py-2 text-sm text-ink outline-none ring-moss/30 placeholder:text-slate/60 focus:ring-2 dark:border-sand/15 dark:bg-white/5 dark:text-sand",
        className,
      )}
      {...props}
    />
  );
}

export function Label({
  className,
  ...props
}: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("mb-1 block text-sm font-medium text-slate dark:text-sand/70", className)}
      {...props}
    />
  );
}

export function Badge({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full bg-sand px-2.5 py-0.5 text-xs font-semibold text-forest dark:bg-white/10 dark:text-lime",
        className,
      )}
    >
      {children}
    </span>
  );
}
