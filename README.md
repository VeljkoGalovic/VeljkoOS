# VeljkoOS Core API

Personal operating system backend: goals, tasks, learning sessions, and a daily
planner that turns pending work into an ordered, time-boxed schedule.

Async FastAPI · PostgreSQL · SQLAlchemy 2.0 (asyncio) · Alembic · Pydantic v2

---

## Quickstart

```bash
cp .env.example .env          # optional; compose has working defaults
docker compose up --build
```

The API comes up on <http://localhost:8000>, interactive docs at `/docs`.
Migrations apply automatically on container start — the `api` service waits on a
Postgres healthcheck first, so a cold `up` works without a manual step.

```bash
curl localhost:8000/health
# {"status":"online","system":"VeljkoOS Core"}
```

Teardown, dropping the volume:

```bash
docker compose down -v
```

<details>
<summary>Running without Docker</summary>

Needs a reachable PostgreSQL. Point `DATABASE_URL` at it (note the
`postgresql+asyncpg://` prefix — the sync driver will not work).

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Podman users can substitute `podman-compose up --build`.
</details>

---

## Endpoints

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | Liveness. Unprefixed. |
| `POST` | `/api/v1/goals` | Create goal → `201` |
| `GET` | `/api/v1/goals` | List goals, newest first |
| `POST` | `/api/v1/tasks` | Create task → `201`; `404` if `goal_id` is unknown |
| `GET` | `/api/v1/tasks` | Filters: `?scheduled_for=YYYY-MM-DD&status=pending`, both optional |
| `PATCH` | `/api/v1/tasks/{id}` | Partial update; `404` unknown task, `400` empty body |
| `POST` | `/api/v1/learning-sessions` | Log a study block → `201` |
| `GET` | `/api/v1/learning-sessions` | Filter: `?subject=math` |
| `POST` | `/api/v1/planner/generate` | Generate the day plan |

---

## The planner

`POST /api/v1/planner/generate`

```json
{ "available_minutes": 240, "energy_level": 4, "target_date": "2026-09-08" }
```

**Candidates.** Pending tasks whose `scheduled_for` is the target date, plus
unscheduled priority-1 tasks — high-priority work should not drift because it
was never booked.

**Ranking**, in strict order of precedence:

1. `priority` ascending. A P1 task never sorts below a P2, whatever else is true.
2. **Goal urgency** descending — breaks ties inside a priority band.
3. **Duration** — direction set by energy (below).

**Energy** reflects how rested you are, and gates task *size*:

| `energy_level` | profile | longest task admitted | duration ordering |
|---|---|---|---|
| 1 | depleted | 30 min | shortest first |
| 2 | low | 45 min | shortest first |
| 3 | moderate | 90 min | shortest first |
| 4 | good | 150 min | **longest first** |
| 5 | peak | uncapped | **longest first** |

Rested, you front-load the long deep-work blocks while they are cheap. Depleted,
you get quick wins and anything oversized moves to `deferred` with reason
`exceeds_energy_capacity` — nothing is silently dropped. `available_minutes` is
*not* scaled by energy; the cap already expresses that constraint.

> Duration is the proxy for intensity, because `Task` has no difficulty column.
> A 90-minute Anki grind and 90 minutes of proof-writing look identical to the
> planner. An explicit `intensity` column is the natural fix.

**Goal urgency** ∈ [0, 1], `0.0` for a task with no goal or a completed one:

```
days_left      = goal.target_date - target_date      # absent -> date_score 0
date_score     = clamp(1 - days_left / 90, 0, 1)     # overdue saturates at 1
progress_score = (100 - goal.progress_pct) / 100
urgency        = 0.6 * date_score + 0.4 * progress_score
```

**Fill** is greedy with backfill: candidates are walked in ranked order, and one
that does not fit is skipped rather than ending the scan — so a shorter task
further down can still use the leftover gap.

**The plan is read-only.** It is a projection; it does not write `scheduled_for`
back onto the tasks it selects. Committing a plan is a separate future endpoint.

<details>
<summary>Response shape</summary>

```json
{
  "target_date": "2026-09-08",
  "energy_level": 4,
  "energy_profile": "good",
  "max_task_minutes": 150,
  "available_minutes": 240,
  "allocated_minutes": 205,
  "remaining_minutes": 35,
  "utilization_pct": 85.42,
  "task_count": 3,
  "domain_focus": { "math": 2, "programming": 1 },
  "schedule": [
    {
      "order": 1,
      "task_id": 4,
      "description": "Work through spectral theorem proofs",
      "priority": 1,
      "estimated_minutes": 120,
      "cumulative_start_minute": 0,
      "goal_id": 1,
      "goal_title": "Master Linear Algebra",
      "goal_category": "math",
      "goal_urgency": 0.7133
    }
  ],
  "deferred": [
    {
      "task_id": 9,
      "description": "Refactor the ingest pipeline",
      "priority": 2,
      "estimated_minutes": 180,
      "reason": "exceeds_energy_capacity"
    }
  ]
}
```
</details>

---

## Data model

**`goals`** — `id`, `title`, `category`, `target_date?`, `progress_pct` (0–100),
`created_at`

**`tasks`** — `id`, `goal_id?` → `goals.id` `ON DELETE SET NULL`, `description`,
`priority` (1–3), `estimated_minutes`, `status`
(`pending`/`completed`/`skipped`), `scheduled_for?`, `created_at`

**`learning_sessions`** — `id`, `subject`, `topic`, `duration_minutes`,
`confidence_before?` (1–10), `confidence_after?` (1–10), `notes_ref?`
(Obsidian path), `created_at`

Retiring a goal nulls its tasks' `goal_id` rather than deleting them — logged
work outlives the objective that motivated it. All ranges are enforced twice: as
Pydantic field constraints and as database `CHECK` constraints.

`created_at` is `TIMESTAMPTZ` with a `now()` server default, so timestamps come
from the database clock rather than whichever process happened to insert.

---

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://veljko:veljko@localhost:5432/veljkoos` | Must use the `asyncpg` prefix |
| `APP_NAME` | `VeljkoOS Core` | Shown in `/docs` |
| `DEBUG` | `false` | Echoes SQL when true |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `veljko` / `veljko` / `veljkoos` | Read by the `db` compose service |

Compose overrides `DATABASE_URL` to use host `db`; `.env.example` uses
`localhost` for non-container runs.

---

## Migrations

```bash
alembic upgrade head                                  # apply
alembic revision --autogenerate -m "add x"            # generate
alembic check                                         # models vs. schema drift
alembic downgrade -1                                  # roll back one
```

New models must be imported in `app/models/__init__.py` or autogenerate will not
see them.
