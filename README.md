# Mission Control 🎯

EMVY Crew Operations Dashboard — live view of pipeline, agents, and current work.

![Next.js](https://img.shields.io/badge/Next.js-15-black)
![Supabase](https://img.shields.io/badge/Supabase-Realtime-green)
![Vercel](https://img.shields.io/badge/Vercel-Deploy-black)

## Features

- **Live Pipeline** — Kanban view of all clients through EMVY pipeline
- **Agent Status** — Real-time heartbeat indicators (Callie, Atlas, Executioner)
- **Current Work** — Track Mew + Yuki active projects
- **Knowledge Bases** — Agent learning stats
- **Quick Actions** — Create clients, health checks, alert history
- **Discord Alerts** — Auto-alerts for stuck clients (>24h) and missing agents (>30min)

## Tech Stack

- **Next.js 15** (App Router)
- **Tailwind CSS**
- **Supabase** (Database + Realtime)
- **Vercel** (Deployment)

## Setup

### 1. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run `supabase-schema.sql`
3. Copy your project URL and anon key

### 2. Environment Variables

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

Fill in your values:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DASHBOARD_PASSWORD=your-secure-password
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook
```

### 3. Deploy to Vercel

```bash
npm install
npm run build
npx vercel --prod
```

Or connect the GitHub repo to Vercel and add env vars in dashboard.

### 4. Discord Webhook (Optional)

1. In Discord, go to Server Settings → Integrations → Webhooks
2. Create a webhook, copy the URL
3. Add to `DISCORD_WEBHOOK_URL` env var

## Views

### Pipeline
- 6 stages: INBOUND → PRE-CALL RESEARCH → CALL → AUDIT → BUILD → DONE
- Color-coded cards with time-in-stage
- Agent assignment shown on each card

### Agent Status
- GREEN = Active (<5min heartbeat)
- YELLOW = Idle (5-30min heartbeat)
- RED = Stuck (>30min heartbeat)

### Current Work
- Active/Blocked/Done project tracking
- Owner: Mew, Yuki, or Claude Code
- Real-time status updates

### Knowledge Bases
- Atlas: Question Library, Audit Frameworks
- Gandalf: Tool Database, Integration Guides
- Executioner: Build Patterns, Mistake Log

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth` | POST | Authenticate with password |
| `/api/clients` | POST | Create new pipeline job |
| `/api/alerts` | GET | Get alert history |
| `/api/alerts` | POST | Trigger Discord alert |
| `/api/health-check` | POST | Ping all agents |

## Demo Mode

Without Supabase configured, the dashboard runs in demo mode with sample data. This lets you preview all views and UI components.

## License

Internal — EMVY Crew
