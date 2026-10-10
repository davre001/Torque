"use client"

import { ArrowRight } from "lucide-react"
import { motion, useReducedMotion } from "motion/react"
import { SonarGrid } from "@/components/ui/sonar-grid"

const settings = {
  ringWidth: 90,
  speed: 260,
  amplitude: 2.2,
  pingEvery: 2.4,
  interactive: true,
  spacing: 26,
  baseOpacity: 0.18,
  useThemeColor: false,
  color: "#000000",
  eyebrow: "Autonomous Recovery Agent",
  headline: "Signals, not noise.",
  subline: "Every ping is a real event from your infrastructure. Tap anywhere to send one.",
}

export default function Demo(props: Partial<typeof settings>) {
  const s = { ...settings, ...props }
  const reduce = useReducedMotion()
  const enter = (delay: number) =>
    reduce
      ? {}
      : {
          initial: { opacity: 0, y: 14, filter: "blur(6px)" },
          animate: { opacity: 1, y: 0, filter: "blur(0px)" },
          transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
        }

  return (
    <SonarGrid
      id="sonar-grid-demo"
      ringWidth={s.ringWidth}
      speed={s.speed}
      amplitude={s.amplitude}
      pingEvery={s.pingEvery}
      interactive={s.interactive}
      spacing={s.spacing}
      baseOpacity={s.baseOpacity}
      color={s.color}
      pingArea={[0.22, 0.18, 0.78, 0.82]}
      className="bg-white text-zinc-950 flex min-h-[max(560px,100svh)] w-full flex-col"
    >
      {/* Soft wash in white */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_50%_50%_at_50%_50%,rgba(255,255,255,0.92)_0%,transparent_100%)]"
      />

      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col items-center justify-center px-8 py-24 text-center">
        <div className="flex max-w-2xl flex-col items-center">
          <motion.p
            {...enter(0)}
            className="glass-pill mb-5 inline-flex items-center gap-2 rounded-full px-3.5 py-1 text-xs font-medium text-zinc-800"
          >
            <span aria-hidden="true" className="bg-black size-1.5 rounded-full animate-pulse" />
            {s.eyebrow}
          </motion.p>
          <motion.h1
            {...enter(0.08)}
            className="text-black text-5xl font-semibold tracking-tight text-balance sm:text-6xl md:text-7xl"
          >
            {s.headline}
          </motion.h1>
          <motion.p {...enter(0.16)} className="text-zinc-600 mt-6 max-w-xl text-base text-pretty sm:text-lg">
            {s.subline}
          </motion.p>
          <motion.div {...enter(0.24)} className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              id="cta-primary"
              data-slot="cta-primary"
              className="glass-btn-primary inline-flex h-11 cursor-pointer items-center gap-2 rounded-full px-6 text-sm font-medium outline-none focus-visible:ring-[3px] focus-visible:ring-black/20"
            >
              Start listening
              <ArrowRight
                aria-hidden="true"
                className="size-4 transition-transform duration-200 group-hover:translate-x-0.5"
              />
            </button>
            <a
              href="#docs"
              data-slot="cta-secondary"
              className="glass-btn-secondary inline-flex h-11 cursor-pointer items-center rounded-full px-6 text-sm font-medium outline-none focus-visible:ring-[3px] focus-visible:ring-black/20"
            >
              Read the docs
            </a>
          </motion.div>
        </div>
      </div>
    </SonarGrid>
  )
}
