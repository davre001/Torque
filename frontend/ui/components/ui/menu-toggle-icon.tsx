'use client';
import * as React from 'react';
import { cn } from '@/lib/utils';

export interface MenuToggleIconProps extends React.ComponentProps<'svg'> {
  open: boolean;
  duration?: number;
}

export function MenuToggleIcon({
  open,
  duration = 300,
  className,
  ...props
}: MenuToggleIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('size-5', className)}
      {...props}
    >
      <line
        x1="4"
        y1="6"
        x2="20"
        y2="6"
        style={{
          transition: `all ${duration}ms cubic-bezier(0.16, 1, 0.3, 1)`,
          transformOrigin: '12px 6px',
          transform: open ? 'translateY(6px) rotate(45deg)' : 'none',
        }}
      />
      <line
        x1="4"
        y1="12"
        x2="20"
        y2="12"
        style={{
          transition: `opacity ${duration / 2}ms ease`,
          opacity: open ? 0 : 1,
        }}
      />
      <line
        x1="4"
        y1="18"
        x2="20"
        y2="18"
        style={{
          transition: `all ${duration}ms cubic-bezier(0.16, 1, 0.3, 1)`,
          transformOrigin: '12px 18px',
          transform: open ? 'translateY(-6px) rotate(-45deg)' : 'none',
        }}
      />
    </svg>
  );
}
