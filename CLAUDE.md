# Project Standing Orders

## Spec Orchestration — Non-Negotiable Rules

This project uses the `spec-start` and `forge-start` workflows. These rules are always in effect.

### You are the orchestrator. You do not touch spec or implementation files directly.

| Document | Owner | You may... |
|---|---|---|
| `docs/specs/*/01-REQUIREMENTS.md` | @requirements-analyst | Write a fix contract, delegate |
| `docs/specs/*/02-ARCHITECTURE.md` | @architect | Write a fix contract, delegate |
| `docs/specs/*/03-UI-SPEC.md` | @ui-spec-writer | Write a fix contract, delegate |
| `docs/specs/*/04-ROADMAP.md` | @planner | Write a fix contract, delegate |
| `docs/specs/*/05-REVIEW.md` | @spec-reviewer | Write a fix contract, delegate |
| Any implementation file | @code-executor | Write a fix contract, delegate |

**You never use Edit, Write, or Bash to modify any of the above files yourself.**

### When the reviewer finds gaps

1. Parse the gaps table from `05-REVIEW.md`
2. Group by owning document
3. Delegate each group to the owning agent with a precise fix contract
4. Re-run @spec-reviewer after all fixes are confirmed
5. If gaps remain after 2 iterations → HALT and present to human

### Agent selection

- Use the agent whose description matches the task
- Never use `code-executor` for editing documentation or spec files
- Never use a general-purpose agent when a specialized one exists

### HALT conditions

Stop and ask the human when:
- A gap requires a business decision (e.g., watchlist behavior, layout decisions, data sources)
- Two agents produce contradictory outputs
- A fix contract would change scope beyond the identified gap

---

## Sprint Closure Gate — Non-Negotiable

A forge sprint is not complete until **both** of the following pass:

### Gate 1: TypeScript Compilation
```bash
cd frontend && npx tsc --noEmit
```
**Required**: zero errors, exit code 0.

### Gate 2: Playwright QC (full-stack browser tests)
```bash
bash scripts/run_playwright_qc.sh
```
**Required**: all tests pass, exit code 0.

The Playwright QC catches bugs invisible to compilation checks: CORS, runtime errors,
multi-step UX flows, localStorage persistence, and browser rendering. It is the final
gate — not optional, not skippable. See `docs/SOP_PLAYWRIGHT_QC.md` for the full procedure.

**Sprint status must not be set to COMPLETE in PROGRESS.md until both gates pass.**

---

## Project Context

- **Backend**: FastAPI at `app/` — proxies AskEdgar V2, TradingView gainers, Massive gainers, FMP gainers
- **Frontend**: Next.js 16 at `frontend/` — single-page dashboard with top toolbar, 4-column layout (gainers + charts + dilution + watchlist)
- **Charts**: TradingView Advanced Chart free embeds via CDN script injection
- **Deployment**: Production builds only (`npx next build && npx next start -p 3001 -H 0.0.0.0`)
- **Access**: Tailscale IP `100.70.21.69:3001` (frontend), `100.70.21.69:8000` (backend)
- **Spec docs**: `docs/specs/<feature-name>/` — single canonical location
- **Design system**: `#1b2230` background, `#2a3447` borders, `#a78bfa` accent, `#ec4899` magenta highlights
