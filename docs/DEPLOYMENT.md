# NAYA V19.3 — Deployment Guide

## TL;DR

| Target       | Trigger                                   | Config file             | Required GitHub Secrets                                                |
| ------------ | ----------------------------------------- | ----------------------- | ---------------------------------------------------------------------- |
| Local        | `docker compose up`                       | `docker-compose.yml`    | none (reads `.env`)                                                    |
| Cloud Run    | Tag `v*` push                             | `cloudbuild.yaml`       | `GCP_SA_KEY`, `GCP_PROJECT_ID`, `GCP_REGION` (optional)                |
| Render       | Manual dispatch                           | `render.yaml`           | `RENDER_API_KEY`, `RENDER_SERVICE_ID`                                  |
| Vercel       | Manual dispatch                           | `vercel.json`           | `VERCEL_TOKEN`, `VERCEL_PROJECT_ID`, `VERCEL_ORG_ID`                   |
| Docker       | Push to `main` or tag `v*`                | `Dockerfile`            | Optional: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` (GHCR works by default)|

## 1. Local (Docker Compose)

```bash
# Generate .env from your raw dump
python scripts/parse_raw_keys.py
python scripts/activate_production.py --apply

# Boot the full stack (19 services)
docker compose up -d

# Check health
curl http://localhost:8000/api/v1/health
```

## 2. Cloud Run (primary production target)

The `cloudbuild.yaml` is already configured with a **Pre-Deploy Gate** requiring 2 real sales before any deployment (see `tools/pre_deploy_validator.py`).

**Required GitHub Secrets** (Repo Settings → Secrets and variables → Actions):
- `GCP_SA_KEY` — JSON content of a service account with `roles/cloudbuild.builds.editor`, `roles/run.admin`, `roles/artifactregistry.writer`
- `GCP_PROJECT_ID` — e.g. `naya-pro-ultime`
- `GCP_REGION` — e.g. `europe-west1` (default)

**Deploy**:
```bash
git tag v19.3.0
git push origin v19.3.0
# → triggers .github/workflows/deploy.yml::cloud-run
```

## 3. Render

**Required GitHub Secrets**:
- `RENDER_API_KEY` — from https://dashboard.render.com/u/settings#api-keys
- `RENDER_SERVICE_ID` — from the URL when viewing your service (`srv-xxxxx`)

**Deploy**:
GitHub Actions → `Deploy` workflow → Run → Target: `render`.

## 4. Vercel (TORI_APP frontend)

**Required GitHub Secrets**:
- `VERCEL_TOKEN` — from https://vercel.com/account/tokens
- `VERCEL_PROJECT_ID` — from `.vercel/project.json` after `vercel link`
- `VERCEL_ORG_ID` — same file

**Configure env vars in Vercel dashboard** (not in `vercel.json`):
- `NAYA_API_URL` = `https://<your-cloud-run-url>` (Preview/Production separately)

**Deploy**:
GitHub Actions → `Deploy` workflow → Run → Target: `vercel`.

## 5. Docker image

Every push to `main` and every tag `v*` builds + pushes to:
- `ghcr.io/nayaintelligencepro-max/naya-supreme:<tag>`
- `ghcr.io/nayaintelligencepro-max/naya-supreme:latest` (main branch only)

To also push to Docker Hub, add `DOCKERHUB_USERNAME` + `DOCKERHUB_TOKEN` secrets.

## CI gates (every PR)

- **lint** — `ruff` fatal errors (E9,F63,F7,F82) must pass
- **secret-scan** — no `.env`/`raw_dump`/service-account/pem/key committed; no real-looking API key in tracked source
- **smoke** — `NAYA_CORE` imports, `config.production_flags` loads, `outreach.multi_channel_dispatcher` imports, FastAPI app boots

Soft gates (warnings, not blockers for bootstrap):
- **typecheck** (mypy)
- **security** (bandit + pip-audit)
- **tests** (pytest fast subset)

These will flip to strict gates once all warnings are cleaned up.

## Nightly watchdog

`.github/workflows/nightly.yml` runs every day at 03:17 UTC:
- Bandit full scan (high-severity Python vulns)
- pip-audit (CVE on dependencies)
- Safety (CVE DB cross-check)

Reports are uploaded as artifacts with 30-day retention.
