import { useGameStore } from './store';
import { ScreenState } from './types';
import { LandingScreen } from './screens/LandingScreen';
import { LobbyScreen } from './screens/LobbyScreen';
import { GameScreen } from './screens/GameScreen';
import { SpectatorScreen } from './screens/SpectatorScreen';
import { RevealScreen } from './screens/RevealScreen';
import { GameOverScreen } from './screens/GameOverScreen';
import { AnimatePresence, motion } from 'framer-motion';

const App = () => {
  const { screen } = useGameStore();

  const renderScreen = () => {
    switch (screen) {
      case ScreenState.LANDING:
        return <LandingScreen />;
      case ScreenState.LOBBY:
        return <LobbyScreen />;
      case ScreenState.GAME:
        return <GameScreen />;
      case ScreenState.SPECTATE:
        return <SpectatorScreen />;
      case ScreenState.REVEAL:
        return <RevealScreen />;
      case ScreenState.GAME_OVER:
        return <GameOverScreen />;
      default:
        return <LandingScreen />;
    }
  };

  return (
    <div className="bg-background text-white min-h-screen font-sans selection:bg-gold/30 selection:text-gold-light">
      <AnimatePresence mode="wait">
        <motion.div
            key={screen}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full h-full"
        >
            {renderScreen()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default App;
