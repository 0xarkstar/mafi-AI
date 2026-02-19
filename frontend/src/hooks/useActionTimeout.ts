import { useEffect } from 'react';
import { ActionRequest } from '../types';

/**
 * Syncs timeLeft with the current action's timeout value.
 * Call with setTimeLeft from useCountdown to start the countdown.
 */
export function useActionTimeout(
  action: ActionRequest | null,
  setTimeLeft: (value: number) => void,
): void {
  useEffect(() => {
    if (action) {
      setTimeLeft(action.timeout);
    }
  }, [action, setTimeLeft]);
}
