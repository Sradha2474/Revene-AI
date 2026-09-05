import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-full text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-45 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-zinc-200 text-zinc-950 shadow-[inset_0_-2px_0_rgba(0,0,0,0.2),inset_0_2px_0_rgba(255,255,255,0.25)] hover:bg-white active:scale-[0.97]",
        hero:
          "bg-white text-zinc-950 font-semibold shadow-[inset_0_-2px_0_rgba(0,0,0,0.2),inset_0_2px_0_rgba(255,255,255,0.4),0_0_24px_rgba(255,255,255,0.25)] hover:bg-zinc-100 hover:shadow-[0_0_32px_rgba(56,189,248,0.4)] active:scale-[0.96]",
        razorpay:
          "bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 text-white font-medium shadow-[0_0_25px_rgba(2,132,199,0.35),inset_0_1px_0_rgba(255,255,255,0.3)] hover:shadow-[0_0_35px_rgba(2,132,199,0.55)] border border-sky-400/30 active:scale-[0.97]",
        glass:
          "bg-white/[0.06] backdrop-blur-md border border-white/15 text-white hover:bg-white/[0.12] hover:border-white/30 active:scale-[0.98]",
        ghost: "rounded-md bg-transparent text-white/80 hover:bg-white/5 hover:text-white",
        outline:
          "rounded-md border border-[var(--color-line)] bg-transparent text-[var(--color-fg)] hover:bg-white/5 hover:border-white/20",
        danger: "rounded-md bg-[var(--color-policy-red)]/90 text-white hover:bg-[var(--color-policy-red)]",
        soft: "rounded-md bg-[var(--color-panel-2)] text-[var(--color-fg)] border border-[var(--color-line)] hover:border-white/20",
      },
      size: {
        default: "h-10 px-5",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-7 text-[15px]",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    );
  },
);
Button.displayName = "Button";
