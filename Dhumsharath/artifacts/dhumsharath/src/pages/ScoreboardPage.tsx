import { motion } from "framer-motion";
import { Trophy, Film, ChevronRight } from "lucide-react";
import type { GameState } from "@/data/gameTypes";
import { TEAM_COLORS, TEAM_TEXT_COLORS } from "@/data/gameTypes";

interface ScoreboardPageProps {
  state: GameState;
  onContinue: () => void;
  isFinal?: boolean;
  onPlayAgain?: () => void;
}

export default function ScoreboardPage({ state, onContinue, isFinal = false, onPlayAgain }: ScoreboardPageProps) {
  const { settings, rounds, currentRoundIndex } = state;

  const sortedTeams = [...settings.teams].sort((a, b) => b.score - a.score);
  const leader = sortedTeams[0];

  const teamRoundHistory = settings.teams.map(team => {
    const teamRounds = rounds.slice(0, currentRoundIndex + 1).filter(r => r.teamId === team.id);
    return {
      team,
      rounds: teamRounds,
      correct: teamRounds.filter(r => r.guessed).length,
    };
  });

  const podiumIcons = ["🥇", "🥈", "🥉"];

  return (
    <div className="min-h-screen p-4 sm:p-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 dark:from-orange-950/20 dark:via-amber-950/10 dark:to-yellow-950/20" />
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-orange-400 via-yellow-400 to-red-400" />

      <div className="relative z-10 max-w-md mx-auto">
        <motion.div
          className="text-center mb-8 pt-4"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="text-5xl mb-3">{isFinal ? "🏆" : "📊"}</div>
          <h2 className="text-3xl font-black text-foreground">
            {isFinal ? "Final Results!" : "Scoreboard"}
          </h2>
          {isFinal && (
            <motion.p
              className="text-primary font-bold mt-1"
              animate={{ opacity: [0.6, 1, 0.6] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              Game Over!
            </motion.p>
          )}
        </motion.div>

        {/* Podium (for final) */}
        {isFinal && sortedTeams.length >= 2 && (
          <motion.div
            className="flex items-end justify-center gap-2 mb-8"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            {sortedTeams.slice(0, Math.min(3, sortedTeams.length)).map((team, i) => {
              const tIdx = settings.teams.findIndex(t => t.id === team.id);
              const heights = [120, 90, 70];
              const order = i === 0 ? 1 : i === 1 ? 0 : 2;
              return (
                <motion.div
                  key={team.id}
                  style={{ order }}
                  className="flex-1 flex flex-col items-center"
                  initial={{ y: 50, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3 + i * 0.1, type: "spring", bounce: 0.4 }}
                >
                  <span className="text-2xl mb-1">{podiumIcons[i]}</span>
                  <p className="text-xs font-bold text-center mb-1 truncate max-w-full px-1">{team.name}</p>
                  <p className="text-lg font-black text-foreground">{team.score}</p>
                  <div
                    className={`w-full rounded-t-xl bg-gradient-to-b ${TEAM_COLORS[tIdx % TEAM_COLORS.length]} opacity-80`}
                    style={{ height: heights[i] - (i * 10) }}
                  />
                </motion.div>
              );
            })}
          </motion.div>
        )}

        {/* Scores list */}
        <div className="space-y-3 mb-6">
          {sortedTeams.map((team, idx) => {
            const tIdx = settings.teams.findIndex(t => t.id === team.id);
            const isWinner = idx === 0 && isFinal;
            const history = teamRoundHistory.find(h => h.team.id === team.id);
            const totalRoundsPlayed = history?.rounds.length ?? 0;

            return (
              <motion.div
                key={team.id}
                data-testid={`scoreboard-team-${idx}`}
                className={`bg-card border rounded-2xl p-4 shadow-sm flex items-center gap-4 ${isWinner ? "border-yellow-400 dark:border-yellow-600 ring-2 ring-yellow-300 dark:ring-yellow-700" : "border-card-border"}`}
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + idx * 0.08 }}
              >
                <div className="text-2xl font-black text-muted-foreground w-8 text-center">
                  {isWinner ? "👑" : `${idx + 1}`}
                </div>
                <div className={`w-3 h-10 rounded-full bg-gradient-to-b ${TEAM_COLORS[tIdx % TEAM_COLORS.length]}`} />
                <div className="flex-1">
                  <p className="font-bold text-foreground">{team.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {history?.correct ?? 0}/{totalRoundsPlayed} correct
                  </p>
                </div>
                <div className={`text-3xl font-black ${TEAM_TEXT_COLORS[tIdx % TEAM_TEXT_COLORS.length]}`}>
                  {team.score}
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Round history */}
        {rounds.slice(0, currentRoundIndex + 1).length > 0 && (
          <motion.div
            className="bg-card border border-card-border rounded-2xl p-4 mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <div className="flex items-center gap-2 mb-3">
              <Film className="w-4 h-4 text-muted-foreground" />
              <p className="text-sm font-bold text-foreground">Round History</p>
            </div>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {rounds.slice(0, currentRoundIndex + 1).map((round, i) => {
                const team = settings.teams.find(t => t.id === round.teamId)!;
                const tIdx = settings.teams.findIndex(t => t.id === round.teamId);
                return (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <div className={`w-2 h-2 rounded-full bg-gradient-to-br ${TEAM_COLORS[tIdx % TEAM_COLORS.length]} flex-shrink-0`} />
                    <span className="text-muted-foreground font-medium w-20 truncate">{team.name}</span>
                    <span className="flex-1 text-foreground truncate">{round.movie.title}</span>
                    <span>{round.guessed ? "✅" : "❌"}</span>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        {isFinal ? (
          <motion.div
            className="space-y-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <div className="text-center mb-4">
              <p className="text-lg font-bold text-foreground">
                🎊 Congratulations, {leader.name}!
              </p>
              <p className="text-muted-foreground text-sm">Winner with {leader.score} points</p>
            </div>
            {onPlayAgain && (
              <button
                data-testid="button-play-again"
                onClick={onPlayAgain}
                className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold text-lg rounded-2xl shadow-lg"
              >
                Play Again
              </button>
            )}
          </motion.div>
        ) : (
          <motion.button
            data-testid="button-continue-game"
            onClick={onContinue}
            className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold text-lg rounded-2xl shadow-lg flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <span>Continue Game</span>
            <ChevronRight className="w-5 h-5" />
          </motion.button>
        )}
      </div>
    </div>
  );
}
