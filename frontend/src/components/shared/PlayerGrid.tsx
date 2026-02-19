import { Player } from '../../types';
import { GamePlayerCard } from '../GamePlayerCard';

interface PlayerGridProps {
  players: Player[];
  activeSpeakerId?: string | null;
  chatBubbles: Record<string, string>;
  activeEmotes?: Record<string, string>;
  onVote?: (id: string) => void;
  showVoteButton?: boolean;
}

export const PlayerGrid = ({
  players,
  activeSpeakerId,
  chatBubbles,
  activeEmotes = {},
  onVote,
  showVoteButton,
}: PlayerGridProps) => (
  <div className="w-full max-w-5xl flex flex-col gap-8 md:gap-12 relative z-10 overflow-visible">
    {/* Top Row (first 4 players) */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8 justify-items-center overflow-visible">
      {players.slice(0, 4).map(p => (
        <GamePlayerCard
          key={p.id}
          player={p}
          isSpeaking={activeSpeakerId === p.id}
          onVote={onVote}
          showVoteButton={showVoteButton}
          currentMessage={chatBubbles[p.id]}
          activeEmote={activeEmotes[p.id]}
        />
      ))}
    </div>
    {/* Bottom Row (remaining players, up to 3) */}
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 justify-items-center w-full md:w-4/5 mx-auto overflow-visible">
      {players.slice(4, 7).map(p => (
        <GamePlayerCard
          key={p.id}
          player={p}
          isSpeaking={activeSpeakerId === p.id}
          onVote={onVote}
          showVoteButton={showVoteButton}
          currentMessage={chatBubbles[p.id]}
          activeEmote={activeEmotes[p.id]}
        />
      ))}
    </div>
  </div>
);
