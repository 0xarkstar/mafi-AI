import { ProgressRing } from '../ui/ProgressRing'

interface PhaseTimerProps {
  seconds: number
  total: number
}

export function PhaseTimer({ seconds, total }: PhaseTimerProps) {
  const progress = (seconds / total) * 100

  // Color shift: green → amber → red
  let color = '#22c55e' // green
  if (progress < 50) {
    color = '#f59e0b' // amber
  }
  if (progress < 20) {
    color = '#ef4444' // red
  }

  return (
    <div className="relative inline-flex items-center justify-center">
      <ProgressRing progress={progress} size={64} strokeWidth={4} color={color} />
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-bold font-mono text-zinc-100">{seconds}</span>
      </div>
    </div>
  )
}
