import { useEffect, useRef } from 'react'
import { useChatStore } from '../../stores/chatStore'
import { GlassCard } from '../ui/GlassCard'
import { ChatBubble } from './ChatBubble'
import { MessageSquare } from 'lucide-react'

export function ChatPanel() {
  const messages = useChatStore((s) => s.messages)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages])

  return (
    <GlassCard className="flex-1 flex flex-col min-h-0 p-4">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/10">
        <MessageSquare className="w-5 h-5 text-zinc-400" />
        <h2 className="text-lg font-semibold text-zinc-100">Game Chat</h2>
        <span className="ml-auto text-xs text-zinc-500">{messages.length} messages</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center">
            <div className="text-zinc-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p className="text-sm">No messages yet</p>
              <p className="text-xs mt-1">Game will start soon...</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg} />
            ))}
            <div ref={scrollRef} />
          </>
        )}
      </div>
    </GlassCard>
  )
}
