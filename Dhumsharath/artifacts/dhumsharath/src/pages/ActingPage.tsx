import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, SkipForward, AlertCircle } from "lucide-react";
import type { GameState } from "@/data/gameTypes";
import { TEAM_COLORS } from "@/data/gameTypes";

interface ActingPageProps {
  state: GameState;
  onGuessed: (timeUsed: number) => void;
  onSkipped: (timeUsed: number) => void;
}

export default function ActingPage({ state, onGuessed, onSkipped }: ActingPageProps) {
  const { currentRoundIndex, rounds, settings } = state;
  const currentRound = rounds[currentRoundIndex];
  const currentTeam = settings.teams.find(t => t.id === currentRound.teamId)!;
  const teamIndex = settings.teams.findIndex(t => t.id === currentRound.teamId);
  const timeLimit = currentRound.timeLimit;

  const [timeLeft, setTimeLeft] = useState(timeLimit);
  const [showConfirm, setShowConfirm] = useState<"guessed" | "skipped" | null>(null);
  const [showHint, setShowHint] = useState(false);

  const timeUsed = timeLimit - timeLeft;
  const progress = (timeLeft / timeLimit) * 100;

  const getTimerColor = () => {
    if (progress > 50) return "from-green-400 to-emerald-500";
    if (progress > 25) return "from-yellow-400 to-orange-400";
    return "from-red-400 to-rose-500";
  };

  const getTimerBgColor = () => {
    if (progress > 50) return "text-green-600 dark:text-green-400";
    if (progress > 25) return "text-orange-600 dark:text-orange-400";
    return "text-red-600 dark:text-red-400";
  };

  useEffect(() => {
    if (timeLeft <= 0) {
      onSkipped(timeLimit);
      return;
    }
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [timeLeft, timeLimit, onSkipped]);

  const handleGuessed = useCallback(() => {
    setShowConfirm(null);
    onGuessed(timeUsed);
  }, [timeUsed, onGuessed]);

  const handleSkipped = useCallback(() => {
    setShowConfirm(null);
    onSkipped(timeUsed);
  }, [timeUsed, onSkipped]);

  const movie = currentRound.movie;

  return (
    <div className="min-h-screen flex flex-col p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900" />

      {/* Animated background effects */}
      <div className="absolute top-0 left-0 right-0 h-1">
        <motion.div
          className={`h-full bg-gradient-to-r ${getTimerColor()}`}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "linear" }}
        />
      </div>

      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Header */}
        <div className="flex items-center justify-between mb-4 pt-2">
          <div className={`flex items-center gap-2 bg-gradient-to-r ${TEAM_COLORS[teamIndex % TEAM_COLORS.length]} text-white px-4 py-2 rounded-xl font-bold text-sm`}>
            <span>🏅</span>
            <span>{currentTeam.name}</span>
          </div>
          <div className="text-slate-400 text-sm font-medium">
            Round {currentRoundIndex + 1}/{rounds.length}
          </div>
        </div>

        {/* Movie reveal */}
        <div className="flex-1 flex flex-col items-center justify-center">
          <motion.div
            className="w-full max-w-md"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", bounce: 0.4 }}
          >
            {/* Movie title card */}
            <div className="bg-white dark:bg-slate-800 rounded-3xl p-8 mb-6 shadow-2xl text-center">
              <div className="text-4xl mb-4">🎬</div>
              <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">ACT THIS MOVIE</p>
              <h2 className="text-3xl sm:text-4xl font-black text-foreground mb-2 leading-tight">
                {movie.title}
              </h2>
              {movie.teluguTitle && (
                <p className="text-lg text-muted-foreground font-semibold" style={{ fontFamily: "'Noto Sans Telugu', sans-serif" }}>
                  {movie.teluguTitle}
                </p>
              )}
              <div className="flex items-center justify-center gap-3 mt-4">
                <span className="text-xs font-semibold bg-muted text-muted-foreground px-3 py-1 rounded-full capitalize">
                  {movie.genre}
                </span>
                <span className="text-xs font-semibold bg-muted text-muted-foreground px-3 py-1 rounded-full">
                  {movie.year}
                </span>
              </div>

              {movie.hint && (
                <div className="mt-4">
                  {showHint ? (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-3"
                    >
                      <p className="text-sm text-amber-800 dark:text-amber-300">
                        💡 {movie.hint}
                      </p>
                    </motion.div>
                  ) : (
                    <button
                      data-testid="button-show-hint"
                      onClick={() => setShowHint(true)}
                      className="text-xs text-primary hover:underline font-medium"
                    >
                      Show hint
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Timer */}
            <div className="text-center mb-6">
              <motion.div
                className={`text-6xl font-black ${getTimerBgColor()}`}
                key={timeLeft}
                animate={timeLeft <= 10 ? { scale: [1, 1.15, 1] } : {}}
                transition={{ duration: 0.3 }}
              >
                {timeLeft}
              </motion.div>
              <p className="text-slate-400 text-sm mt-1">seconds remaining</p>
            </div>

            {/* Action buttons */}
            <div className="grid grid-cols-2 gap-4">
              <motion.button
                data-testid="button-team-guessed"
                onClick={() => setShowConfirm("guessed")}
                className="flex flex-col items-center gap-2 bg-green-500 hover:bg-green-600 text-white font-bold py-5 rounded-2xl shadow-lg transition-all"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                <CheckCircle className="w-7 h-7" />
                <span className="text-lg">Guessed!</span>
              </motion.button>

              <motion.button
                data-testid="button-skip-movie"
                onClick={() => setShowConfirm("skipped")}
                className="flex flex-col items-center gap-2 bg-slate-600 hover:bg-slate-700 text-white font-bold py-5 rounded-2xl shadow-lg transition-all"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                <SkipForward className="w-7 h-7" />
                <span className="text-lg">Skip</span>
              </motion.button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Confirm dialogs */}
      <AnimatePresence>
        {showConfirm && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-card rounded-3xl p-6 max-w-sm w-full shadow-2xl text-center"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: "spring", bounce: 0.3 }}
            >
              {showConfirm === "guessed" ? (
                <>
                  <div className="text-5xl mb-3">🎉</div>
                  <h3 className="text-xl font-black mb-1">Team Guessed It?</h3>
                  <p className="text-muted-foreground text-sm mb-6">Award points to {currentTeam.name}</p>
                  <div className="flex gap-3">
                    <button
                      data-testid="button-confirm-guessed"
                      onClick={handleGuessed}
                      className="flex-1 bg-green-500 text-white font-bold py-3 rounded-xl hover:bg-green-600 transition-colors"
                    >
                      Yes! +1 Point
                    </button>
                    <button onClick={() => setShowConfirm(null)} className="flex-1 bg-muted text-muted-foreground font-bold py-3 rounded-xl hover:bg-muted/70 transition-colors">
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="text-5xl mb-3">⏭️</div>
                  <h3 className="text-xl font-black mb-1">Skip this movie?</h3>
                  <p className="text-muted-foreground text-sm mb-6">No points will be awarded</p>
                  <div className="flex gap-3">
                    <button
                      data-testid="button-confirm-skip"
                      onClick={handleSkipped}
                      className="flex-1 bg-slate-600 text-white font-bold py-3 rounded-xl hover:bg-slate-700 transition-colors"
                    >
                      Skip
                    </button>
                    <button onClick={() => setShowConfirm(null)} className="flex-1 bg-muted text-muted-foreground font-bold py-3 rounded-xl hover:bg-muted/70 transition-colors">
                      Cancel
                    </button>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Time's up overlay */}
      <AnimatePresence>
        {timeLeft === 0 && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="text-center"
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", bounce: 0.4 }}
            >
              <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h2 className="text-4xl font-black text-white">Time's Up!</h2>
              <p className="text-slate-400 mt-2">The movie was:</p>
              <p className="text-2xl font-bold text-white mt-1">{movie.title}</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
