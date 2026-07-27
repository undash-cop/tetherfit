import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss/40 disabled:pointer-events-none disabled:opacity-50 min-h-11 px-5",
  {
    variants: {
      variant: {
        primary: "bg-lime text-ink hover:brightness-105",
        secondary:
          "bg-forest text-sand hover:bg-moss dark:bg-mint dark:text-ink dark:hover:brightness-105",
        ghost: "bg-transparent text-forest hover:bg-sand/70 dark:text-sand dark:hover:bg-white/5",
        outline:
          "border border-forest/20 bg-white/60 text-forest backdrop-blur hover:bg-white dark:border-sand/20 dark:bg-white/5 dark:text-sand",
      },
      size: {
        default: "min-h-11 px-5",
        lg: "min-h-12 px-6 text-base",
        icon: "h-11 w-11 px-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
