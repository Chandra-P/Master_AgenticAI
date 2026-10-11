# KidSpark future enhancements

These are proposed improvements, not implemented features. The current release
is a local assignment demonstration with curated decisions and nickname-based
history.

| Priority | Enhancement | Benefit and prerequisite |
| --- | --- | --- |
| 1 | Student and educator usability review | Observe whether prompts, hints, choices, and charts are understandable. Use feedback to refine reading load before claiming age validation. |
| 1 | Accessibility evaluation | Check keyboard-only navigation, focus transitions, chart alternatives, contrast, and screen-reader announcements; provide text summaries wherever charts need them. |
| 1 | Authenticated student profiles | Replace nickname-only identification with reliable access control before making student histories private. Define recovery, consent, and retention requirements. |
| 2 | Further question variety and calibration | Extend the implemented 90-question, objective-balanced bank; evaluate variants with students and educators to calibrate comparable difficulty. Keep exact content versions and question IDs. |
| 2 | Adaptive difficulty | Suggest appropriate practice based on skill evidence while avoiding pressure or punishment. Validate recommendations against educator feedback. |
| 2 | Persistent hosting | Put the app on a host with durable writable storage, backups, monitoring, and configuration management; consider a server database for higher concurrency. |
| 3 | Teacher reports | Add authorized class-level views and exports once profile and classroom permissions exist. Keep students' individual histories protected. |
| 3 | Resume unfinished rounds | Store in-progress state safely with explicit lifecycle and expiry rules, while retaining duplicate-answer and duplicate-save protection. |
| 3 | Portable release packaging | Bundle sample data and resolve user data directories for wheel installs; add migration tests and clean-environment automated checks. |

Begin with feedback and accessibility because engagement depends on how real
students experience the application. Authentication and durable hosting are
separate engineering work, required before expanding beyond the local demo.
