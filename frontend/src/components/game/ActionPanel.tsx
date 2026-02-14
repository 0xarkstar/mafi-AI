import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Send, Clock } from 'lucide-react'
import { useGameStore } from '../../stores/gameStore'
import { GlassCard } from '../ui/GlassCard'
import { Button } from '../ui/Button'
import { PhaseTimer } from './PhaseTimer'

interface ActionPanelProps {
  onSubmit: (response: string) => void
}

export function ActionPanel({ onSubmit }: ActionPanelProps) {
  const actionRequest = useGameStore((s) => s.actionRequest)
  const [response, setResponse] = useState('')
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    if (!actionRequest) return

    setSubmitted(false)
    setTimeRemaining(actionRequest.timeout)
    const firstOption = actionRequest.options?.[0]
    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval)
          if (firstOption) {
            onSubmit(firstOption)
            setSubmitted(true)
          }
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [actionRequest, onSubmit])

  if (!actionRequest) return null

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (submitted) return
    if (response.trim() || actionRequest.actionType === 'vote') {
      onSubmit(response.trim())
      setResponse('')
      setSubmitted(true)
    }
  }

  const isStatement = actionRequest.actionType === 'statement'
  const isVote = actionRequest.actionType === 'vote'

  return (
    <motion.div
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 100, opacity: 0 }}
      className="fixed bottom-0 left-0 right-0 z-30 p-4 lg:relative lg:mt-4"
    >
      <GlassCard className="p-4">
        <div className="flex items-start gap-4">
          {/* Timer */}
          <div className="flex-shrink-0">
            <PhaseTimer seconds={timeRemaining} total={actionRequest.timeout} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-semibold text-zinc-200">Your Turn</h3>
            </div>

            <p className="text-sm text-zinc-400 mb-3">{actionRequest.prompt}</p>

            <form onSubmit={handleSubmit} className="space-y-3">
              {isStatement && (
                <textarea
                  value={response}
                  onChange={(e) => setResponse(e.target.value)}
                  placeholder="Type your statement..."
                  className="w-full px-3 py-2 rounded-lg glass-card text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 resize-none"
                  rows={3}
                  maxLength={200}
                  autoFocus
                />
              )}

              {isVote && (
                <select
                  value={response}
                  onChange={(e) => setResponse(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg glass-card text-zinc-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  autoFocus
                >
                  <option value="">Select a player to vote for...</option>
                  {actionRequest.options.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              )}

              <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-500">
                  {isStatement && `${response.length}/200`}
                  {isVote && actionRequest.options.length > 0 && `${actionRequest.options.length} options`}
                </span>

                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={!response.trim()}
                  className="gap-2"
                >
                  Submit
                  <Send className="w-3 h-3" />
                </Button>
              </div>
            </form>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  )
}
