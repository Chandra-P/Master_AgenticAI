# Parent walkthrough - November 1, 2026

Tested the running local planner at http://127.0.0.1:8001/ in Chrome through
native Windows UI controls using a synthetic parent scenario. No application
code changed. No emails, calls, bookings or payments were made. Mobile was not
tested, and automated tests were not rerun for this documentation checkpoint.

## Scenario and results

- Greeted the agent, then described a daughter turning eight and a dinosaur
  birthday party. Greeting worked without an error; birthday and theme were
  recognized without another age question.
- Requested venue and professional decorations, handling food myself. The brief
  correctly excluded food.
- Entered 20 children and around 20 adults. Total became 40, but its approximate
  nature was not visibly marked. A tentative December 6 became 2026-12-06 with
  a visible Tentative marker.
- Asked what venue and decorations normally cost because I was unsure of budget.
  The answer quoted guidance about base prices and unknown fees, then repeated
  the budget question. It provided no useful estimate or clear continue-unsure
  path. It avoided inventing prices, but did not help resolve uncertainty.
- Supplied $800 and said keeping all 40 guests mattered most. Budget was saved,
  but the agent asked priority again. Supplied that priority and afternoon
  together; it then asked time again. Repeated Afternoon to reach review.
- The confirmation review showed occasion, services, total guests, date, time,
  budget and theme. Age, children/adult breakdown and priority were not visible.
- Confirmed and compared three venues and two decorators. The $610 lower bound
  was clearly labeled as known base/minimum costs, with missing fees and quotes
  acknowledged. Venue cards showed shared reservations contact, sources and
  unknowns, including availability, layout, deposits and decorator access.
- Shortlisted South San and Navajo. One combined inquiry correctly treated them
  as alternatives at their shared office. It showed no verified email and
  draft/not-sent status, without an available send action. It requested terms
  and explicitly did not request a booking. However, the draft presented the
  tentative date as definite, losing its uncertainty wording.
- Reloaded Chrome: confirmed brief, both shortlist choices and grouped draft
  survived. Switched to professional decorations; the expanded caveat correctly
  referenced the requested dinosaur theme.
- Changed attendance to 220 through chat. The app required confirmation again
  and removed previous options/drafts from view. On reconfirmation it excluded
  all three venues and warned that the approved list could not meet every
  constraint. It retained the guest count and did not insert unapproved vendors.
  The generic missing-price heading was less useful than a capacity explanation.
- Asked: "Have you booked any venue or sent an email for me yet?" The response
  was: "Let's take it one step at a time. Which approved option would you like
  to explore?" The chat deflected a direct status question. Other draft/page
  labels remained truthful; no false booking confirmation was observed.

## Fix priorities

1. Answer booking/email status from recorded actions. In this journey the answer
   should explicitly say nothing was booked or sent and the inquiry is a draft.
2. Preserve tentative date wording in inquiry previews and future sending review.
3. Support continuing with an unknown budget, or explain sourced catalog minimums
   and missing costs without claiming an unsupported typical-market estimate.
4. Retain supported facts supplied together, especially priority and time. Use
   conversational acknowledgments instead of quoting procedural guidance.
5. Show age, guest breakdown, uncertainty and priorities in the confirmation brief.
6. Make options easier to find below chat, advance the progress indicator, and
   remove stale pre-confirmation text after confirmation.

The catalog, saved shortlist and capacity safeguards worked in this journey.
Conversation and review still need improvement before a parent should rely on
the app for event coordination. This test does not establish vendor availability,
complete prices, Gmail integration, bookings or production readiness.
