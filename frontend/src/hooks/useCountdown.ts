import { useEffect, useState } from 'react';

/**
 * Simple countdown timer.
 * Returns [timeLeft, setTimeLeft] — call setTimeLeft to start/reset the countdown.
 */
export function useCountdown(initialValue = 0): [number, (value: number) => void] {
  const [timeLeft, setTimeLeft] = useState(initialValue);

  useEffect(() => {
    if (timeLeft > 0) {
      const timerId = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timerId);
    }
  }, [timeLeft]);

  return [timeLeft, setTimeLeft];
}
