# Tagalong: from an idea to a group decision

Status: design approved by the owner on November 6; implementation and verification are tracked in the matching plan and DECISION_WORKFLOW.md. Reference examples below remain design examples, not production records. All people and example plans are fictional.

## Product direction

Tagalong helps groups move from idea → options → group response → confirmed decisions → finalized plan → experience. Trips, dinners, celebrations and family outings share this flow. Keep the current coral, graphite, cloud, blue and mint palette, Arial typography, restrained rounded cards, thin borders, spacing and existing shell. Avoid replacing the design system or adding a chat product.

The key product distinction is **working details versus confirmed decisions**. An AI-generated Austin destination, a populated date field, and a leading poll option are working choices. They are not evidence that the group agreed. AI summarizes evidence and recommends actions; people confirm decisions.

## Observed integration points

- `src/features/planning/proactive-home.tsx` implements the current home, coordination overview, recommendations, insights and history. Retain its account/role-keyed lifecycle and accessible-plan filtering.
- `src/features/planning/workspace.tsx` starts on Chat and exposes board/polls/itinerary/documents/discovery/bookings/group-fit tabs. Add Decisions as the default while preserving old links and all existing capabilities.
- `src/features/planning/coordination-card.tsx` reads revision-matched coordination summaries. Reuse this fetching boundary and its stale/error handling.
- `src/services/types.ts` has plans, polls, tasks and messages, but no persisted decision or decision-comment entities.
- `backend/tagalong/coordination.py` computes health from filled dates/location/budget, polls, itinerary and tasks. That is planning completeness; do not relabel this value as consensus.
- `src/features/planning/finalize-review.tsx` explicitly says finishing review does not change shared state. Durable finalization therefore needs a server action; a modal close is insufficient.
- `src/app/globals.css` defines the existing palette and component classes; `@theme inline` already exposes coral/graphite/cloud/blue/mint for Tailwind. Use the current Button/Dialog/Avatars primitives.

These are repository observations. The entities, endpoints and components below are proposals, not descriptions of already shipped functionality.

## 1. Component architecture

```text
Existing Shell / PlanningProvider / connected authentication
├── DecisionHome (adapt proactive-home.tsx)
│   ├── IdeaComposer (adapt PlanGenerator)
│   ├── NextStepsList
│   │   └── NextStepCard
│   └── ContinuePlanning
│       └── DecisionPlanCard
│           ├── ConsensusMeter
│           └── ParticipationStatus
└── Workspace
    ├── PlanHeader + existing invitations / owner controls
    ├── DecisionSummaryCard
    └── Workspace content grid
        ├── DecisionsPanel (default section)
        │   └── DecisionCard
        │       ├── DecisionOptions / VoteControls
        │       ├── ParticipationStatus
        │       ├── EvidenceSummary + source links
        │       └── DecisionComments (collapsed by default)
        ├── Existing Discussion / Itinerary / Discover / Documents / tools
        └── MomentumPanel
            ├── ConsensusMeter
            ├── NextAction
            ├── OpenTasks
            └── GroupInsights
```

Keep canonical state in services/provider. Components receive typed view models and callbacks. Compute progress once in the backend and once in a deterministic demo adapter using the same fixtures/contract; do not implement different scoring logic in every card. Preserve the real member IDs, Admin/Member separation and local-demo boundary. Contacts from reusable demo groups never enter decision context.

Suggested files under `src/features/planning/decisions/`: `decision-home.tsx`, `idea-composer.tsx`, `next-step-card.tsx`, `decision-plan-card.tsx`, `consensus-meter.tsx`, `decision-summary-card.tsx`, `decisions-panel.tsx`, `decision-card.tsx`, `decision-comments.tsx`, `momentum-panel.tsx`. Put contracts/client in `src/services/decisions.ts` and demo derivation in `src/services/demo-decisions.ts`. Avoid enlarging the compressed workspace component with all new UI.

## 2. Updated layouts and interactions

### Homepage

```text
Existing shell and personal greeting

Good company starts here.
Turn group chats into plans.
Describe an idea in one sentence. Tagalong organizes decisions,
gathers preferences, and helps your group move forward.

[ Large, labeled idea textarea                              ]
[ Weekend trip to Austin with 6 friends                     ]
[ Dinner Friday night for 8 people ] [ Birthday brunch ... ]
                                             [ Start Planning ]

Your next steps
[ Waiting on votes ] [ Destination undecided ] [ Ready to finalize ]
  Plan name            Plan name                 Plan name
  Blocker              Blocker                   Blocker
  4 of 6 responded     3 options proposed        6 of 6 responded
  Review lodging →     Compare destinations →    Review final plan →

Continue planning                            All / Trips / Outings
[ Plan name / consensus / people / decisions / action / activity ]

Optional collapsed group insights; existing Discover link
```

The textarea uses the first supplied example as a stable placeholder and displays all four examples as clickable chips. Do not rotate placeholder text while someone types. Clicking a chip fills the textarea without submitting. Connected mode retains the existing generated-draft review before plan creation; label the submit CTA **Start Planning**. Demo mode uses a clearly simulated draft path with the same composer, rather than claiming live AI. Empty/error/loading states retain typed input and offer manual creation.

Next-step cards appear above history. Prefer the current user's outstanding vote, then unresolved decisions, then final review. Show no more than three cards, with a link to all actions. Never infer nonparticipation from someone not writing chat messages. Count eligible decision responses. “Waiting on Sarah and Mike” must come from missing current-version responses, not generated prose.

Plan cards display name, consensus meter, actual member count, completed/remaining required decision counts, completed labels, pending labels, next action, missing responders and last recorded activity. If there are many decisions, show two labels plus “3 more.” Last activity comes from server activity timestamps; unavailable timestamps display “Activity not available.” Avoid using React render time or a message's time-of-day string as historical evidence.

### Plan details

```text
All plans / Plan name / members / Invite / owner controls

[ AI Summary                                             ]
[ Completed: Austin · Apr 19–21 · budget                  ]
[ Remaining: lodging · activities                        ]
[ Agreement: 6 members support Austin                    ]
[ Action: 2 members still need to respond to lodging      ]
[ Recommendation: Review lodging responses →             ]

Decisions | Discussion | Itinerary | Explore | Documents | More tools

Main column                              Persistent side panel
[ Destination · Confirmed              ] Group momentum
[ Dates · Confirmed                    ] Consensus + explanation
[ Budget · Confirmed                   ] Suggested next action
[ Lodging · Awaiting responses         ] Open tasks
[ options / votes / comments / summary ] Evidence-based insights
[ Activities · Needs options           ]
```

The summary has separate Completed decisions, Remaining decisions, Areas of agreement, Requires action and Suggested next step groups. Compact lists show two items before expanding. Display generated-at time, evidence links and summary status. Stale summaries are visibly marked and cannot supply authoritative counts or permissions. Fallback says **Plan summary**, never “AI Summary” when no model produced it.

Decision cards always contain status, selected/proposed option, participation, vote distribution, comment count and summary/evidence area. Use statuses **Needs options**, **Awaiting responses**, **Needs discussion**, **Ready to confirm**, **Confirmed**, **Reopened**. Show “No comments yet” and “Summary not available” rather than inventing content.

Comments open inside the relevant decision card/drawer. Include author, timestamp and decision/option version. A comment may express a concern; it is never counted as a ballot or approval. Editing an option invalidates relevant earlier responses and marks summaries stale. An AI synthesis such as “Most members prefer downtown despite parking concerns” must link to its ballots/comments and preserve unresolved objections.

The persistent panel offers Group Momentum, Consensus Score, Suggested Next Action, Open Tasks and Insights. CTAs navigate to a decision anchor, open a vote or open final review. “Review missing responses” opens the eligible-member list; do not show “Reminder sent” without an implemented, authorized delivery action. No new notification provider is required for the first iteration.

## 3. Consensus contract

Use the requested labels: **0–30% Early Discussion**, **31–70% Narrowing Options**, **71–99% Almost Ready**, **100% Finalized**.

Use a fixed set of required decisions for each plan, explicitly reviewed by its owner. Trip defaults: destination, dates, budget, lodging, activities. Dinner/date/brunch defaults: place, date/time, budget and activity/meal; do not require a hotel for dinner. Optional decisions do not silently inflate the denominator. Marking lodging not applicable requires an explicit recorded change; AI cannot remove blockers.

Recommended initial policy: full participation and consent. Ballots use stable member/option IDs and responses `support`, `can_live_with`, `object`, `abstain`. Every eligible member must respond before confirmation. An objection blocks confirmation. Abstention counts participation, but is not agreement. At least one non-abstaining member must consent to the selected option; all non-abstaining members must consent to it. Different supported options remain unresolved until members respond to the same candidate. Do not claim unanimity when people abstained.

For each required decision, contribution is 1 if confirmed; otherwise the fraction of eligible non-abstaining members consenting to the leading option on the current version. If no eligible/non-abstaining members or no options exist, contribution is 0. Multiply the mean contribution by 100, round and cap at 99 until the owner explicitly finalizes a valid current snapshot. Always label this **consensus progress**, with tooltip: “Agreement toward required decisions. 100% means this plan was explicitly finalized; it does not mean everything is booked.” Show “All decisions confirmed · final review needed” at 99 when appropriate.

Planning completeness and consensus remain separate metrics. A detailed itinerary with no votes can have high completeness and low consensus. Unanswered participants remain visible even if all received votes support one option. Example: 4 of 6 consent to the same option is 67% agreement with 2 responses missing, not consensus reached.

Finalization requires all required decisions confirmed on current versions; plan outline reviewed; no unresolved decision objections; current membership and revision; authorized owner action. Post-finalization decision edits reopen finalization and return the score below 100. Booking readiness remains a separate server-enforced check; approved decisions do not themselves authorize a booking, payment or outbound message.

## 4. React and Tailwind reference implementation

These examples are design references to adapt into the existing components after approval. They introduce no package dependency. Use real server results for the view model; do not copy the sample data into a connected user's state.

```tsx
// consensus-meter.tsx
type Consensus = { score: number; finalized: boolean };

export function ConsensusMeter({ score, finalized }: Consensus) {
  const value = finalized ? 100 : Math.min(99, Math.max(0,
    Number.isFinite(score) ? Math.round(score) : 0));
  const label = value === 100 ? 'Finalized' : value > 70 ? 'Almost Ready'
    : value > 30 ? 'Narrowing Options' : 'Early Discussion';
  return (
    <div className="min-w-0 space-y-2">
      <div className="flex flex-wrap justify-between gap-2 text-sm">
        <span className="font-semibold">Consensus {value}%</span>
        <span className="text-[var(--muted)]">{label}</span>
      </div>
      <div role="progressbar" aria-label="Group consensus"
        aria-valuemin={0} aria-valuemax={100} aria-valuenow={value}
        aria-valuetext={`${value}% — ${label}`}
        className="h-2 overflow-hidden rounded-full bg-cloud">
        <div className="h-full rounded-full bg-[var(--coral)]"
          style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
```

```tsx
// decision-plan-card.tsx
import Link from 'next/link';
import { ArrowRight, Check } from 'lucide-react';
import { ConsensusMeter } from './consensus-meter';

export type PlanCardModel = {
  id: string; title: string; score: number; finalized: boolean;
  participantCount: number; completed: string[]; pending: string[];
  nextAction: { label: string; href: string };
  waitingOn: string[]; lastActivity: string;
};

export function DecisionPlanCard({ plan }: { plan: PlanCardModel }) {
  return (
    <article className="flex min-w-0 flex-col gap-5 rounded-xl border
      border-[var(--line)] bg-white p-5 sm:p-6">
      <div>
        <h3 className="break-words text-lg font-semibold">
          <Link href={`/plans/${encodeURIComponent(plan.id)}`}>
            {plan.title}
          </Link>
        </h3>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {plan.participantCount} participants
        </p>
      </div>
      <ConsensusMeter score={plan.score} finalized={plan.finalized} />
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="mb-2 font-semibold">{plan.completed.length} completed</p>
          <ul className="space-y-1">
            {plan.completed.slice(0, 2).map(label => (
              <li key={label} className="flex gap-2">
                <Check size={16} aria-hidden="true" />{label}
              </li>
            ))}
          </ul>
          {plan.completed.length > 2 && <p>+{plan.completed.length - 2} more</p>}
        </div>
        <div>
          <p className="mb-2 font-semibold">{plan.pending.length} remaining</p>
          <ul className="space-y-1">
            {plan.pending.slice(0, 2).map(label => <li key={label}>{label}</li>)}
          </ul>
          {plan.pending.length > 2 && <p>+{plan.pending.length - 2} more</p>}
        </div>
      </div>
      <p className="text-sm text-[var(--muted)]">
        {plan.waitingOn.length ? `Waiting on ${plan.waitingOn.join(', ')}`
          : 'No outstanding responses'}
      </p>
      <Link href={plan.nextAction.href} className="btn btn-outline mt-auto
        min-h-11 justify-between whitespace-normal text-left">
        {plan.nextAction.label}<ArrowRight size={16} aria-hidden="true" />
      </Link>
      <p className="text-xs text-[var(--muted)]">{plan.lastActivity}</p>
    </article>
  );
}
```

```tsx
// decision-card.tsx — callbacks perform authorized, revision-checked writes
'use client';
import { useId, useState } from 'react';
import { Button } from '@/components/ui/button';

type DecisionView = {
  id: string; title: string; status: string; selectedOption: string | null;
  responseCount: number; eligibleCount: number; commentCount: number;
  summary: string | null; summaryIsLive: boolean; summaryIsStale: boolean;
  sources: { id: string; label: string; href: string }[];
};

export function DecisionCard({ decision, pending, comments, onRespond }:
  { decision: DecisionView; pending: boolean; comments: React.ReactNode;
    onRespond: () => void }) {
  const titleId = useId();
  const commentsId = useId();
  const [expanded, setExpanded] = useState(false);
  return (
    <article id={`decision-${decision.id}`} aria-labelledby={titleId}
      className="scroll-mt-24 rounded-xl border border-[var(--line)] bg-white p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 id={titleId} className="text-lg">{decision.title}</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {decision.selectedOption || 'No option selected'}
          </p>
        </div>
        <span className="rounded-full bg-cloud px-3 py-1 text-xs">
          {decision.status}
        </span>
      </div>
      <p className="my-4 text-sm">
        {decision.responseCount} of {decision.eligibleCount} responded
      </p>
      <section className="rounded-lg bg-cloud p-4">
        <h4 className="text-sm font-semibold">
          {decision.summaryIsLive ? 'AI summary' : 'Decision summary'}
          {decision.summaryIsStale && ' · Needs refresh'}
        </h4>
        <p className="mt-2 text-sm">{decision.summary || 'Summary not available yet.'}</p>
        <ul className="mt-2 flex flex-wrap gap-3 text-xs">
          {decision.sources.map(source => <li key={source.id}>
            <a className="underline underline-offset-4" href={source.href}>
              {source.label}
            </a>
          </li>)}
        </ul>
      </section>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button disabled={pending} onClick={onRespond}>Review options and respond</Button>
        <button type="button" aria-expanded={expanded} aria-controls={commentsId}
          className="min-h-11 px-2 text-sm underline underline-offset-4"
          onClick={() => setExpanded(value => !value)}>
          {decision.commentCount} comments
        </button>
      </div>
      <div id={commentsId} hidden={!expanded} className="mt-5 border-t
        border-[var(--line)] pt-5">{comments}</div>
    </article>
  );
}
```

Use internal, server-generated source links in the last example. External URLs must pass the existing safe-URL validation. Render comments as text, not HTML. Wire buttons to existing Dialog primitives for option review, confirmation and failure reporting; retain focus restoration and pending-state protection.

### Layout utilities

```tsx
// Homepage cards: one column on phones, then two, then three
<div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
  {/* NextStepCard or DecisionPlanCard instances */}
</div>

// Workspace: sidebar is persistent only where the content fits.
<div className="grid min-w-0 grid-cols-1 gap-6 p-5
  lg:grid-cols-[minmax(0,1fr)_19rem] lg:p-8">
  <section aria-label="Decisions" className="min-w-0 space-y-4">
    {/* Decision cards */}
  </section>
  <aside aria-label="AI planning assistant" className="min-w-0
    self-start lg:sticky lg:top-24 lg:max-h-[calc(100dvh-7rem)] lg:overflow-y-auto">
    {/* MomentumPanel */}
  </aside>
</div>
```

Do not change the global font or theme tokens. Reuse `.btn` through Button and preserve current shell offsets. Use existing page padding as the outer boundary; avoid doubling it when applying these utilities. Component-level readability should use 12–14px secondary text, rather than extending the current tiny mobile labels.

## 5. Responsive and accessible behavior

- At 320–767px use one-column cards, wrapped labels and stacked CTAs. Keep consensus and next action visible above the decision list. Put the full assistant in a labeled, keyboard-accessible drawer with a 44px **Planning assistant** trigger. It must not cover the existing bottom navigation.
- At tablet widths use two-column home cards and a single workspace column until enough width exists for the 19rem sidebar. At desktop keep summary above the grid and sidebar sticky within available viewport height; sidebar sections can collapse.
- Preserve 44px interaction targets, visible keyboard focus, proper field labels, logical heading order and text equivalents for color/status icons. Vote choices use a radio group, not clickable unlabelled divs.
- Use a textual label and numeric percentage with every progress bar. Announce completed user actions politely; do not announce each polling refresh. Restore drawer/dialog focus and respect reduced motion.
- Long names, 12 members, long comments, five or more options, empty decisions and failed requests must wrap without horizontal overflow. Comments use pagination; never put full comment histories on homepage cards.
- Scope cached requests by account, role, plan and revision. Clear on sign-out or workspace switch. Preserve the existing stale-response guards.

## 6. Recommended state model and persistence

Extend the existing FastAPI/Postgres repository; a new state platform is unnecessary. Persist decisions separately from messages within the existing transactional state representation first, following the repository's actual storage contract. A physical SQL-table migration is not assumed by this design and needs a separately reviewed storage decision.

```ts
type Response = 'support' | 'can_live_with' | 'object' | 'abstain';
type DecisionStatus = 'needs_options' | 'awaiting_responses' | 'needs_discussion'
  | 'ready_to_confirm' | 'confirmed' | 'reopened';

interface Decision {
  id: string; planId: string; title: string; category: string;
  required: boolean; status: DecisionStatus; version: number;
  options: { id: string; label: string; sourceIds: string[] }[];
  eligibleMemberIds: string[];
  ballots: { memberId: string; optionId: string | null; response: Response;
    decisionVersion: number; updatedAt: string }[];
  selectedOptionId: string | null;
  confirmation: null | { by: string; at: string; decisionVersion: number };
}
interface DecisionComment {
  id: string; planId: string; decisionId: string; authorId: string;
  decisionVersion: number; text: string; createdAt: string;
}
interface EvidenceSummary {
  text: string; sourceIds: string[]; decisionVersion: number;
  generatedAt: string; providerStatus: 'live' | 'pending' | 'unavailable';
}
interface Finalization {
  id: string; planId: string; by: string; at: string;
  planRevision: number; decisionVersions: Record<string, number>;
}
```

Server commands: list decisions, propose/update options, respond, add/list comments, confirm/reopen decision, finalize/reopen plan. Membership checks apply to reads and writes; only the owner confirms/finalizes in the first release. Members control their own ballot. Confirmation validates all current ballots; finalization validates the current plan revision and required decisions atomically. Keep an idempotency key for finalization/retries and return a conflict when versions moved.

Suggested endpoints: `GET/POST /v1/plans/{id}/decisions`, `PATCH /v1/plans/{id}/decisions/{decisionId}`, `PUT .../{decisionId}/response`, `GET/POST .../{decisionId}/comments`, `POST .../{decisionId}/confirm`, `POST .../{decisionId}/reopen`, `POST /v1/plans/{id}/finalize`, `POST /v1/plans/{id}/reopen`. Nested IDs must be checked for the same authorized plan. Bound text lengths, list sizes and comment pages. Return canonical state and revisions.

Use a `decisionId` link for polls created through Decisions. Legacy polls remain accessible as legacy/unclassified until mapped by the owner. Do not infer persistent category relationships from question-text regexes or convert all legacy leading options to confirmations. Existing plan fields seed proposed options only. Member joins/leaves require explicit eligible-set/version reconciliation; do not silently preserve an old finalization over changed membership.

UI-local state: expanded comments, focused decision, draft comment, drawer open, pending request/error. Server state: decisions, ballots, comments, summaries, activity and finalizations. Derived state: score, missing responders, blockers, counts, stage and next action. Avoid independent mutable `score` fields or a global shared comments draft.

AI context includes authorized current decisions, current-version responses, bounded decision comments, confirmed preferences and plan-scoped RAG evidence. Comment/option updates invalidate relevant summaries and ingestion versions. Summaries cite stable source IDs; counts/statuses/next permitted commands are deterministic. User text is data, never tool authorization. An AI recommendation never confirms a decision or sends reminders.

## 7. Sample JSON

One fictional lodging decision, with incomplete participation; names are presentation labels only:

```json
{
  "planId": "demo-austin",
  "title": "Friends weekend in Austin",
  "planRevision": 12,
  "participantCount": 6,
  "stage": "narrowing_options",
  "consensus": { "score": 50, "finalized": false, "policy": "full_participation_consent_v1" },
  "requiredDecisionIds": ["lodging"],
  "decisions": [{
    "id": "lodging",
    "planId": "demo-austin",
    "title": "Lodging",
    "category": "lodging",
    "required": true,
    "status": "awaiting_responses",
    "version": 2,
    "options": [{ "id": "downtown", "label": "Downtown rental", "sourceIds": [] }],
    "eligibleMemberIds": ["m1", "m2", "m3", "m4", "m5", "m6"],
    "ballots": [
      { "memberId": "m1", "optionId": "downtown", "response": "support", "decisionVersion": 2, "updatedAt": "2027-04-01T18:00:00Z" },
      { "memberId": "m2", "optionId": "downtown", "response": "support", "decisionVersion": 2, "updatedAt": "2027-04-01T18:01:00Z" },
      { "memberId": "m3", "optionId": "downtown", "response": "can_live_with", "decisionVersion": 2, "updatedAt": "2027-04-01T18:02:00Z" }
    ],
    "selectedOptionId": null,
    "confirmation": null
  }],
  "comments": [{
    "id": "c1", "planId": "demo-austin", "decisionId": "lodging",
    "authorId": "m4", "decisionVersion": 2,
    "text": "Parking seems difficult downtown.", "createdAt": "2027-04-01T18:03:00Z"
  }],
  "nextAction": {
    "kind": "review_responses", "decisionId": "lodging",
    "label": "Review lodging responses", "missingMemberIds": ["m4", "m5", "m6"]
  },
  "lastActivityAt": "2027-04-01T18:03:00Z",
  "finalization": null
}
```

The score in this minimal fixture is 3/6 for its single required decision. A real trip normally has the full reviewed required set. The parking comment does not turn m4 into a responder. This JSON contains no invented venue inventory or booking claim.

## Implementation sequence and acceptance

1. **Decision contract and deterministic scoring.** Add backend/frontend contracts and fixtures. Test score boundaries, empty required sets, ties, all-abstain, objections, missing replies, stale versions, membership changes, and legacy plans. Existing health must remain distinct.
2. **Persist responses and contextual comments.** Add authorized versioned commands in the current repository abstraction, duplicate-submit protection and conflict handling. Test cross-plan access, revocation, member identity, owner restrictions and refresh persistence. Storage changes must preserve old snapshots and defaults.
3. **Homepage and default Decisions view.** Adapt composer copy, next steps, cards, summary and persistent panel using current tokens/primitives. Preserve generated review, manual fallback, profile/admin boundaries, discovery, RAG sources and old tab links.
4. **Confirmation, final review and AI evidence.** Human confirmation/finalization, reopening and booking gates; versioned cited summaries with honest unavailable/stale states. No model calls in deterministic tests; live provider checks require explicit authorization.
5. **Regression and visual review.** Lint, typecheck, production build, frontend Playwright desktop/mobile, shared-workspace suite and backend pytest. Add focused browser cases for comments, voting, missing participants, finalization/reopening and responsive access. Inspect 320/390/768/1440px screenshots and keyboard flow. These are proposed checks, not claimed results.

Acceptance: the homepage uses the supplied copy and CTA; next actions precede history; every plan card includes the requested fields; Decisions is the default workspace object; comments persist against decisions; summary/panel use evidence; no false consensus, automatic confirmation, reminder delivery or booking claim; no role/privacy regressions; current visual identity retained.

Risks: invalidating votes on edits needs clear member messaging; the new strict consent policy can reveal existing disagreement rather than hide it; legacy plans need an explicit decision-review step; stale AI text must not compete with canonical statuses; structured decisions must remain useful when AI is offline.

## Review gate

The repository's root `AGENTS.md`, Session rules, requires: “For later features, propose files, schema/migrations, tests, risks and acceptance criteria first; wait for user approval before implementation.” The owner subsequently approved implementation and full testing, while explicitly holding publication. The initial design-only deliverable did not change app behavior. Current implementation/verification evidence is recorded in the matching plan and CONNECTED_STATUS.md; the original reference snippets remain illustrative.
