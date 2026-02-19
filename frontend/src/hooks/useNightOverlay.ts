import { useEffect, useState } from 'react';
import { GamePhase } from '../types';

/**
 * Returns true for 3 seconds when phase transitions to NIGHT.
 * Used to show the night overlay animation.
 */
export function useNightOverlay(phase: GamePhase): boolean {
  const [showNightOverlay, setShowNightOverlay] = useState(false);

  useEffect(() => {
    if (phase === GamePhase.NIGHT) {
      setShowNightOverlay(true);
      const timer = setTimeout(() => setShowNightOverlay(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [phase]);

  return showNightOverlay;
}
