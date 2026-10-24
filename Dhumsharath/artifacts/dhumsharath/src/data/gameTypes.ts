import type { Movie, MovieLanguage } from "./movies";

export interface Team {
  id: string;
  name: string;
  score: number;
  color: string;
}

export interface Round {
  roundNumber: number;
  teamId: string;
  movie: Movie;
  timeLimit: number;
  timeUsed?: number;
  guessed: boolean;
  skipped: boolean;
}

export interface GameSettings {
  teams: Team[];
  roundsPerTeam: number;
  timePerRound: number;
  movieLanguage: MovieLanguage | null;
}

export type GamePhase =
  | "setup"
  | "team-setup"
  | "ready"
  | "acting"
  | "result"
  | "scoreboard"
  | "finished";

export interface GameState {
  phase: GamePhase;
  settings: GameSettings;
  rounds: Round[];
  currentRoundIndex: number;
  movieQueue: Movie[];
}

export const TEAM_COLORS = [
  "from-orange-500 to-red-500",
  "from-blue-500 to-indigo-600",
  "from-green-500 to-emerald-600",
  "from-purple-500 to-pink-600",
  "from-yellow-400 to-orange-500",
  "from-teal-500 to-cyan-600",
];

export const TEAM_SOLID_COLORS = [
  "bg-orange-500",
  "bg-blue-500",
  "bg-green-500",
  "bg-purple-500",
  "bg-yellow-500",
  "bg-teal-500",
];

export const TEAM_TEXT_COLORS = [
  "text-orange-500",
  "text-blue-500",
  "text-green-500",
  "text-purple-500",
  "text-yellow-500",
  "text-teal-500",
];
