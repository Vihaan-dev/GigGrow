# GigShield MVP

This file defines the smallest version of GigShield that can realistically be built in one day for a hackathon demo.

The MVP is split into two parts:

1. The web app, which shows the live financial state of the user.
2. The simulation layer, which generates fake SMS, earnings, spending, weather, and calendar events to drive the app.

## Goal

Help a gig worker like Ramesh understand whether he is financially safe today, where his money is going, and whether a big purchase is affordable.

## MVP Promise

The MVP should do 5 things well:

1. Show mocked earnings for the last 30 days.
2. Parse a few common SMS spending messages into categories.
3. Compute a simple safety buffer from earnings and savings.
4. Let the user chat in Hindi or Kannada about earnings, safety, and purchases.
5. Re-run the same app against simulated day/week/month event streams so the demo can show changing outcomes.

## Product Shape

Think of the project as two folders or two services:

### Part A: App

This is the actual GigShield web app.

It should:

- Read SMS-like events and update earnings, spending, and safety.
- Show charts, trends, and alerts.
- Classify good days, bad days, holidays, low-demand days, and rainy days.
- Estimate projected earnings based on recent history.
- Show scheme and loan suggestions based on the current financial state.
- Support chat queries against the current data state.

### Part B: Simulation

This is the fake event generator.

It should:

- Store fake event data in JSON.
- Pretend to be an SMS source or event API.
- Send events into the app through an internal API.
- Support replay of one day, one week, or one month.
- Support custom commands like "simulate rain", "simulate holiday", or "simulate high earnings day".
- Update the app state as if real life happened.

## What Is In Scope

### Backend

- FastAPI app with SQLite
- Seeded mock user: Ramesh
- Earnings table
- Spending table
- Events table for simulated SMS and life events
- Safety calculator
- SMS parser for a small set of bank patterns
- Scheme matcher for 3 to 4 schemes
- Claude-powered chat endpoint for simple intents
- Purchase simulation endpoint
- Simulation API that accepts fake events and writes them into the backend

### Frontend

- Dashboard with safety status
- Recent earnings list
- Spending summary
- Purchase simulator
- Scheme cards
- Chat box with language toggle
- Charts for earnings trend, spend trend, and safety trend
- Day type indicators like good day, bad day, holiday, and rainy day

### Demo Data

- 30 days of mocked Swiggy earnings
- A few sample SMS transactions
- One sample user profile
- A JSON event file with fake days, rain, holidays, bonuses, spending spikes, and low-demand periods

### Simulation Commands

The simulation layer should support commands like:

- Simulate a single SMS event.
- Simulate a full day.
- Simulate a week of events.
- Simulate a month of events.
- Simulate a rainy day with low earnings.
- Simulate a holiday with low demand.
- Simulate a good earnings day with surge income.

The idea is that the app should visibly change after each simulation run.

## What Is Out Of Scope

These should be cut from the one-day version:

- Real Swiggy or Zomato API integration
- Real SMS inbox access
- Voice input
- Production authentication
- Encryption and hard security work
- Multi-user support
- Weekly digests and notification jobs
- Full loan application flows
- Beautiful production-grade UI polish
- Real SMS inbox permissions on the phone
- Production-grade forecasting models
- Complex fraud detection

## How The Two-Part MVP Works

### Flow 1: App First

The app loads the current saved state and shows:

- earnings history
- spending history
- safety buffer
- projected earnings
- alerts
- scheme matches

### Flow 2: Simulation First

The simulation layer creates fake events and sends them to the app.

Examples:

- A fake SMS says fuel spend happened.
- A fake event says rain happened, so the day gets fewer deliveries.
- A fake event says it is a festival holiday, so demand drops.
- A fake event says bonuses are higher today, so earnings rise.

After each event, the app should recalculate:

- total earnings
- total spending
- safety days
- projected month-end earnings
- whether today is a good or bad day

## Event Types

The simulation data should support a small event schema.

### Suggested event types

- `sms_expense`
- `sms_income`
- `manual_spend`
- `weather_rain`
- `holiday`
- `surge_bonus`
- `low_demand`
- `loan_query`
- `scheme_query`

### Suggested event fields

- `date`
- `type`
- `amount`
- `message`
- `category`
- `confidence`
- `tags`
- `metadata`

## App Responsibilities

The app should not just display raw data. It should interpret it.

It should:

- classify days as good, average, bad, or holiday-affected
- infer whether a spend is essential or non-essential
- estimate whether the user is on track for the month
- flag overspend and low-safety conditions
- explain why a decision changed after a simulated event

## Simulation Responsibilities

The simulation layer should behave like a fake world.

It should:

- output deterministic fake data for demo reproducibility
- allow random mode for more realistic variation
- replay events in order
- support manual overrides for special demo moments
- be able to feed the app through a single internal API endpoint

## Minimum API Split

### App API

The app backend should expose endpoints like:

- `GET /api/state`
- `GET /api/earnings/{user_id}`
- `GET /api/spending/{user_id}`
- `GET /api/safety/{user_id}`
- `GET /api/schemes/match`
- `POST /api/chat`
- `POST /api/purchase/simulate`

### Simulation API

The simulation service should expose endpoints like:

- `POST /simulate/event`
- `POST /simulate/day`
- `POST /simulate/week`
- `POST /simulate/month`
- `POST /simulate/custom`

These endpoints should push events into the app and return the updated state.

## MVP User Flow

1. Open app.
2. See Ramesh’s safety buffer, earnings chart, and current day classification.
3. Run one simulated SMS or event and watch the dashboard update.
4. Replay a whole day, a week, or a month.
5. Ask a simple Hindi or Kannada question.
6. Simulate a purchase like a bike or phone.
7. See matched government schemes and loan options.

## Acceptance Criteria

The MVP is good enough if all of these work:

- Backend starts without errors.
- Frontend loads and shows a dashboard.
- Safety buffer returns a sensible days-safe value.
- SMS parser correctly identifies at least fuel, food, rent, and transfer.
- Chat returns a response in the selected language.
- Purchase simulator shows before/after safety impact.
- Scheme matcher returns at least 3 eligible schemes for the demo profile.
- Simulation endpoints can inject fake events and the app state changes after replay.
- The app can show at least one chart and one day classification label.
- The app can run a day, week, or month simulation without manual DB editing.

## Recommended Build Order

1. Create backend database, seed data, and event schema.
2. Build earnings, spending, safety, and state endpoints.
3. Add SMS parser and event ingestion endpoint.
4. Build the simulation service and fake JSON event files.
5. Add Claude chat and purchase simulation.
6. Build the frontend dashboard, charts, and day labels.
7. Wire in scheme matching and loan queries.
8. Do one end-to-end demo pass with replayable mock data.

## Suggested Hackathon Demo Script

1. Show Ramesh’s 30-day earnings chart.
2. Replay a rainy day and show earnings drop.
3. Replay an SMS fuel spend and show the spending chart update.
4. Mark a holiday and show the app classify it as a bad or low-demand day.
5. Ask “Kal kitna kamaya?” in Hindi.
6. Simulate a ₹22,000 bike purchase.
7. Show matching schemes and one recommended next step.
8. Replay a week and show projected earnings change.

## Hard Cut Rule

If a feature does not directly improve the demo story above, it should wait for v2.

## MVP Folder Idea

If you want this to stay clean, use two top-level areas:

- `app/` for the web app and backend that powers the dashboard
- `simulation/` for fake JSON, replay scripts, and event generators

Optional support folders:

- `app/backend/`
- `app/frontend/`
- `simulation/data/`
- `simulation/scripts/`

## One-Day Reality Check

This version is still doable in one day if:

- the simulation layer is simple JSON plus replay commands
- the app uses mock data and local state first
- charts are basic but clear
- the language layer only supports a few core intents

If the simulation layer becomes too dynamic or too many event types are added, the build stops being one-day friendly.
