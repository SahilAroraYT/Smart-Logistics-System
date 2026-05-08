"use client";

import { cn } from "@/lib/utils";

interface CheckboxProps {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export function Checkbox({ checked, onCheckedChange, disabled, className, id }: CheckboxProps) {
  return (
    <input
      type="checkbox"
      id={id}
      checked={checked}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
      disabled={disabled}
      className={cn(
        "h-4 w-4 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
    />
  );
}
