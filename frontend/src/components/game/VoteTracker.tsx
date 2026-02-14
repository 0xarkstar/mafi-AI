import { motion } from 'framer-motion'
import { useGameStore } from '../../stores/gameStore'
import { GlassCard } from '../ui/GlassCard'
import { Vote as VoteIcon } from 'lucide-react'
import { AGENTS } from '../../lib/constants'

export function VoteTracker() {
  const phase = useGameStore((s) => s.phase)
  const votes = useGameStore((s) => s.votes)

  if (phase !== 'day_vote' || votes.length === 0) {
    return null
  }

  // Group votes by target
  const votesByTarget = votes.reduce(
    (acc, vote) => {
      if (!acc[vote.target]) {
        acc[vote.target] = []
      }
      acc[vote.target]!.push(vote.voter)
      return acc
    },
    {} as Record<string, string[]>
  )

  // Get agent color helper
  const getAgentColor = (name: string): string => {
    return AGENTS.find((a) => a.name === name)?.color ?? '#71717a'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4"
    >
      <GlassCard className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <VoteIcon className="w-4 h-4 text-zinc-400" />
          <h3 className="text-sm font-semibold text-zinc-200">Current Votes</h3>
          <span className="ml-auto text-xs text-zinc-500">{votes.length} cast</span>
        </div>

        <div className="space-y-2">
          {Object.entries(votesByTarget).map(([target, voters], i) => (
            <motion.div
              key={target}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center justify-between text-sm"
            >
              <span className="font-semibold" style={{ color: getAgentColor(target) }}>
                {target}
              </span>
              <div className="flex items-center gap-2">
                <div className="flex -space-x-2">
                  {voters.map((voter) => (
                    <div
                      key={voter}
                      className="w-6 h-6 rounded-full border-2 border-zinc-900 flex items-center justify-center text-xs font-semibold"
                      style={{
                        backgroundColor: getAgentColor(voter),
                        color: '#000',
                      }}
                      title={voter}
                    >
                      {voter[0]}
                    </div>
                  ))}
                </div>
                <span className="text-zinc-400 font-mono ml-2">×{voters.length}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </GlassCard>
    </motion.div>
  )
}
