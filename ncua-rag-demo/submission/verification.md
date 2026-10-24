# Verification and remaining work

- 26 Python tests passed, including one-repair-only generation and rejection of unsupported financial figures.
- 3 UI proxy tests passed.
- The final production UI build passed.
- The live 15-question assessment completed; see evaluation/generation-review.md for actual outcomes and limitations.
- The pre-publication secret scan checked 160 publishable source files plus existing build outputs and detected no configured API key or backend token. Ignored environment files are excluded from the deliverable ZIP.
- Public Sites project: appgprj_6ad58528a1dc8191b08c8c2988ac2b41. Public access is configured, but no source version or deployment has been verified. The policy blocked hidden terminal input even after explicit user approval: sandbox_approval is disabled. Earlier direct input attempts could not resolve the repository host in the restricted runtime. Do not report an expected URL as a live app.
- A personal walkthrough recording and course-form submission remain user actions. A timed script is supplied.

Known limitations: nine-institution sample rather than the full national corpus; original downloadable HTML rather than email-delivered PDFs; incomplete retrieval on the cross-institution comparison; some generated drafts withheld; ratio answers may omit explicit units; the source view may omit a malformed identity heading while retaining the financial tables; live backend requires the local computer and temporary tunnel.
