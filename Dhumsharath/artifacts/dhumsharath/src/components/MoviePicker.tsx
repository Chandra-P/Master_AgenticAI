import { useState, useMemo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Film, ChevronRight, Filter, PenLine } from "lucide-react";
import { getMovieLanguage, searchMovies, teluguMovies } from "@/data/movies";
import LanguageSelector from "@/components/LanguageSelector";
import type { Movie, Difficulty, Genre, MovieLanguage } from "@/data/movies";

interface MoviePickerProps {
  initialLanguage?: MovieLanguage | null;
  onSelect: (movie: Movie) => void;
  onClose: () => void;
}

const ALL_GENRES: Genre[] = ["action", "romance", "comedy", "drama", "thriller", "family", "historical", "fantasy", "horror", "sci-fi", "adventure"];
const DIFFICULTIES: Difficulty[] = ["easy", "medium", "hard"];

const difficultyColors: Record<Difficulty, string> = {
  easy: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  medium: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  hard: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

const genreEmojis: Record<Genre, string> = {
  action: "💥", romance: "❤️", comedy: "😂", drama: "🎭",
  thriller: "🔪", family: "👨‍👩‍👧", historical: "📜", fantasy: "✨",
  horror: "👻", "sci-fi": "🚀", adventure: "🧭",
};

export default function MoviePicker({ onSelect, onClose, initialLanguage = null }: MoviePickerProps) {
  const [query, setQuery] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState<Difficulty | null>(null);
  const [selectedGenre, setSelectedGenre] = useState<Genre | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<MovieLanguage | null>(initialLanguage);
  const [showFilters, setShowFilters] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const results = useMemo(() => {
    let movies = query.trim() ? searchMovies(query) : [...teluguMovies];
    if (selectedDifficulty) movies = movies.filter(m => m.difficulty === selectedDifficulty);
    if (selectedGenre) movies = movies.filter(m => m.genre === selectedGenre);
    if (selectedLanguage) movies = movies.filter(m => getMovieLanguage(m) === selectedLanguage);
    return movies.sort((a, b) => b.year - a.year);
  }, [query, selectedDifficulty, selectedGenre, selectedLanguage]);

  const trimmedQuery = query.trim();
  const hasFilters = !!(selectedDifficulty || selectedGenre || selectedLanguage || trimmedQuery);

  const clearFilters = () => {
    setSelectedDifficulty(null);
    setSelectedGenre(null);
    setSelectedLanguage(null);
    setQuery("");
  };

  const handleUseCustom = () => {
    if (!trimmedQuery) return;
    const customMovie: Movie = {
      id: Date.now(),
      title: trimmedQuery,
      year: new Date().getFullYear(),
      genre: "action",
      difficulty: "medium",
    };
    onSelect(customMovie);
  };

  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col bg-background"
      initial={{ opacity: 0, y: "100%" }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: "100%" }}
      transition={{ type: "spring", damping: 30, stiffness: 300 }}
    >
      {/* Header */}
      <div className="flex-shrink-0 bg-card border-b border-card-border px-4 pt-4 pb-3">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xl font-black text-foreground">Pick a Movie</h2>
          <button
            data-testid="button-close-picker"
            onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search bar */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            ref={inputRef}
            data-testid="input-movie-search"
            type="search"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && trimmedQuery) handleUseCustom(); }}
            placeholder="Search or type any movie name..."
            className="w-full pl-10 pr-10 py-3 bg-background border border-input rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-ring transition-all"
          />
          {query && (
            <button onClick={() => setQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* "Use as custom" button — always visible when there's a query */}
        <AnimatePresence>
          {trimmedQuery && (
            <motion.button
              data-testid="button-use-custom-movie"
              onClick={handleUseCustom}
              className="w-full flex items-center gap-3 bg-primary/10 border border-primary/30 text-primary rounded-xl px-4 py-3 mb-3 font-semibold text-sm hover:bg-primary/20 transition-all text-left"
              initial={{ opacity: 0, height: 0, marginBottom: 0 }}
              animate={{ opacity: 1, height: "auto", marginBottom: 12 }}
              exit={{ opacity: 0, height: 0, marginBottom: 0 }}
              transition={{ duration: 0.15 }}
            >
              <PenLine className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1 truncate">
                Use <span className="font-black">"{trimmedQuery}"</span> as custom movie
              </span>
              <ChevronRight className="w-4 h-4 flex-shrink-0 opacity-60" />
            </motion.button>
          )}
        </AnimatePresence>

        <div className="mb-3">
          <LanguageSelector
            value={selectedLanguage}
            onChange={setSelectedLanguage}
            testIdPrefix="filter-language"
            compact
          />
        </div>

        {/* Filter row */}
        <div className="flex items-center gap-2">
          <button
            data-testid="button-toggle-filters"
            onClick={() => setShowFilters(v => !v)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold transition-all ${showFilters ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"}`}
          >
            <Filter className="w-3.5 h-3.5" />
            Filters
          </button>
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="px-3 py-1.5 rounded-lg text-sm font-semibold text-destructive hover:bg-destructive/10 transition-all"
            >
              Clear all
            </button>
          )}
          <span className="ml-auto text-xs text-muted-foreground font-medium">{results.length} movies</span>
        </div>

        {/* Filters panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-3 space-y-3">
                <div>
                  <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Difficulty</p>
                  <div className="flex gap-2">
                    {DIFFICULTIES.map(d => (
                      <button
                        key={d}
                        data-testid={`filter-difficulty-${d}`}
                        onClick={() => setSelectedDifficulty(selectedDifficulty === d ? null : d)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all capitalize ${
                          selectedDifficulty === d
                            ? d === "easy" ? "bg-green-500 text-white" : d === "medium" ? "bg-orange-500 text-white" : "bg-red-500 text-white"
                            : difficultyColors[d]
                        }`}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Genre</p>
                  <div className="flex flex-wrap gap-2">
                    {ALL_GENRES.map(g => (
                      <button
                        key={g}
                        data-testid={`filter-genre-${g}`}
                        onClick={() => setSelectedGenre(selectedGenre === g ? null : g)}
                        className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all capitalize ${
                          selectedGenre === g
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <span>{genreEmojis[g]}</span>
                        <span>{g}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Movie list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {results.length === 0 && !trimmedQuery && (
          <div className="text-center py-16">
            <Film className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground font-medium">No movies found</p>
            <button onClick={clearFilters} className="text-primary text-sm mt-2 hover:underline">Clear filters</button>
          </div>
        )}

        {results.length === 0 && trimmedQuery && (
          <div className="text-center py-10">
            <p className="text-muted-foreground text-sm">No match in the list.</p>
            <p className="text-muted-foreground/70 text-xs mt-1">Tap the button above to use it as a custom movie.</p>
          </div>
        )}

        {results.map((movie) => (
          <motion.button
            key={movie.id}
            data-testid={`movie-item-${movie.id}`}
            onClick={() => onSelect(movie)}
            className="w-full flex items-center gap-3 bg-card border border-card-border rounded-2xl p-3.5 text-left hover:border-primary/40 hover:shadow-sm transition-all group"
            whileTap={{ scale: 0.98 }}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center flex-shrink-0 text-white text-lg font-black">
              {genreEmojis[movie.genre]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-bold text-foreground truncate">{movie.title}</p>
              {movie.teluguTitle && (
                <p className="text-xs text-muted-foreground truncate" style={{ fontFamily: "'Noto Sans Telugu', sans-serif" }}>
                  {movie.teluguTitle}
                </p>
              )}
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-muted-foreground">{movie.year}</span>
                <span className="text-xs text-muted-foreground capitalize">· {movie.genre}</span>
                <span className="text-xs text-muted-foreground">· {getMovieLanguage(movie)}</span>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${difficultyColors[movie.difficulty]}`}>
                {movie.difficulty}
              </span>
              <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
            </div>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
