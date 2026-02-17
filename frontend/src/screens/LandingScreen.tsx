import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useGameStore } from '../store';
import { AVATAR_IMAGES } from '../types';
import { Button, Input } from '../components/UIComponents';
import { Gamepad2, Eye, HelpCircle } from 'lucide-react';

// Floating fragment particles for the seam area
interface FloatingPiece {
  top: number;       // % position
  left: number;      // px from seam center
  w: number;         // px
  h: number;         // px
  opacity: number;
  driftX: number;    // px drift range
  driftY: number;    // px drift range
  duration: number;  // seconds for one cycle
  delay: number;     // initial delay
  rotate: number;    // base rotation
  rotateRange: number; // rotation drift
}

const generateFloatingPieces = (): FloatingPiece[] => {
  let seed = 99;
  const rand = () => {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  };

  const pieces: FloatingPiece[] = [];

  for (let i = 0; i < 20; i++) {
    pieces.push({
      top: rand() * 95,
      left: -80 + rand() * 120,
      w: 6 + rand() * 30,
      h: 4 + rand() * 24,
      opacity: 0.08 + rand() * 0.25,
      driftX: 3 + rand() * 10,
      driftY: 2 + rand() * 8,
      duration: 4 + rand() * 6,
      delay: rand() * 3,
      rotate: (rand() - 0.5) * 20,
      rotateRange: 3 + rand() * 8,
    });
  }
  return pieces;
};

// SVG mask applied to the right-half image container
// x=0 is the LEFT edge of the image panel, x=1000 is the RIGHT edge
// Shattered fragments on the left edge, solid on the right
const buildShatteredMask = (): string => {
  let seed = 77;
  const rand = () => {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  };

  const W = 1000;
  const H = 1000;
  let rects = '';

  // Solid: fully visible from x=350 to x=1000 (right ~65% of the image panel)
  rects += `<rect x="350" y="0" width="650" height="${H}" fill="white"/>`;

  // Shattered edge zone: x=0 to x=400
  const rowCount = 70;
  const rowH = H / rowCount;

  for (let i = 0; i < rowCount; i++) {
    const y = i * rowH;

    // Main jagged block: random start between x=80 and x=350
    const startX = 80 + rand() * 270;
    const blockW = 400 - startX;
    const opacity = 0.35 + (1 - (startX - 80) / 270) * 0.65;
    rects += `<rect x="${startX}" y="${y}" width="${blockW}" height="${rowH + 1}" fill="white" opacity="${opacity.toFixed(2)}"/>`;

    // Medium fragments scattering further left
    if (rand() > 0.3) {
      const fragX = 20 + rand() * (startX - 30);
      const fragW = 8 + rand() * 45;
      const fragH = rowH * (0.35 + rand() * 0.65);
      const fragOpacity = 0.08 + rand() * 0.3;
      rects += `<rect x="${fragX}" y="${y + rand() * rowH * 0.3}" width="${fragW}" height="${fragH}" fill="white" opacity="${fragOpacity.toFixed(2)}"/>`;
    }

    // Tiny specks at the far left
    if (rand() > 0.5) {
      const spX = rand() * 60;
      const spW = 3 + rand() * 15;
      const spH = 2 + rand() * (rowH * 0.5);
      rects += `<rect x="${spX}" y="${y + rand() * rowH}" width="${spW}" height="${spH}" fill="white" opacity="${(0.04 + rand() * 0.15).toFixed(2)}"/>`;
    }
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}">${rects}</svg>`;
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
};

export const LandingScreen = () => {
  const { connectAndJoin, joinAsSpectator } = useGameStore();
  const [nick, setNick] = useState('');
  const [selectedAvatar, setSelectedAvatar] = useState(0);

  const shatteredMask = useMemo(() => buildShatteredMask(), []);
  const floatingPieces = useMemo(() => generateFloatingPieces(), []);

  const handleJoin = () => {
    if (!nick.trim()) return;
    connectAndJoin(nick.trim(), selectedAvatar);
  };

  return (
    <div className="h-screen w-full flex overflow-hidden relative bg-[#030712]">

      {/* ===== Right Half: Image with shattered left edge ===== */}
      <div
        className="hidden lg:block absolute top-0 right-0 w-1/2 h-full z-0"
        style={{
          maskImage: shatteredMask,
          WebkitMaskImage: shatteredMask,
          maskSize: '100% 100%',
          WebkitMaskSize: '100% 100%',
        }}
      >
        <img
          src="/images/landing-bg.png"
          alt=""
          className="w-full h-full object-cover"
          style={{ objectPosition: '35% center' }}
        />
      </div>

      {/* ===== Floating shattered pieces at the seam ===== */}
      <div className="hidden lg:block absolute top-0 h-full z-[1] pointer-events-none" style={{ left: '42%', width: '16%' }}>
        {floatingPieces.map((p, i) => (
          <motion.div
            key={i}
            className="absolute overflow-hidden rounded-sm"
            style={{
              top: `${p.top}%`,
              left: `${p.left}px`,
              width: `${p.w}px`,
              height: `${p.h}px`,
              backgroundImage: "url('/images/landing-bg.png')",
              backgroundSize: '50vw 100vh',
              backgroundPosition: `${35 + (p.left / 5)}% ${p.top}%`,
            }}
            initial={{
              opacity: 0,
              rotate: p.rotate,
            }}
            animate={{
              opacity: [0, p.opacity, p.opacity, 0],
              x: [0, p.driftX, -p.driftX * 0.5, 0],
              y: [0, -p.driftY, p.driftY * 0.5, 0],
              rotate: [p.rotate, p.rotate + p.rotateRange, p.rotate - p.rotateRange, p.rotate],
            }}
            transition={{
              duration: p.duration,
              delay: p.delay,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        ))}
      </div>

      {/* ===== Mobile fallback ===== */}
      <div className="lg:hidden absolute inset-0 z-0">
        <img
          src="/images/landing-bg.png"
          alt=""
          className="w-full h-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-[#030712]/80" />
      </div>

      {/* ===== Left Half: Content ===== */}
      <div className="w-full lg:w-1/2 h-full flex flex-col justify-center px-8 lg:pl-24 relative z-10">

        {/* Ambient glow */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-purple-900/5 rounded-full blur-[150px]" />
          <div className="absolute bottom-[-15%] left-[-5%] w-[40%] h-[40%] bg-gold/5 rounded-full blur-[100px]" />
        </div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          className="mb-12 relative z-10"
        >
          <h1
            className="text-6xl md:text-8xl lg:text-9xl font-black tracking-tighter leading-[0.85] text-transparent bg-clip-text"
            style={{
              backgroundImage: 'linear-gradient(180deg, #FFF2CC 0%, #F0D78C 15%, #D4A853 40%, #B8860B 60%, #805F1F 80%, #5C3D10 100%)',
              WebkitTextStroke: '1px rgba(139,90,20,0.3)',
              filter: 'drop-shadow(0 0 30px rgba(212,168,83,0.4)) drop-shadow(0 4px 8px rgba(0,0,0,0.6))',
            }}
          >
            MAFI-AI
          </h1>
          {/* Decorative line */}
          <div className="flex items-center gap-3 mt-4 ml-1">
            <div className="h-px flex-1 max-w-[60px] bg-gradient-to-r from-transparent via-[#8B5A14] to-[#D4A853]" />
            <div className="w-1.5 h-1.5 rotate-45 bg-[#D4A853] shadow-[0_0_8px_rgba(212,168,83,0.6)]" />
            <div className="h-px flex-1 max-w-[60px] bg-gradient-to-l from-transparent via-[#8B5A14] to-[#D4A853]" />
          </div>
          <p className="text-[#8B7355] text-sm font-bold tracking-[0.5em] uppercase mt-4 ml-2 pl-1 border-l-2 border-[#8B5A14]/40">
            Can you tell who's real?
          </p>
        </motion.div>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="w-full max-w-[400px] relative z-10"
        >
          <div className="space-y-6">
            {/* Nickname input */}
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-bold text-[#4b5563] tracking-[0.2em] block pl-1">
                Agent Codename
              </label>
              <Input
                placeholder="ENTER ALIAS"
                value={nick}
                onChange={(e) => setNick(e.target.value)}
                maxLength={12}
                autoFocus
              />
              <div className="flex items-center gap-1.5 pl-1 pt-1 opacity-70">
                <HelpCircle className="w-3 h-3 text-[#4b5563]" />
                <span className="text-[10px] text-[#4b5563] font-medium tracking-wide">
                  Are you human? No problem. Write your nickname.
                </span>
              </div>
            </div>

            {/* Avatar selection */}
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-bold text-[#4b5563] tracking-[0.2em] block pl-1">
                Choose Your Identity
              </label>
              <div className="grid grid-cols-4 gap-2">
                {AVATAR_IMAGES.map((src, i) => {
                  const isSelected = selectedAvatar === i;
                  return (
                    <motion.button
                      key={i}
                      whileHover={{ scale: 1.08 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setSelectedAvatar(i)}
                      className={`aspect-square rounded-lg overflow-hidden border-2 transition-all duration-200 ${
                        isSelected
                          ? 'border-gold shadow-[0_0_12px_rgba(212,168,83,0.4)] ring-1 ring-gold/30'
                          : 'border-white/10 hover:border-white/30'
                      }`}
                    >
                      <img src={src} alt={`Character ${i + 1}`} className="w-full h-full object-cover" />
                    </motion.button>
                  );
                })}
              </div>
            </div>

            {/* Buttons */}
            <div className="space-y-3 pt-2">
              <Button
                onClick={handleJoin}
                disabled={!nick.trim()}
                size="xl"
                className="w-full"
                icon={<Gamepad2 className="w-5 h-5" />}
              >
                Join Game
              </Button>
              <Button
                variant="secondary"
                size="lg"
                className="w-full"
                icon={<Eye className="w-4 h-4" />}
                onClick={joinAsSpectator}
              >
                Spectate Match
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
