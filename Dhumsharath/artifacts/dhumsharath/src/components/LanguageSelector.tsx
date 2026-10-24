import { MOVIE_LANGUAGES } from "@/data/movies";
import type { MovieLanguage } from "@/data/movies";

interface LanguageSelectorProps {
  value: MovieLanguage | null;
  onChange: (language: MovieLanguage | null) => void;
  testIdPrefix: string;
  compact?: boolean;
}

export default function LanguageSelector({
  value, onChange, testIdPrefix, compact = false,
}: LanguageSelectorProps) {
  const options: (MovieLanguage | null)[] = [null, ...MOVIE_LANGUAGES];
  return (
    <fieldset>
      <legend className={`mb-3 font-bold ${compact ? "text-xs text-muted-foreground uppercase tracking-wider" : "text-lg text-foreground"}`}>
        Movie language
      </legend>
      <div className="flex flex-wrap gap-2">
        {options.map(language => (
          <button
            key={language ?? "all"}
            type="button"
            data-testid={`${testIdPrefix}-${language?.toLowerCase() ?? "all"}`}
            aria-pressed={value === language}
            onClick={() => onChange(language)}
            className={`min-h-11 rounded-xl px-3 font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
              compact ? "text-xs" : "text-sm"
            } ${value === language
              ? "bg-primary text-primary-foreground shadow-sm"
              : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            {language ?? "All languages"}
          </button>
        ))}
      </div>
    </fieldset>
  );
}
