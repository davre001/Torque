"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface RevealProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  delay?: number; // milliseconds
  duration?: number; // milliseconds
  yOffset?: number; // pixels
  className?: string;
  variant?: "fade-up" | "fade-in" | "scale-up";
  threshold?: number;
}

export function Reveal({
  children,
  delay = 0,
  duration = 700,
  yOffset = 24,
  className,
  variant = "fade-up",
  threshold = 0.12,
  style,
  ...props
}: RevealProps) {
  const ref = React.useRef<HTMLDivElement | null>(null);
  const [isVisible, setIsVisible] = React.useState(false);

  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // If reduced motion is requested, immediately make visible without animation
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setIsVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(el);
        }
      },
      {
        threshold,
        rootMargin: "0px 0px -40px 0px",
      }
    );

    observer.observe(el);

    return () => {
      observer.disconnect();
    };
  }, [threshold]);

  const getInitialStyle = (): React.CSSProperties => {
    if (isVisible) {
      return {
        opacity: 1,
        transform: "none",
        transition: `opacity ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms, transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms`,
      };
    }

    if (variant === "fade-in") {
      return {
        opacity: 0,
        transition: `opacity ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms`,
      };
    }

    if (variant === "scale-up") {
      return {
        opacity: 0,
        transform: `scale(0.96) translateY(${yOffset * 0.5}px)`,
        transition: `opacity ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms, transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms`,
      };
    }

    // Default: fade-up
    return {
      opacity: 0,
      transform: `translateY(${yOffset}px)`,
      transition: `opacity ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms, transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms`,
    };
  };

  return (
    <div
      ref={ref}
      style={{
        ...getInitialStyle(),
        ...style,
      }}
      className={cn("will-change-transform will-change-opacity", className)}
      {...props}
    >
      {children}
    </div>
  );
}

export default Reveal;
