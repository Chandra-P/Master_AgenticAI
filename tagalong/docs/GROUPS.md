# Reusable Groups

Shyam's reusable Groups feature is integrated with the connected Tagalong app. Open **Groups** from the sidebar or mobile navigation.

Groups are currently a **browser-local demo feature**. In shared mode, the Groups page explains that boundary and provides **Explore demo groups**. Choosing it switches to the local demo; it does not create shared members or send invitations. Use Account to return to the shared workspace.

In demo mode you can create a themed group, edit adult aliases and optional contact details, archive/restore or remove a group, and start a demo plan with its members. Alex is the fixed fictional demo owner. A plan copies the selected group name/theme and member aliases/colors; contact details stay in group storage. Later group edits do not rewrite existing plans, chats or votes.

Local groups are not synchronized with teammates, other devices or incognito windows. A fresh browser has independent demo data. Corrupt or unavailable storage is reported honestly rather than silently overwriting it. To collaborate on a real shared plan, use its existing membership and private invitation controls with authenticated accounts.

No database migration, new credential or provider is needed for this integration. Connected mode does not load local group contacts or use demo groups for plan creation. The implementation lives in the group service, planning provider, group editor/page and create-plan dialog; verification covers both local group behavior and the connected-mode boundary.

## Team contribution and deployment

The current deployment branch is `checkpoint/all-projects-2026-11-04`. A commit pushed only to `main` does not appear on that deployment. Create feature branches from the current deployment branch and submit pull requests targeting it until the main integration PR is merged. See [CONTRIBUTING.md](../CONTRIBUTING.md).

The Groups source originated in ShyamK's `895593a` commit. The integration preserves its history and the newer connected functionality. Earlier audit documents in the repository root remain historical snapshots, not current release claims.
