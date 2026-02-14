import { useEffect } from 'react'
import { useGameStore } from '../stores/gameStore'
import { PHASE_CONFIG } from '../lib/constants'

export function usePhaseTheme() {
  const phase = useGameStore((s) => s.phase)
  const config = PHASE_CONFIG[phase]

  useEffect(() => {
    // Apply phase class to body for ambient background
    document.body.className = `phase-${phase}`

    return () => {
      document.body.className = ''
    }
  }, [phase])

  return {
    phase,
    label: config.label,
    icon: config.icon,
    gradient: config.gradient,
  }
}
