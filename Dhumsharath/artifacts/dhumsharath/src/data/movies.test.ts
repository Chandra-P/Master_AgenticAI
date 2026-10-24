import assert from "node:assert/strict";
import { test } from "node:test";
import {
  getAllMoviesShuffled,
  getMoviesByDifficulty,
  getMoviesForLanguage,
  searchMovies,
  teluguMovies,
} from "./movies.ts";

const normalizeTitle = (title: string) =>
  title.toLowerCase().replace(/[^a-z0-9]/g, "");

test("catalog IDs and film/year identities are unique", () => {
  const ids = new Set<number>();
  const identities = new Set<string>();
  for (const movie of teluguMovies) {
    assert.ok(Number.isInteger(movie.id) && movie.id > 0);
    assert.ok(!ids.has(movie.id), `Repeated ID: ${movie.id}`);
    ids.add(movie.id);
    // Language versions are explicitly named; years distinguish remakes.
    const identity = `${normalizeTitle(movie.title)}:${movie.year}`;
    assert.ok(!identities.has(identity), `Repeated film: ${movie.title} (${movie.year})`);
    identities.add(identity);
    assert.ok(movie.title.trim());
    assert.ok(Number.isInteger(movie.year));
    assert.ok(movie.genre);
    assert.ok(movie.hint?.trim());
  }
});

test("known spelling, streaming, subtitle, and redundant language aliases stay consolidated", () => {
  const groups = [
    ["HanuMan", "Hanu Man", "HanuMan 2024"],
    ["Pushpa: The Rise", "Pushpa: The Rise OTT", "Pushpa Telugu"],
    ["Pushpa 2: The Rule", "Pushpa Rule"],
    ["Ala Vaikunthapurramuloo", "Ala Vaikunthapurramloo"],
    ["Julayi", "Julai"],
    ["Bhramayugam", "Bramayugam"],
    ["Devara: Part 1", "Devara"],
    ["Kalki 2898 AD", "Kalki 2898"],
    ["Bro", "Bro: The Avatar"],
    ["Ponniyin Selvan 1", "Ponniyin Selvan"],
    ["Gang Leader", "Nani's Gang Leader"],
    ["Devdas", "Devdas 2002"],
    ["Jai Bhim", "Jai Bhim Tamil"],
    ["Stree 2", "Stree 2 Bollywood"],
    ["Merry Christmas", "Merry Christmas Netflix"],
  ];
  for (const titles of groups) {
    const variants = new Set(titles.map(normalizeTitle));
    const years = new Set<number>();
    for (const movie of teluguMovies.filter(m => variants.has(normalizeTitle(m.title)))) {
      assert.ok(!years.has(movie.year), `Repeated alias: ${movie.title} (${movie.year})`);
      years.add(movie.year);
    }
    assert.ok(years.size > 0, `Missing film: ${titles[0]}`);
  }
  assert.equal(teluguMovies.filter(m => m.title === "Drishyam 3").length, 1);
  assert.equal(teluguMovies.find(m => m.title === "Drishyam 3")?.year, 2026);
});

test("remakes, sequels, and distinct language versions retain their stable IDs", () => {
  for (const id of [
    7, 852, // Hindi/Tamil Vikram Vedha
    83, 203, // Gang Leader, 2019/1991
    166, 332, // Telugu/Hindi Ready
    323, 411, // Agneepath, 2012/1990
    358, 400, // Don, 2006/1978
    409, 1047, // Coolie, 1983/2025
    731, 779, // Tamil/Hollywood Joker
    483, 713, 629, 997, // Bombay and Adipurush language versions
    491, 492, 847, 983, // Drishyam originals and language remakes
    23, 976, 421, 426, // Karthikeya and Ponniyin Selvan parts
    143, 914, 894, 968, // Brindavanam/Brindavana and Suicide Squad films
  ]) {
    assert.ok(teluguMovies.some(m => m.id === id), `Missing distinct film ID: ${id}`);
  }
  assert.match(teluguMovies.find(m => m.id === 21)!.hint!, /Nani/);
  assert.match(teluguMovies.find(m => m.id === 183)!.hint!, /Shah Rukh Khan/);
  const hindiIds = new Set(getMoviesForLanguage("Hindi").map(m => m.id));
  assert.ok(hindiIds.has(7), "The retained Hindi Vikram Vedha must remain in the Hindi pool");
  assert.ok(hindiIds.has(183), "The retained Hindi Devdas must remain in the Hindi pool");
});

test("search, difficulty pools, and random selection use the same distinct catalog", () => {
  const originalIds = teluguMovies.map(m => m.id);
  const shuffled = getAllMoviesShuffled();
  assert.notStrictEqual(shuffled, teluguMovies);
  assert.equal(shuffled.length, teluguMovies.length);
  assert.deepEqual(shuffled.map(m => m.id).sort((a, b) => a - b), [...originalIds].sort((a, b) => a - b));
  assert.deepEqual(teluguMovies.map(m => m.id), originalIds, "Shuffle must not mutate the catalog");
  assert.equal(searchMovies("").length, teluguMovies.length);
  assert.equal(searchMovies("HanuMan").length, 1);
  assert.equal(searchMovies("హను-మాన్").length, 1);
  const difficultyPools = (["easy", "medium", "hard"] as const).flatMap(getMoviesByDifficulty);
  assert.equal(difficultyPools.length, teluguMovies.length);
  assert.equal(new Set(difficultyPools.map(m => m.id)).size, teluguMovies.length);
});
