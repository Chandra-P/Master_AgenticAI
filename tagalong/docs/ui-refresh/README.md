# Tagalong visual comparisons

All screenshots use synthetic browser-demo plans at 100% browser zoom. `before/` records the committed UI at the start of this task; `after/` records the refreshed production build.

| Screen | Desktop before | Desktop after | Mobile before | Mobile after |
| --- | --- | --- | --- | --- |
| Home | [Before](before/home-1440.png) | [After](after/home-1440.png) | [Before](before/home-390.png) | [After](after/home-390.png) |
| Chat | [Before](before/chat-1440.png) | [After](after/chat-1440.png) | [Before](before/chat-390.png) | [After](after/chat-390.png) |
| Itinerary | [Before](before/itinerary-1440.png) | [After](after/itinerary-1440.png) | [Before](before/itinerary-390.png) | [After](after/itinerary-390.png) |

The screenshot test also runs from the normal frontend suite:

```sh
TAGALONG_TEST_BROWSER_CHANNEL=chromium \
PLAYWRIGHT_BROWSERS_PATH="$PWD/node_modules/.cache/ms-playwright" \
npm test -- ui-refresh.visual.spec.ts --project=desktop
```

The browser-path and channel overrides are optional environment settings. Default Playwright behavior is unchanged. The test loops over desktop and mobile itself, so its duplicate mobile project is skipped.

See [the implementation and coverage report](../UI_REFRESH.md) for the complete screen inventory, design tokens, validation results and limitations. Route, dialog, tablet and connected-mode screenshots are additional ignored Playwright artifacts in `test-results/` and `test-results-shared/`.
