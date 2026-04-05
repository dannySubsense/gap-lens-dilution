# Test & Deploy Playbook — gap-lens-dilution

**Tailscale IP**: `100.70.21.69`
**Project root**: `/home/d-tuned/projects/gap-lens-dilution`

---

## Ports

| Service | Port | URL (local) | URL (Tailscale) |
|---------|------|-------------|-----------------|
| Backend (FastAPI) | 8000 | http://localhost:8000 | http://100.70.21.69:8000 |
| Frontend (Next.js) | 3001 | http://localhost:3001 | http://100.70.21.69:3001 |
| API docs (Swagger) | 8000 | http://localhost:8000/docs | http://100.70.21.69:8000/docs |

---

## Two-Tier Testing Model

This project uses two distinct test tiers. Both must pass before any sprint is closed or deployment made.

| Tier | Command | Services needed | Speed | What it catches |
|------|---------|----------------|-------|----------------|
| TypeScript compilation | `cd frontend && npx tsc --noEmit` | No | ~5s | Type errors, import issues |
| Playwright QC | `bash scripts/run_playwright_qc.sh` | Yes (auto-managed) | ~30-60s | CORS, runtime errors, browser rendering, multi-step UX, localStorage |

Neither tier replaces the other. See `docs/SOP_PLAYWRIGHT_QC.md` for the full Playwright QC procedure.

---

## 1. Run the Test Suite

### TypeScript type check (no services required)

```bash
cd /home/d-tuned/projects/gap-lens-dilution/frontend
npx tsc --noEmit
```

Should produce no output (zero errors).

### Playwright browser QC (fully orchestrated)

The script manages service startup, teardown, and cleanup automatically:

```bash
cd /home/d-tuned/projects/gap-lens-dilution
bash scripts/run_playwright_qc.sh
```

Expected output: all tests pass, exit code 0.
See `docs/SOP_PLAYWRIGHT_QC.md` for failure diagnosis.

---

## 2. Start the Backend

Open a dedicated terminal (tmux pane or separate tab).

```bash
cd /home/d-tuned/projects/gap-lens-dilution
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**What you'll see on healthy startup:**
```
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Verify backend is live

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status": "ok"}
```

---

## 3. Start the Frontend

### Why production builds are required for Tailscale access

`npx next dev` uses HMR websockets that fail over non-localhost connections. Accessing via Tailscale IP causes `ERR_INVALID_HTTP_RESPONSE`, silently breaking React hydration (clicks do nothing, no console errors visible). Always use production builds.

### Build and start

```bash
cd /home/d-tuned/projects/gap-lens-dilution/frontend
npx next build
npx next start -p 3001 -H 0.0.0.0
```

Frontend is ready when you see:
```
▲ Next.js 16.x.x
- Local:         http://localhost:3001
- Network:       http://0.0.0.0:3001
✓ Ready in ~250ms
```

Access from your browser: `http://100.70.21.69:3001`

### Environment setup

Verify `frontend/.env.local` exists with the correct value:

```bash
cat /home/d-tuned/projects/gap-lens-dilution/frontend/.env.local
```

Expected content:
```
NEXT_PUBLIC_API_BASE=http://100.70.21.69:8000
```

---

## 4. Manual Smoke Tests

### 4a. Health endpoint
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

### 4b. Dilution data for a ticker
```bash
curl -s http://localhost:8000/api/v1/dilution/AAPL | python3 -m json.tool
```

### 4c. TradingView gainers
```bash
curl -s http://localhost:8000/api/v1/gainers | python3 -m json.tool
```

### 4d. Massive gainers
```bash
curl -s http://localhost:8000/api/v1/gainers/massive | python3 -m json.tool
```

### 4e. FMP gainers
```bash
curl -s http://localhost:8000/api/v1/gainers/fmp | python3 -m json.tool
```

### 4f. Swagger UI
Open http://localhost:8000/docs (or http://100.70.21.69:8000/docs from another device).
All routes should be listed. You can call them interactively from the UI.

### 4g. Frontend dashboard
Open http://100.70.21.69:3001.

Checklist:
- [ ] Page loads with dark theme
- [ ] Gainer columns visible (TradingView, Massive, FMP)
- [ ] Click a gainer row → charts load in middle column
- [ ] Click a gainer row → dilution data loads in right column
- [ ] Ticker search works
- [ ] Charts show Eastern Time with extended hours

---

## 5. Troubleshooting: Spinning Wheels / "Refresh failed"

### Symptom
Gainer columns show "Refresh failed" or charts don't load.

### Diagnosis

**Step 1 — Check if the backend is alive:**
```bash
curl http://localhost:8000/health
```
If this returns JSON, the backend is running.

**Step 2 — Check the frontend env:**
```bash
cat /home/d-tuned/projects/gap-lens-dilution/frontend/.env.local
```
`NEXT_PUBLIC_API_BASE` must point to `http://100.70.21.69:8000`.

**Step 3 — Rebuild if env was wrong:**
The `NEXT_PUBLIC_*` variables are baked into the JS bundle at build time. If you changed `.env.local`, you must rebuild:
```bash
cd /home/d-tuned/projects/gap-lens-dilution/frontend
npx next build
# Then restart the server
```

---

## 6. Stop Services

```bash
# Backend: Ctrl+C in the uvicorn terminal

# Frontend: Ctrl+C in the next start terminal

# Or kill by port if running detached:
kill $(ss -tlnp sport = :8000 | awk '{print $6}' | grep -oP 'pid=\K[0-9]+')
kill $(ss -tlnp sport = :3001 | awk '{print $6}' | grep -oP 'pid=\K[0-9]+')
```

---

## 7. Environment Variables Reference

| Variable | Location | Notes |
|----------|----------|-------|
| `ASKEDGAR_API_KEY` | `.env` | AskEdgar V2 enterprise API key |
| `MASSIVE_API_KEY` | `.env` | Massive/Polygon API key (Starter plan, 15-min delayed) |
| `FMP_API_KEY` | `.env` | Financial Modeling Prep API key |
| `NEXT_PUBLIC_API_BASE` | `frontend/.env.local` | Must be Tailscale IP for remote access: `http://100.70.21.69:8000` |
