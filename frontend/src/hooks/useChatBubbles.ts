import { useEffect, useRef, useState } from 'react';
import { Message } from '../types';

/**
 * Manages chat bubbles above player cards.
 * Shows a message bubble for 5 seconds after a new chat message arrives.
 * Returns a Record mapping senderId → current bubble text.
 */
export function useChatBubbles(messages: Message[]): Record<string, string> {
  const [chatBubbles, setChatBubbles] = useState<Record<string, string>>({});
  const bubbleTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1]!;
      if (lastMsg.type === 'chat') {
        const senderId = lastMsg.senderId;

        setChatBubbles(prev => ({ ...prev, [senderId]: lastMsg.text }));

        if (bubbleTimers.current[senderId]) {
          clearTimeout(bubbleTimers.current[senderId]);
        }

        bubbleTimers.current[senderId] = setTimeout(() => {
          setChatBubbles(prev => {
            const newState = { ...prev };
            delete newState[senderId];
            return newState;
          });
          delete bubbleTimers.current[senderId];
        }, 5000);
      }
    }
  }, [messages]);

  return chatBubbles;
}
