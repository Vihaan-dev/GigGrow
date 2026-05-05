# GigShield Simulation (Part B)

This folder replays fake events into the Part A backend so the app can update in real time.

## What It Does

- Uses a JSON file of fake earnings, spending, and life events.
- Sends those events to the backend via `/api/events/ingest`.
- Supports day, week, month, or full replay.

## Requirements

- Backend running on `http://127.0.0.1:8000`
- Python available (use the workspace venv)

## Quick Start

1. Start backend

```bash
cd /Users/vihaan/Programming/ClaudeHackathon/backend
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python app.py
```

2. Seed a demo user

```bash
cd /Users/vihaan/Programming/ClaudeHackathon/simulation
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python run_sim.py seed-user
```

3. Replay a single day

```bash
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python run_sim.py simulate-day --date 2026-04-14
```

4. Replay a week

```bash
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python run_sim.py simulate-week --start 2026-04-10
```

5. Replay the full month

```bash
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python run_sim.py simulate-month --start 2026-04-06 --days 30
```

## Useful Commands

List available dates in the data file:

```bash
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python run_sim.py list-dates
```

Dry run to see how many events will be sent:

```bash
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python run_sim.py simulate-week --start 2026-04-10 --dry-run
```

Override the user id (if your backend user id is not 1):

```bash
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python run_sim.py simulate-month --start 2026-04-06 --days 30 --user-id 2
```

## Data Source

The fake events live in:

```
simulation/data/events.json
```

You can edit that file to add more events, or create your own data file and pass it with:

```bash
/Users/vihaan/Programming/ClaudeHackathon/.venv/bin/python run_sim.py simulate-all --data /path/to/your/events.json
```
