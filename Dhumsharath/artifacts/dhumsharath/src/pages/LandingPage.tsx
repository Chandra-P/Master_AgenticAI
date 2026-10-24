import { Link } from "wouter";
import { ChevronRight, Clapperboard, Clock, Trophy, Users } from "lucide-react";
import { teluguMovies } from "@/data/movies";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-orange-50 via-amber-50 to-red-50" />
      <div className="relative z-10 text-center max-w-lg">
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-orange-100 text-orange-600">
          <Clapperboard className="h-11 w-11" aria-hidden="true" />
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-foreground mb-3 tracking-tight">
          Indian Dumb Charades
        </h1>
        <p className="text-xl font-bold text-primary mb-2">ధుమ్ షారాత్</p>
        <p className="text-muted-foreground text-lg mb-2">Act out movies without speaking!</p>
        <p className="text-muted-foreground text-sm mb-8">
          {teluguMovies.length.toLocaleString()} movies across six languages
        </p>
        <div className="flex flex-wrap justify-center gap-3 mb-9">
          {[
            { Icon: Users, label: "2–6 teams" },
            { Icon: Clock, label: "Beat the clock" },
            { Icon: Trophy, label: "Win points" },
          ].map(({ Icon, label }) => (
            <div key={label} className="flex items-center gap-2 bg-card border border-card-border rounded-full px-4 py-2 text-sm font-medium shadow-sm">
              <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
              <span>{label}</span>
            </div>
          ))}
        </div>
        <Link href="/sign-up" data-testid="link-create-account" className="inline-flex items-center gap-3 bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold text-lg px-8 py-4 rounded-2xl shadow-lg hover:shadow-xl transition-shadow">
          Create an account to play
          <ChevronRight className="h-5 w-5" aria-hidden="true" />
        </Link>
        <p className="mt-5 text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/sign-in" data-testid="link-sign-in" className="font-semibold text-orange-700 hover:underline">Sign in</Link>
        </p>
        <p className="mt-6 text-xs text-muted-foreground">Sign-in is required to start a game.</p>
      </div>
    </main>
  );
}
