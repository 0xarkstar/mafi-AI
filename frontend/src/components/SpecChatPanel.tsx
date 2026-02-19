import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, MessageSquare, Send } from 'lucide-react';

interface SpecMessage {
  id: string;
  name: string;
  text: string;
  time: number;
  isMe: boolean;
}

interface SpecChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onUnreadChange?: () => void;
}

const SPEC_NAMES = ['Whale_0x', 'CryptoNerd', 'MonadFan', 'BetKing', 'DeFiDegen', 'MafiaWatcher', 'LurkMaster'];
const SPEC_LINES = [
  'Viktor is definitely sus',
  'lol Nova is playing it cool',
  'anyone else think Iris is mafia?',
  'just went all in on Citizens',
  'this round is crazy',
  'mafia is so obvious rn',
  'no way they vote out Luna',
  'GG ez citizens win',
  'that elimination was huge',
  "I think it's Rex tbh",
  'who else is betting?',
  'odds just shifted hard',
  'night phase incoming...',
  'calling it now, Blaze is mafia',
  'Sage is playing 4D chess',
];

export const SpecChatPanel = ({ isOpen, onClose: _onClose, onUnreadChange }: SpecChatPanelProps) => {
  const [specMessages, setSpecMessages] = useState<SpecMessage[]>([]);
  const [specChatInput, setSpecChatInput] = useState('');
  const specChatScrollRef = useRef<HTMLDivElement>(null);

  // Simulated spectator chat from other viewers
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.55) {
        const name = SPEC_NAMES[Math.floor(Math.random() * SPEC_NAMES.length)]!;
        const text = SPEC_LINES[Math.floor(Math.random() * SPEC_LINES.length)]!;
        const msg: SpecMessage = { id: Math.random().toString(36).substr(2, 9), name, text, time: Date.now(), isMe: false };
        setSpecMessages(prev => [...prev, msg].slice(-50));
        if (!isOpen) {
          onUnreadChange?.();
        }
      }
    }, 4000 + Math.random() * 3000);
    return () => clearInterval(interval);
  }, [isOpen, onUnreadChange]);

  // Auto-scroll spectator chat
  useEffect(() => {
    if (specChatScrollRef.current) {
      specChatScrollRef.current.scrollTop = specChatScrollRef.current.scrollHeight;
    }
  }, [specMessages]);

  const handleSpecChatSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!specChatInput.trim()) return;
    const msg: SpecMessage = {
      id: Math.random().toString(36).substr(2, 9),
      name: 'You',
      text: specChatInput.trim(),
      time: Date.now(),
      isMe: true,
    };
    setSpecMessages(prev => [...prev, msg].slice(-50));
    setSpecChatInput('');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          className="absolute bottom-24 left-6 z-[60] w-[340px] h-[420px] flex flex-col bg-[#0f172a]/95 backdrop-blur-xl border border-purple-500/30 rounded-2xl shadow-[0_0_40px_rgba(168,85,247,0.15)] overflow-hidden"
        >
          {/* Chat Header */}
          <div className="h-12 bg-purple-500/10 border-b border-purple-500/20 flex items-center justify-between px-4 shrink-0">
            <div className="flex items-center gap-2 text-purple-300 text-xs uppercase tracking-[0.15em] font-bold">
              <Users className="w-4 h-4" />
              <span>Spectator Chat</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-[9px] text-white/30 font-mono">online</span>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2" ref={specChatScrollRef}>
            {specMessages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-white/20 gap-2">
                <MessageSquare className="w-8 h-8 opacity-20" />
                <p className="text-[10px] uppercase tracking-widest">No messages yet...</p>
              </div>
            ) : (
              specMessages.map(msg => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, x: msg.isMe ? 10 : -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`flex flex-col ${msg.isMe ? 'items-end' : 'items-start'}`}
                >
                  <div className={`max-w-[85%] ${msg.isMe ? 'items-end' : 'items-start'}`}>
                    <div className="flex items-center gap-2 px-1 mb-0.5">
                      <span className={`text-[10px] font-bold ${msg.isMe ? 'text-purple-300' : 'text-white/60'}`}>{msg.name}</span>
                      <span className="text-[9px] text-white/20">
                        {new Date(msg.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div className={`px-3 py-1.5 rounded-lg text-sm leading-relaxed border ${
                      msg.isMe
                        ? 'bg-purple-500/20 text-white border-purple-500/30 rounded-tr-none'
                        : 'bg-white/5 text-white/80 border-white/5 rounded-tl-none'
                    }`}>
                      {msg.text}
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>

          {/* Input */}
          <div className="p-3 bg-black/40 border-t border-purple-500/20 shrink-0">
            <form onSubmit={handleSpecChatSend} className="flex items-center gap-2">
              <div className="relative flex-1">
                <input
                  value={specChatInput}
                  onChange={(e) => setSpecChatInput(e.target.value)}
                  placeholder="Chat with spectators..."
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-purple-500/50 transition-colors"
                />
              </div>
              <button
                type="submit"
                disabled={!specChatInput.trim()}
                className="w-10 h-10 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300 hover:bg-purple-500/30 transition-colors disabled:opacity-30"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
