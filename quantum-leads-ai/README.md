# Quantum Leads AI

Private, mobile-first lead management and campaign workspace for your own businesses. This project lives in the `quantum-leads-ai` folder on the dedicated `quantum-leads-ai` branch of the Quantum-ai repository. The repository's `main` branch is not changed.

## Included
- Responsive dashboard and original Quantum Leads AI logo
- Owner-only login using signed, HttpOnly session cookies
- Cloudflare D1 persistence for leads, campaigns and activity
- Lead create, edit, delete, search, CSV import and export
- Campaign drafts and owner approval; approval does not send messages
- Optional Cloudflare Workers AI endpoint
- Installable PWA shell and offline caching
- Health check at `/api/health`

## Important boundaries
Discovery cards are integration placeholders, not active connections to social networks. Google, TikTok, Instagram, Facebook, YouTube, Reddit, X, Telegram and LinkedIn each have their own API permissions, rate limits and terms. This MVP does not scrape private accounts, private messages or access-controlled content. It does not send email/DMs or process crypto payments. Those require approved provider integrations, credentials and verified webhooks.

## Deploy to Cloudflare
Cloudflare account access and creation of account-specific resources must be completed by the account owner. Never share your Cloudflare password or API token in chat.

1. Open the folder `quantum-leads-ai` in this branch.
2. In Cloudflare, create a D1 database named `quantum-leads-ai-db`.
3. Copy the database ID into `wrangler.jsonc`, replacing `REPLACE_AFTER_CREATING_D1`.
4. In a trusted Node.js environment, run:
   ```sh
   npm install
   npx wrangler login
   npx wrangler secret put OWNER_PASSWORD
   npx wrangler secret put SESSION_SECRET
   npx wrangler d1 migrations apply quantum-leads-ai-db --remote
   npx wrangler deploy
   ```
5. Set a strong unique owner password. Use a random SESSION_SECRET of at least 32 characters.
6. Open the workers.dev URL printed by Wrangler and check `/api/health`.

The Worker requires the D1 binding `DB`, the static asset binding `ASSETS`, and secrets `OWNER_PASSWORD` and `SESSION_SECRET`. The optional `AI` binding enables the assistant endpoint; remove it from `wrangler.jsonc` if you do not want Workers AI.

## Local checks
The JavaScript files pass Node syntax checks. Live deployment still requires the Cloudflare D1 database ID, secrets and account authorization.
