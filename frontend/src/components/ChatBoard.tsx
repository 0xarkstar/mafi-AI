import { useEffect, useRef, useState } from 'react';
import type React from 'react';
import { Input } from './UIComponents';
import { motion } from 'framer-motion';
import { MessageSquare, Send, Skull, X, Smile } from 'lucide-react';
import { useGameStore } from '../store';
import { EmoteMenu } from './GameComponents';

interface ChatBoardProps {
  onClose?: () => void;
}

export const ChatBoard = ({ onClose }: ChatBoardProps) => {
  const { messages, addMessage, nickname, triggerEmote, currentAction, submitActionResponse } = useGameStore();
  const [input, setInput] = useState('');
  const [isEmoteOpen, setIsEmoteOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const isStatementTurn = currentAction?.actionType === 'statement';

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    if (isStatementTurn) {
      submitActionResponse(input.trim());
    } else {
      addMessage({
        senderId: 'human-1',
        senderName: nickname,
        text: input,
        type: 'chat',
        color: '#ffffff'
      });
    }
    setInput('');
  };

  return (
    <div className="h-full flex flex-col relative bg-[#030712]/95 backdrop-blur-xl border-r border-white/5 shadow-2xl">
      {/* Top Bar */}
      <div className="h-14 bg-black/40 border-b border-white/5 flex items-center justify-between px-4">
         <div className="flex items-center gap-2 text-gold text-xs uppercase tracking-[0.15em] font-bold">
            <MessageSquare className="w-4 h-4" />
            <span>{isStatementTurn ? 'Your Turn to Speak' : 'Encrypted Channel'}</span>
         </div>
         {onClose && (
             <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-white/50 hover:text-white transition-colors">
                 <X className="w-5 h-5" />
             </button>
         )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-white/20 gap-4">
             <MessageSquare className="w-10 h-10 opacity-20" />
             <p className="text-xs uppercase tracking-widest">No signals detected...</p>
          </div>
        )}

        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className={`flex flex-col ${msg.senderId === 'human-1' ? 'items-end' : 'items-start'}`}
          >
            {msg.type === 'system' ? (
               <div className="w-full text-center my-3">
                 <span className="text-[9px] uppercase tracking-[0.15em] text-white/30 bg-white/5 px-2 py-1 rounded-full">{msg.text}</span>
               </div>
            ) : msg.type === 'elimination' ? (
                <div className="w-full flex items-center justify-center my-2">
                    <div className="bg-red-950/40 border border-red-500/30 px-4 py-1.5 rounded text-red-400 text-[10px] font-bold uppercase tracking-widest flex items-center gap-2">
                        <Skull className="w-3 h-3" /> {msg.text}
                    </div>
                </div>
            ) : (
              <div className={`max-w-[85%] flex flex-col gap-1 ${msg.senderId === 'human-1' ? 'items-end' : 'items-start'}`}>
                <div className="flex items-center gap-2 px-1">
                    <span className="text-[10px] font-bold" style={{ color: msg.color || '#fff' }}>{msg.senderName}</span>
                    <span className="text-[9px] text-white/20">{new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
                <div className={`px-3 py-2 rounded-lg text-sm leading-relaxed shadow-sm border ${
                    msg.senderId === 'human-1'
                    ? 'bg-[#d4a853]/10 text-white border-[#d4a853]/30 rounded-tr-none'
                    : 'bg-[#1e293b] text-white/90 border-white/10 rounded-tl-none'
                }`}>
                    {msg.text}
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-3 bg-black/60 border-t border-white/5">
        <form onSubmit={handleSend} className="relative flex items-center gap-2">
            <div className="relative">
                <button
                    type="button"
                    onClick={() => setIsEmoteOpen(!isEmoteOpen)}
                    className={`w-10 h-10 rounded-full flex items-center justify-center border transition-all duration-300 shrink-0 ${
                        isEmoteOpen
                        ? 'bg-white/20 border-white text-white'
                        : 'bg-white/5 border-white/10 text-white/50 hover:border-gold/50 hover:text-gold'
                    }`}
                >
                    <Smile className="w-5 h-5" />
                </button>
                <EmoteMenu
                    isOpen={isEmoteOpen}
                    onClose={() => setIsEmoteOpen(false)}
                    onSelect={(emote) => { triggerEmote('human-1', emote); setIsEmoteOpen(false); }}
                />
            </div>
            <div className="relative flex-1">
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={isStatementTurn ? "Share your thoughts..." : "Type message..."}
                    className="pl-3 pr-10 py-3 bg-white/5 border-white/10 focus:border-gold/50 rounded-lg text-sm w-full"
                />
                <button
                    type="submit"
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 p-2 text-gold hover:text-white transition-colors disabled:opacity-30"
                    disabled={!input}
                >
                    <Send className="w-4 h-4" />
                </button>
            </div>
        </form>
      </div>
    </div>
  );
};
