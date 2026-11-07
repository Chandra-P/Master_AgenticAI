# Tagalong UI refresh

## Design direction and scope

Warm ivory and sand replace the gray canvas; deep navy and legible secondary text replace faded grays. Coral remains the brand accent, with a darker action shade for white-text buttons. Sage identifies confirmed choices and planning context, while restrained blue distinguishes assistant evidence. Rounded surfaces, consistent control borders and subtle depth connect all screens. The original logo, existing photos, visible demo labels and product behavior remain.

Only files inside `tagalong/` were changed. No backend, API, schema, service contract, authentication, permission or agent logic changed. No user data, environment files or repository settings were changed. The pre-existing `next-env.d.ts` modification and unrelated `.vscode/` directory are preserved. Publication requires explicit owner approval.

[Before-and-after screenshots](ui-refresh/README.md) include Home, Chat and Itinerary at 1440px and 390px. Screenshots contain synthetic demo data only.

## Reusable design system

`src/app/design-system.css` defines typography, palette, spacing, radii, focus and surface tokens and shared buttons, inputs, tabs, badges, dialogs and feedback. `src/app/visual-refresh.css` applies page-specific composition and responsive rules. Existing component overrides were also updated in all eight existing stylesheets. Global styles now import in a single declared order in the root layout, avoiding different appearances after switching tools. The reservation CSS module stays locally scoped.

| Role | Size |
| --- | --- |
| Page headings | 32–40px |
| Section headings | 24–28px |
| Card titles | 20px |
| Body and inputs | 16px; selected introductory copy 18px |
| Buttons, navigation and labels | 15–16px |
| Dates, locations and supporting metadata | 14–15px |
| Badges and avatar initials | 13px |
| Decorative uppercase labels | 12.5px |

Body line height is 1.6; conversation text uses 1.65–1.7. Responsive rules reflow layouts while preserving readable text. Controls generally have 44–46px target heights, with explicit focus outlines and reduced-motion support. No zoom or transform enlarges the application.

| Pair | Colors | Contrast ratio |
| --- | --- | --- |
| Primary text / ivory | `#20343f` / `#fffdf9` | 12.72:1 |
| Secondary text / canvas | `#52616b` / `#f6f2eb` | 5.74:1 |
| White text / coral action | `#ffffff` / `#bb4334` | 5.30:1 |
| Sage text / sage surface | `#25594e` / `#e8f0e9` | 6.90:1 |
| Accent text / peach | `#a8372a` / `#fbe7df` | 5.42:1 |
| Control boundary / white | `#7e888b` / `#ffffff` | 3.63:1 |
| Focus ring / ivory | `#285f71` / `#fffdf9` | 6.97:1 |

Avatar initials select a foreground according to the saved background's luminance; saved participant colors remain unchanged. Contrast checks inspect actual rendered text on solid surfaces; gradients and photos are additionally reviewed visually. This is targeted visual/accessibility QA, not a claim of complete WCAG certification.

## Complete screen coverage

The source audit covered every file under `src/`, including all routes, the root layout, shared primitives, feature components and conditional views. Services/API routes were inspected only to identify presentation modes; their behavior was preserved.

All nine UI routes were reviewed at **1440px, 1024px and 390px**:

| Route / state | Presentation and interactions reviewed |
| --- | --- |
| `/` | Illustrated split planning hero; populated and empty next-action/history cards; photo covers; filter selection; group insights; reviewed AI draft and manual creation |
| `/welcome` | Landing hero, original coast photo, floating note, feature panels and CTAs |
| `/discover` | Demo suggestion cards, search/category controls, no-results state and plan picker; connected destination/category filters, synthetic venue result, unavailable-photo fallback and place/date dialog |
| `/itinerary` | All-plan itinerary summaries, dates, activity counts and navigation |
| `/groups` | Saved groups, roster cards, active/archived filters, empty state, creation/editor, optional adult details, removal confirmation and group selection for planning |
| `/account` | Demo account; Member/Admin sign-in; signup; signed-in profile; role choices; reset request; expired and verified recovery forms |
| `/admin` | Access-denied state, overview, account/plan lists, action reason, private inspection, story library and expanded replay |
| `/join` | Missing-link state, connected join surface; valid private-link acceptance also exercised by the existing multi-user regression suite |
| `/plans/[id]` | All three demo plans, connected owner/member headers, working details, roster, nine tabs, participant/invitation controls and owner transfer/delete dialogs |
| Missing plan / unknown route | Missing-plan and not-found screens |
| Transient UI | Workspace loading, service/configuration failure, success toast, selected controls, keyboard focus and mobile navigation |

All planning tools were reviewed in **demo and connected fixture modes**:

- **Decisions:** summary panels, response controls, option selection, evidence, comments, creation/edit dialogs, final review and responsive planning-assistant drawer.
- **Chat:** sender identities, readable timestamps, participant initials, human/assistant message surfaces, evidence, typing help, composer and send/mention controls.
- **Planning board:** date/budget/destination facts, proposed/confirmed preferences, tasks, edit-details dialog and compact chat companion.
- **Polls:** readable options/counts/percentages, selected-vote treatment, vote feedback and poll creation.
- **Discover:** photos, venue cards, filters, source information, activity-saving and venue-fit dialogs.
- **Itinerary:** clear day labels, time rail, category/date metadata, activity surfaces, image/link states and activity creation. Activity order and saved dates were preserved.
- **Documents:** entry form, empty list and expanded saved synthetic note.
- **Demo bookings:** clearly identified fictional reservation workflow, form fields, readiness and result surfaces. Existing regressions cover review, confirmation and cancellation using the local demo MCP service.
- **Group fit:** option/menu form, notices, result, source links and expanded evidence.

Shared navigation, buttons, inputs, selects, textareas, badges, avatars, dialogs, cards, focus and feedback styles apply to the entire application. API routes `/api/config`, `/api/health` and `/api/backend/[...path]` have no visual screens and were not modified. The generic application error boundary was reviewed in source; configuration/service errors were rendered in browser tests.

## Validation

The requested lint, typecheck, production build and frontend suite were run from `tagalong/`. Additional shared-workspace and backend checks use the existing synthetic fixtures and fake providers. No paid provider, production account, real email, reservation, calendar or production database operation was used.

| Check | Result |
| --- | --- |
| `npm run lint` | Passed, no warnings |
| `npm run typecheck` | Passed |
| `npm run build` | Passed, including standalone asset packaging |
| `npm test -- --workers=4` | 148 passed; four duplicate mobile visual runs skipped because each visual test explicitly loops through all three widths |
| Focused final visual audits | Four demo visual tests and four connected visual tests passed after final screenshot refinements |
| `npm run test:shared` | 42 passed; four duplicate mobile visual runs skipped because these checks explicitly cover desktop, tablet and mobile within each test |
| Backend `.venv/bin/python -m pytest tests -q` | 210 passed, one gated real-database test skipped |
| `git diff --check` | Passed |

Browser runs used `TAGALONG_TEST_BROWSER_CHANNEL=chromium` and the local `PLAYWRIGHT_BROWSERS_PATH` override. Both options leave the default browser configuration unchanged when unset. Tests inspect minimum text/input sizes, text contrast on solid surfaces, clipped buttons and document overflow. Gradients, imagery and representative route/dialog screenshots were also inspected visually.

## Limitations

- Live Supabase email delivery, production data, external inventory and paid AI services were not exercised. Connected visual checks use the project's explicit local test adapters.
- The real-database integration test is gated by a disposable test database and remains skipped when that configuration is absent.
- Browser checks use Chromium; other browser engines and a formal screen-reader audit were not part of this task.

## Changed files

The following 43 files are the complete task manifest, including the twelve comparison images. The unrelated pre-existing `next-env.d.ts` modification is excluded.

- [docs/UI_REFRESH.md](../docs/UI_REFRESH.md)
- [docs/ui-refresh/README.md](../docs/ui-refresh/README.md)
- [docs/ui-refresh/after/chat-1440.png](../docs/ui-refresh/after/chat-1440.png)
- [docs/ui-refresh/after/chat-390.png](../docs/ui-refresh/after/chat-390.png)
- [docs/ui-refresh/after/home-1440.png](../docs/ui-refresh/after/home-1440.png)
- [docs/ui-refresh/after/home-390.png](../docs/ui-refresh/after/home-390.png)
- [docs/ui-refresh/after/itinerary-1440.png](../docs/ui-refresh/after/itinerary-1440.png)
- [docs/ui-refresh/after/itinerary-390.png](../docs/ui-refresh/after/itinerary-390.png)
- [docs/ui-refresh/before/chat-1440.png](../docs/ui-refresh/before/chat-1440.png)
- [docs/ui-refresh/before/chat-390.png](../docs/ui-refresh/before/chat-390.png)
- [docs/ui-refresh/before/home-1440.png](../docs/ui-refresh/before/home-1440.png)
- [docs/ui-refresh/before/home-390.png](../docs/ui-refresh/before/home-390.png)
- [docs/ui-refresh/before/itinerary-1440.png](../docs/ui-refresh/before/itinerary-1440.png)
- [docs/ui-refresh/before/itinerary-390.png](../docs/ui-refresh/before/itinerary-390.png)
- [playwright.config.ts](../playwright.config.ts)
- [playwright.integration.config.ts](../playwright.integration.config.ts)
- [src/app/coordination.css](../src/app/coordination.css)
- [src/app/design-system.css](../src/app/design-system.css)
- [src/app/globals.css](../src/app/globals.css)
- [src/app/layout.tsx](../src/app/layout.tsx)
- [src/app/visual-refresh.css](../src/app/visual-refresh.css)
- [src/components/travel-motif.tsx](../src/components/travel-motif.tsx)
- [src/features/planning/chat.tsx](../src/features/planning/chat.tsx)
- [src/features/planning/decisions/decision-plan-card.tsx](../src/features/planning/decisions/decision-plan-card.tsx)
- [src/features/planning/decisions/decisions-panel.tsx](../src/features/planning/decisions/decisions-panel.tsx)
- [src/features/planning/decisions/decisions.css](../src/features/planning/decisions/decisions.css)
- [src/features/planning/decisions/home.css](../src/features/planning/decisions/home.css)
- [src/features/planning/demo-bookings.module.css](../src/features/planning/demo-bookings.module.css)
- [src/features/planning/group-editor.tsx](../src/features/planning/group-editor.tsx)
- [src/features/planning/group-fit.css](../src/features/planning/group-fit.css)
- [src/features/planning/group-fit.tsx](../src/features/planning/group-fit.tsx)
- [src/features/planning/itinerary.tsx](../src/features/planning/itinerary.tsx)
- [src/features/planning/live-discover.tsx](../src/features/planning/live-discover.tsx)
- [src/features/planning/place-cards.css](../src/features/planning/place-cards.css)
- [src/features/planning/proactive-home.tsx](../src/features/planning/proactive-home.tsx)
- [src/features/planning/shared.tsx](../src/features/planning/shared.tsx)
- [src/features/planning/typing-suggestions.css](../src/features/planning/typing-suggestions.css)
- [src/features/planning/typing-suggestions.tsx](../src/features/planning/typing-suggestions.tsx)
- [src/lib/avatar-contrast.ts](../src/lib/avatar-contrast.ts)
- [tests/shared-ui-refresh.spec.ts](../tests/shared-ui-refresh.spec.ts)
- [tests/ui-refresh.helpers.ts](../tests/ui-refresh.helpers.ts)
- [tests/ui-refresh.spec.ts](../tests/ui-refresh.spec.ts)
- [tests/ui-refresh.visual.spec.ts](../tests/ui-refresh.visual.spec.ts)
