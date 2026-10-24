import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import type { GameState } from "@/data/gameTypes";
import { TEAM_COLORS } from "@/data/gameTypes";

interface ResultPageProps {
  state: GameState;
  onNext: () => void;
}

export default function ResultPage({ state, onNext }: ResultPageProps) {
  const { currentRoundIndex, rounds, settings } = state;
  const currentRound = rounds[currentRoundIndex];
  const currentTeam = settings.teams.find(t => t.id === currentRound.teamId)!;
  const teamIndex = settings.teams.findIndex(t => t.id === currentRound.teamId);
  const isLastRound = currentRoundIndex >= rounds.length - 1;

  const movie = currentRound.movie;
  const guessed = currentRound.guessed;
  const timeUsed = currentRound.timeUsed ?? 0;
  const timeLeft = currentRound.timeLimit - timeUsed;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className={`absolute inset-0 ${guessed ? "bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-950/30 dark:to-emerald-950/20" : "bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-950/30 dark:to-gray-950/20"}`} />

      <motion.div
        className="relative z-10 w-full max-w-md text-center"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", bounce: 0.4 }}
      >
        {/* Result banner */}
        <motion.div
          className="text-7xl mb-4"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", bounce: 0.6, delay: 0.1 }}
        >
          {guessed ? "🎉" : "😔"}
        </motion.div>

        <motion.h2
          className={`text-3xl font-black mb-2 ${guessed ? "text-green-600 dark:text-green-400" : "text-slate-600 dark:text-slate-400"}`}
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {guessed ? "Correct Guess!" : "Time's Up / Skipped"}
        </motion.h2>

        {/* Movie reveal */}
        <motion.div
          className="bg-card border border-card-border rounded-2xl p-6 mb-6 shadow-sm"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">The Movie Was</p>
          <h3 className="text-2xl font-black text-foreground mb-1">{movie.title}</h3>
          {movie.teluguTitle && (
            <p className="text-base text-muted-foreground mb-3" style={{ fontFamily: "'Noto Sans Telugu', sans-serif" }}>
              {movie.teluguTitle}
            </p>
          )}
          <div className="flex items-center justify-center gap-3 text-sm">
            <span className="bg-muted text-muted-foreground px-3 py-1 rounded-full capitalize font-medium">{movie.genre}</span>
            <span className="bg-muted text-muted-foreground px-3 py-1 rounded-full font-medium">{movie.year}</span>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          className="grid grid-cols-2 gap-4 mb-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className={`bg-gradient-to-br ${TEAM_COLORS[teamIndex % TEAM_COLORS.length]} text-white rounded-2xl p-4`}>
            <p className="text-xs font-medium opacity-80">{currentTeam.name}</p>
            <p className="text-2xl font-black">{guessed ? "+1" : "0"} pts</p>
          </div>
          <div className="bg-card border border-card-border rounded-2xl p-4">
            <p className="text-xs font-medium text-muted-foreground">Time used</p>
            <p className="text-2xl font-black text-foreground">{timeUsed}s</p>
          </div>
        </motion.div>

        {/* Scores so far */}
        <motion.div
          className="bg-card border border-card-border rounded-2xl p-4 mb-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">Current Scores</p>
          <div className="space-y-2">
            {[...settings.teams]
              .sort((a, b) => b.score - a.score)
              .map((team, idx) => {
                const tIdx = settings.teams.findIndex(t => t.id === team.id);
                return (
                  <div key={team.id} className="flex items-center gap-3">
                    <span className="text-sm font-bold text-muted-foreground w-4">{idx + 1}</span>
                    <div className={`w-3 h-3 rounded-full bg-gradient-to-br ${TEAM_COLORS[tIdx % TEAM_COLORS.length]}`} />
                    <span className="flex-1 text-sm font-semibold text-foreground text-left">{team.name}</span>
                    <span className="font-black text-foreground">{team.score}</span>
                  </div>
                );
              })}
          </div>
        </motion.div>

        <motion.button
          data-testid="button-next-round"
          onClick={onNext}
          className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold text-lg rounded-2xl shadow-lg flex items-center justify-center gap-2"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <span>{isLastRound ? "See Final Scores" : "Next Round"}</span>
          <ChevronRight className="w-5 h-5" />
        </motion.button>
      </motion.div>
    </div>
  );
}
