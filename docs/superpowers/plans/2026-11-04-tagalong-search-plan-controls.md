# Source-link discovery and owner plan controls

User requested clickable links for people to explore discovered places, and the choice to delete a plan or switch its owner. Reuse the verified CONVENE Keenable protocol with a Tagalong adapter; public search works without a key.

- Authenticated bounded place search sends only explicitly entered query/category/destination, rate-limited to ten requests per account per minute. Filter unsafe URLs, render plain snippets, and provide labeled external source links with noopener/noreferrer. Do not imply verified ratings, prices, availability or live booking inventory.
- Add owner-only transfer to an existing active member, guarded by current revision and human confirmation. Keep the old owner as a member and invalidate the old invitation link. Update the normalized Postgres owner projection.
- Add owner-only deletion with current revision and exact plan-name confirmation. Use an access tombstone, disable invitations, and queue source/vector removal. Retain records for audited admin review, clearly disclosed in the dialog. Do not delete or transfer any existing user plan as an implementation test.
- Verify backend auth/input/rate-limit, ownership/revision and deletion isolation tests; browser link-opening, transfer, cancel/confirm delete and existing suites; live Keenable only with generic nonprivate search terms. Review, synchronize and push the review branch.

No new package, account, migration or mandatory hosting secret is needed. Existing source/vector deletion jobs require the configured ingestion worker to run. The live assistant is not automatically given a place-search tool by this change; the explicit Discover form is the entry point.
