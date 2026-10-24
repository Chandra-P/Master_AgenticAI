import { useState } from "react";
import { motion } from "framer-motion";
import { Users, Clock, Trophy, ChevronRight, Plus, Trash2 } from "lucide-react";
import type { GameSettings, Team } from "@/data/gameTypes";
import { TEAM_COLORS } from "@/data/gameTypes";
import { getMoviesForLanguage, teluguMovies } from "@/data/movies";
import type { MovieLanguage } from "@/data/movies";
import LanguageSelector from "@/components/LanguageSelector";

interface SetupPageProps {
  onStart: (settings: GameSettings) => void;
}

const defaultTeams: Team[] = [
  { id: "t1", name: "Team A", score: 0, color: TEAM_COLORS[0] },
  { id: "t2", name: "Team B", score: 0, color: TEAM_COLORS[1] },
];

export default function SetupPage({ onStart }: SetupPageProps) {
  const [teams, setTeams] = useState<Team[]>(defaultTeams);
  const [roundsPerTeam, setRoundsPerTeam] = useState(3);
  const [timePerRound, setTimePerRound] = useState(60);
  const [movieLanguage, setMovieLanguage] = useState<MovieLanguage | null>(null);
  const [useCustomTime, setUseCustomTime] = useState(false);
  const [customTimeInput, setCustomTimeInput] = useState("75");
  const [step, setStep] = useState<"welcome" | "config">("welcome");
  const customTime = Number(customTimeInput);
  const isValidCustomTime =
    Number.isInteger(customTime) && customTime >= 10 && customTime <= 300;
  const moviePoolSize = getMoviesForLanguage(movieLanguage).length;

  const addTeam = () => {
    if (teams.length >= 6) return;
    const newTeam: Team = {
      id: `t${Date.now()}`,
      name: `Team ${String.fromCharCode(65 + teams.length)}`,
      score: 0,
      color: TEAM_COLORS[teams.length % TEAM_COLORS.length],
    };
    setTeams([...teams, newTeam]);
  };

  const removeTeam = (id: string) => {
    if (teams.length <= 2) return;
    setTeams(teams.filter(t => t.id !== id));
  };

  const updateTeamName = (id: string, name: string) => {
    setTeams(teams.map(t => t.id === id ? { ...t, name } : t));
  };

  const handleStart = () => {
    if (useCustomTime && !isValidCustomTime) return;
    onStart({
      teams,
      roundsPerTeam,
      timePerRound: useCustomTime ? customTime : timePerRound,
      movieLanguage,
    });
  };

  if (step === "welcome") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-orange-50 via-amber-50 to-red-50 dark:from-orange-950/30 dark:via-amber-950/20 dark:to-red-950/30" />
        <div className="absolute top-10 right-10 w-40 h-40 bg-orange-200/40 dark:bg-orange-800/20 rounded-full blur-3xl" />
        <div className="absolute bottom-10 left-10 w-56 h-56 bg-yellow-200/40 dark:bg-yellow-800/20 rounded-full blur-3xl" />
        <div className="absolute top-1/3 left-1/4 w-24 h-24 bg-red-200/30 dark:bg-red-800/20 rounded-full blur-2xl" />

        <motion.div
          className="relative z-10 text-center max-w-lg"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <motion.div
            className="text-7xl mb-6"
            animate={{ rotate: [0, -10, 10, -5, 5, 0] }}
            transition={{ duration: 1.5, delay: 0.5, ease: "easeInOut" }}
          >
            🎬
          </motion.div>

          <h1 className="text-4xl sm:text-5xl font-black text-foreground mb-3 tracking-tight">
            Indian Dumb Charades
          </h1>
          <p className="text-xl font-bold text-primary mb-2">ధుమ్ షారాత్</p>
          <p className="text-muted-foreground text-lg mb-2">Act out movies without speaking!</p>
          <p className="text-muted-foreground/70 text-sm mb-10">
            {teluguMovies.length.toLocaleString()} distinct movies — Telugu, Hindi, Tamil, Malayalam & more
          </p>

          <div className="flex flex-wrap justify-center gap-3 mb-10">
            {[
              { icon: "🎭", label: "Act It Out" },
              { icon: "⏱️", label: "Beat the Clock" },
              { icon: "🏆", label: "Win Points" },
              { icon: "🔍", label: "Pick Any Movie" },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2 bg-card border border-card-border rounded-full px-4 py-2 text-sm font-medium shadow-sm"
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>

          <motion.button
            data-testid="button-start-game"
            onClick={() => setStep("config")}
            className="group flex items-center gap-3 mx-auto bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold text-lg px-10 py-4 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200"
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.97 }}
          >
            <span>Let's Play!</span>
            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </motion.button>

          <p className="mt-6 text-xs text-muted-foreground">2–6 teams · Customizable rounds & timer</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 sm:p-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-orange-50 via-amber-50 to-red-50 dark:from-orange-950/20 dark:via-amber-950/10 dark:to-red-950/20" />

      <div className="relative z-10 max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center"
        >
          <button
            onClick={() => setStep("welcome")}
            className="text-muted-foreground hover:text-foreground text-sm mb-4 transition-colors"
          >
            ← Back
          </button>
          <h2 className="text-3xl font-black text-foreground">Game Setup</h2>
          <p className="text-muted-foreground mt-1">Customize your game</p>
        </motion.div>

        <div className="space-y-5">
          {/* Teams */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-card border border-card-border rounded-2xl p-5 shadow-sm"
          >
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                <Users className="w-4 h-4 text-orange-600 dark:text-orange-400" />
              </div>
              <h3 className="font-bold text-foreground text-lg">Teams</h3>
              <span className="text-muted-foreground text-sm ml-auto">{teams.length}/6</span>
            </div>

            <div className="space-y-3 mb-4">
              {teams.map((team, idx) => (
                <motion.div
                  key={team.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex items-center gap-3"
                >
                  <div className={`w-4 h-4 rounded-full bg-gradient-to-br ${team.color} flex-shrink-0`} />
                  <input
                    data-testid={`input-team-name-${idx}`}
                    type="text"
                    value={team.name}
                    onChange={(e) => updateTeamName(team.id, e.target.value)}
                    className="flex-1 bg-background border border-input rounded-xl px-4 py-2.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-ring transition-all"
                    placeholder={`Team ${idx + 1} name`}
                    maxLength={20}
                  />
                  <button
                    data-testid={`button-remove-team-${idx}`}
                    onClick={() => removeTeam(team.id)}
                    disabled={teams.length <= 2}
                    className="w-9 h-9 flex items-center justify-center rounded-xl text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </motion.div>
              ))}
            </div>

            {teams.length < 6 && (
              <button
                data-testid="button-add-team"
                onClick={addTeam}
                className="flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Team
              </button>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="bg-card border border-card-border rounded-2xl p-5 shadow-sm"
          >
            <LanguageSelector
              value={movieLanguage}
              onChange={setMovieLanguage}
              testIdPrefix="setup-language"
            />
            <p className="mt-3 text-xs text-muted-foreground">
              Random movies will come from {movieLanguage ?? "all languages"}.
            </p>
          </motion.div>

          {/* Rounds */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-card border border-card-border rounded-2xl p-5 shadow-sm"
          >
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                <Trophy className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="font-bold text-foreground text-lg">Rounds per Team</h3>
            </div>
            <div className="flex gap-2 flex-wrap">
              {[1, 2, 3, 4, 5, 6, 8, 10].map(n => (
                <button
                  key={n}
                  data-testid={`button-rounds-${n}`}
                  onClick={() => setRoundsPerTeam(n)}
                  className={`w-12 h-12 rounded-xl font-bold text-lg transition-all ${
                    roundsPerTeam === n
                      ? "bg-primary text-primary-foreground shadow-md scale-105"
                      : "bg-muted text-muted-foreground hover:bg-muted/70"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </motion.div>

          {/* Time */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="bg-card border border-card-border rounded-2xl p-5 shadow-sm"
          >
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                <Clock className="w-4 h-4 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="font-bold text-foreground text-lg">Time per Round</h3>
            </div>
            <div className="flex gap-2 flex-wrap">
              {[30, 45, 60, 90, 120].map(t => (
                <button
                  key={t}
                  data-testid={`button-time-${t}`}
                  aria-pressed={!useCustomTime && timePerRound === t}
                  onClick={() => {
                    setTimePerRound(t);
                    setUseCustomTime(false);
                  }}
                  className={`px-4 h-11 rounded-xl font-bold text-sm transition-all ${
                    !useCustomTime && timePerRound === t
                      ? "bg-primary text-primary-foreground shadow-md scale-105"
                      : "bg-muted text-muted-foreground hover:bg-muted/70"
                  }`}
                >
                  {t}s
                </button>
              ))}
              <button
                type="button"
                data-testid="button-time-custom"
                aria-pressed={useCustomTime}
                onClick={() => setUseCustomTime(true)}
                className={`px-4 h-11 rounded-xl font-bold text-sm transition-all ${
                  useCustomTime
                    ? "bg-primary text-primary-foreground shadow-md scale-105"
                    : "bg-muted text-muted-foreground hover:bg-muted/70"
                }`}
              >
                Custom
              </button>
            </div>
            {useCustomTime && (
              <div className="mt-4 max-w-xs">
                <label htmlFor="custom-round-time" className="mb-2 block text-sm font-medium text-foreground">
                  Round duration
                </label>
                <div className="flex items-center gap-3">
                  <input
                    id="custom-round-time"
                    data-testid="input-custom-round-time"
                    type="number"
                    inputMode="numeric"
                    min={10}
                    max={300}
                    step={1}
                    required
                    value={customTimeInput}
                    aria-invalid={!isValidCustomTime}
                    aria-describedby="custom-round-time-help"
                    onChange={(event) => setCustomTimeInput(event.target.value)}
                    className="h-11 w-28 rounded-xl border border-input bg-background px-3 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <span className="text-sm text-muted-foreground">seconds</span>
                </div>
                <p id="custom-round-time-help" className="mt-2 text-xs text-muted-foreground">
                  Choose a whole number from 10 to 300 seconds.
                </p>
                {!isValidCustomTime && (
                  <p role="alert" className="mt-1 text-xs font-medium text-destructive">
                    Enter a whole number between 10 and 300.
                  </p>
                )}
              </div>
            )}
          </motion.div>

          {/* Info note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-2xl p-4"
          >
            <p data-testid="movie-pool-count" className="text-sm text-amber-800 dark:text-amber-300 font-semibold mb-0.5">{moviePoolSize.toLocaleString()} distinct movies in the {movieLanguage ?? "all-language"} pool</p>
            <p className="text-xs text-amber-700 dark:text-amber-400">
              Your language choice applies to every random round. Before each round, the actor can also search and pick a specific movie.
            </p>
          </motion.div>

          <motion.button
            data-testid="button-start-setup"
            onClick={handleStart}
            disabled={useCustomTime && !isValidCustomTime}
            className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold text-lg rounded-2xl shadow-lg hover:shadow-xl transition-all"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            Start Game!
          </motion.button>
        </div>
      </div>
    </div>
  );
}
