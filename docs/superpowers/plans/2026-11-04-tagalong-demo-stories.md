# Admin/Member login choice and presentation storyboards

The user requested explicit Admin/Member sign-in choice, dashboard availability only in Admin mode, and exclusion of QA scenarios from Member mode. They clarified the demonstration means complete fictional conversations showing how planning begins, how AI helps, and how participants agree on an outline. Approved destinations are San Francisco for Christmas, a three-day Yosemite trip for four, and a San Francisco date night. The user approved including current-planning versus AI-assisted planning in the presentation narrative.

- Enforce a bounded request mode (`member` by default, `admin` only for granted admins) on the backend. Existing admin grants remain independent of membership. Member mode denies QA plans through both lists and direct access.
- Bind tab-scoped selection to the authenticated account. Ask on sign-in, allow explicit switching on the account page, clear old content/pending requests on switching, and hide/unmount admin views in Member mode.
- Add an admin-only versioned storyboard library, independent of real plans/accounts. Each story has at least 16 exchanges, an evolving budget/preferences/poll/itinerary/task snapshot, and explicit final human agreement. Label all scripted AI illustrations and fictional costs. No real accounts or reservations are created.
- Add a replay UI and before/after presentation narrative, distinguishing curated stories from live OpenAI/Pinecone behavior.
- Verify backend mode authorization/direct-link isolation, desktop/mobile role switching, all three replays and the existing suites; review, synchronize, commit and push the review branch.

Builder defaults: fictional supporting names and sample budgets; dates December 25–27, 2026 for Christmas, May 14–16, 2027 for Yosemite, and December 12, 2026 for date night. Remaining travel checks are explicitly unfinished; fictional outlines are not verified travel advice.
