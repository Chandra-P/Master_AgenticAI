---
name: pnpm configuration rewrites
description: Preserve security and compatibility rationale when pnpm normalizes workspace configuration.
---

Dependency updates can normalize the workspace YAML, reorder its keys, and strip its comments. Restore important rationale after package-manager edits.

**Why:** A dependency update removed the explanations for the minimum release-age defense and exact shared React/Expo version pins, even though the settings themselves survived.

**How to apply:** After dependency updates, check that release-age protection, trusted exclusions, platform exclusions, and build-script allowlists remain intact. Preserve comments explaining security settings and exact compatibility pins.
