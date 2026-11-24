# Quantum Leads AI

Dedicated private prospect-research workspace for the **QUANTUM AI trading app only**. Deployed as a Node.js service on Render and backed by Neon Postgres. This folder is on the `quantum-leads-ai-render` branch; the separate trading app and mailer projects are not part of this service.

## Features
- Owner-only password login with signed bearer sessions.
- Persistent PostgreSQL storage for leads, campaigns and activity.
- Lead create/edit/delete, search, CSV import/export and source links.
- Public buyer-intent discovery through Reddit public search and Hacker News public search.
- Heuristic qualification scoring based on trading-topic relevance and explicit recommendation/purchase language.
- URL deduplication and reviewable public source links.
- Mobile-responsive installable web app and 200-qualified-leads/day target counter.
- Health check at `/api/health`.

## Configure Render
Set these environment variables on the Render web service:
- `OWNER_PASSWORD`: strong private owner password.
- `SESSION_SECRET`: random secret of at least 32 characters.
- `DATABASE_URL`: Neon PostgreSQL connection string (keep secret).

Build command: `cd quantum-leads-ai && npm install --omit=dev`
Start command: `cd quantum-leads-ai && npm start`

The app creates its required tables and indexes on startup. Node.js 20 or newer is required.

## Discovery limits and responsible use
The discovery endpoint searches public discussion indexes only. A matching public post is a research signal, not proof that its author is a buyer or a customer. Scores are heuristic, not an AI prediction. It does not scrape private accounts, collect private messages, harvest personal email addresses, or send email/DMs. Respect each platform's terms, rate limits, and applicable privacy rules. Reddit availability can vary due to access controls and rate limits.

The target of 200 qualified research leads per day is a dashboard goal, not a guaranteed volume. Actual results depend on fresh public discussions and provider availability. This version does not claim 200 confirmed buyers daily.

Campaign approval saves an owner decision only; no messages are sent automatically.
