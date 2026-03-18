\# Technical Implementation: Complete Architecture & Design Document

\---

\## 1. Technology Stack Selection

\### 1.1 Core Language: \*\*Python 3.11+\*\*

\*\*Why Python:\*\*

\- Both Telethon and Pyrogram (Telegram client libraries) are Python-native

\- Async/await ecosystem is mature (asyncio)

\- AI/LLM integration libraries are Python-first

\- Rapid prototyping with production-grade capability

\- Largest ecosystem for Telegram automation

\### 1.2 Telegram Client Library: \*\*Telethon 1.36+\*\*

\*\*Why Telethon over Pyrogram:\*\*

\- More granular control over MTProto layer

\- Better session management (string-based sessions that can be stored in DB)

\- More mature tdata import utilities

\- Better handling of flood waits and bans

\- Larger community for edge cases

\*\*Secondary:\*\* Pyrogram for specific features where its API is cleaner (optional, not required)

\### 1.3 Database: \*\*PostgreSQL 16 + Redis 7\*\*

\*\*PostgreSQL\*\* - primary data store:

\- Account metadata, proxies, channels, logs, configurations

\- JSONB columns for flexible schema (action logs, patterns)

\- Excellent indexing for query-heavy workloads

\- Built-in full-text search for channel parsing results

\*\*Redis\*\* - real-time state + queue:

\- Pub/Sub for real-time dashboard updates

\- Stream-based queues for action processing

\- Session token caching

\- Rate limiter state (sliding windows)

\- Active account connection pools

\### 1.4 Message Queue: \*\*Redis Streams\*\* (primary) + \*\*Celery\*\* (fallback)

\*\*Why Redis Streams over RabbitMQ/Kafka:\*\*

\- Already using Redis; reduces infrastructure

\- Consumer groups handle multi-worker distribution naturally

\- Built-in acknowledgment and retry

\- Simpler operational overhead than Kafka for this scale

\*\*Celery\*\* only if you need scheduled/recurring tasks with complex retry logic.

\### 1.5 AI/LLM Integration: \*\*OpenAI API\*\* (primary) + \*\*Local LLM\*\* (fallback)

\- OpenAI GPT-4o-mini for comment generation (cost-effective, fast)

\- Configurable: users can supply their own API keys

\- Fallback: locally hosted Ollama/llama.cpp for cost reduction

\- Prompt templates stored in DB, versioned

\### 1.6 Frontend: \*\*React 18 + Vite + TailwindCSS + shadcn/ui\*\*

\- Fast development, rich ecosystem

\- Tailwind for rapid styling

\- shadcn/ui for consistent component library

\- WebSocket connection for real-time logs

\- Chart.js/Recharts for analytics dashboards

\### 1.7 Backend API: \*\*FastAPI\*\*

\- Async-native, pairs perfectly with asyncio Telegram clients

\- Automatic OpenAPI documentation

\- WebSocket support for real-time updates

\- Pydantic validation

\- High performance (uvicorn + uvloop)

\### 1.8 Deployment: \*\*Docker + Docker Compose\*\* (self-hosted)

\- Single-server deployment for most users

\- Docker Compose orchestrates: API, workers, Redis, PostgreSQL, frontend

\- Optional: Kubernetes for multi-server scaling

\- Optional: Fly.io / Railway for managed hosting

\---

\## 2. High-Level Architecture

\`\`\`

┌─────────────────────────────────────────────────────────────────────┐

│ FRONTEND (React) │

│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │

│ │ Accounts │ │ Channels │ │Commenting│ │ Reactions│ │ Analytics│ │

│ │ Manager │ │ Parser │ │ Engine │ │ Engine │ │Dashboard │ │

│ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │

│ └────────────┴────────────┴────────────┴────────────┘ │

│ │ WebSocket + REST │

└──────────────────────────────┼──────────────────────────────────────┘

│

┌──────────────────────────────┼──────────────────────────────────────┐

│ API GATEWAY (FastAPI) │

│ ┌──────────────────────────────────────────────────────────────┐ │

│ │ REST Endpoints │ WebSocket Hub │ Auth Middleware │ │

│ └──────────────────────────────────────────────────────────────┘ │

│ │ │ │ │

└───────────┼────────────────────┼────────────────────┼────────────────┘

│ │ │

┌───────────┼────────────────────┼────────────────────┼────────────────┐

│ ▼ ▼ ▼ │

│ ┌──────────────────────────────────────────────────────────────┐ │

│ │ SERVICE LAYER │ │

│ │ │ │

│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │ │

│ │ │ Account │ │ Channel │ │ AI/Prompt │ │ │

│ │ │ Service │ │ Service │ │ Service │ │ │

│ │ └──────┬──────┘ └──────┬──────┘ └────────────┬────────────┘ │ │

│ │ │ │ │ │ │

│ │ ┌──────┴──────┐ ┌──────┴──────┐ ┌─────────────┴────────────┐│ │

│ │ │ Proxy │ │ Parsing │ │ Protection ││ │

│ │ │ Service │ │ Service │ │ Service ││ │

│ │ └─────────────┘ └─────────────┘ └──────────────────────────┘│ │

│ └──────────────────────────────────────────────────────────────┘ │

│ │ │

└──────────────────────────────┼───────────────────────────────────────┘

│

┌──────────────────────────────┼───────────────────────────────────────┐

│ WORKER LAYER (Asyncio) │

│ │

│ ┌────────────────┐ ┌────────────────┐ ┌────────────────────────┐ │

│ │ Comment │ │ Reaction │ │ Warming │ │

│ │ Workers (N) │ │ Workers (M) │ │ Workers (K) │ │

│ │ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │ │

│ │ │TG Client │ │ │ │TG Client │ │ │ │TG Client │ │ │

│ │ │Pool │ │ │ │Pool │ │ │ │Pool │ │ │

│ │ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │ │

│ └────────┬───────┘ └────────┬───────┘ └──────────┬─────────────┘ │

│ │ │ │ │

│ ┌────────┴───────────────────┴──────────────────────┴─────────────┐│

│ │ TELETHON CLIENT MANAGER ││

│ │ ┌──────────────────────────────────────────────────────────┐ ││

│ │ │ Connection Pool │ Session Manager │ Flood Wait │ ││

│ │ │ (per account) │ (tdata→session) │ Handler │ ││

│ │ └──────────────────────────────────────────────────────────┘ ││

│ └─────────────────────────────────────────────────────────────────┘│

│ │ │

└──────────────────────────────┼───────────────────────────────────────┘

│ MTProto

▼

┌─────────────┐

│ Telegram │

│ Servers │

└─────────────┘

│

┌──────────────────────────────┼───────────────────────────────────────┐

│ DATA LAYER │

│ │

│ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────┐ │

│ │ PostgreSQL │ │ Redis │ │ File Storage │ │

│ │ │ │ │ │ │ │

│ │ - accounts │ │ - action queues │ │ - tdata files │ │

│ │ - proxies │ │ - rate limiters │ │ - session files │ │

│ │ - channels │ │ - pub/sub │ │ - avatars │ │

│ │ - logs │ │ - cache │ │ - exports │ │

│ │ - configs │ │ - active state │ │ │ │

│ │ - patterns │ │ │ │ │ │

│ │ - prompts │ │ │ │ │ │

│ └──────────────────┘ └──────────────────┘ └───────────────────┘ │

│ │

└──────────────────────────────────────────────────────────────────────┘

\`\`\`

\---

\## 3. Project Structure

\`\`\`

gram-gpt/

├── docker-compose.yml

├── docker-compose.prod.yml

├── .env.example

├── Makefile

│

├── backend/

│ ├── Dockerfile

│ ├── pyproject.toml

│ ├── requirements/

│ │ ├── base.txt

│ │ ├── dev.txt

│ │ └── prod.txt

│ │

│ ├── app/

│ │ ├── \__init_\_.py

│ │ ├── main.py # FastAPI application entry

│ │ ├── config.py # Settings via pydantic-settings

│ │ ├── dependencies.py # DI containers

│ │ │

│ │ ├── api/ # REST + WebSocket routes

│ │ │ ├── \__init_\_.py

│ │ │ ├── v1/

│ │ │ │ ├── \__init_\_.py

│ │ │ │ ├── router.py # Main v1 router aggregator

│ │ │ │ ├── accounts.py # CRUD + actions

│ │ │ │ ├── proxies.py # CRUD + validation

│ │ │ │ ├── channels.py # CRUD + parsing

│ │ │ │ ├── commenting.py # Start/stop/config

│ │ │ │ ├── reactions.py # Start/stop/config

│ │ │ │ ├── warming.py # Start/stop/config

│ │ │ │ ├── prompts.py # CRUD + templates

│ │ │ │ ├── analytics.py # Stats, reports

│ │ │ │ └── protection.py # AI protection stats

│ │ │ ├── ws/

│ │ │ │ ├── \__init_\_.py

│ │ │ │ ├── live_logs.py # Real-time log streaming

│ │ │ │ ├── dashboard.py # Dashboard metrics push

│ │ │ │ └── account_status.py # Account status changes

│ │ │ └── middleware/

│ │ │ ├── auth.py

│ │ │ ├── rate_limit.py

│ │ │ └── error_handler.py

│ │ │

│ │ ├── models/ # SQLAlchemy ORM models

│ │ │ ├── \__init_\_.py

│ │ │ ├── account.py

│ │ │ ├── proxy.py

│ │ │ ├── channel.py

│ │ │ ├── target_channel.py

│ │ │ ├── action_log.py

│ │ │ ├── ban_event.py

│ │ │ ├── prompt_template.py

│ │ │ ├── protection_pattern.py

│ │ │ ├── warming_schedule.py

│ │ │ ├── comment_job.py

│ │ │ ├── reaction_job.py

│ │ │ └── analytics_snapshot.py

│ │ │

│ │ ├── schemas/ # Pydantic request/response

│ │ │ ├── \__init_\_.py

│ │ │ ├── account.py

│ │ │ ├── proxy.py

│ │ │ ├── channel.py

│ │ │ ├── commenting.py

│ │ │ ├── reactions.py

│ │ │ ├── warming.py

│ │ │ ├── analytics.py

│ │ │ └── common.py # Pagination, filters

│ │ │

│ │ ├── services/ # Business logic

│ │ │ ├── \__init_\_.py

│ │ │ ├── account_service.py

│ │ │ ├── proxy_service.py

│ │ │ ├── channel_service.py

│ │ │ ├── parsing_service.py

│ │ │ ├── comment_service.py

│ │ │ ├── reaction_service.py

│ │ │ ├── warming_service.py

│ │ │ ├── ai_service.py # LLM integration

│ │ │ ├── prompt_service.py

│ │ │ ├── protection_service.py # Anti-detection

│ │ │ ├── analytics_service.py

│ │ │ ├── import_service.py # tdata/session import

│ │ │ └── export_service.py

│ │ │

│ │ ├── workers/ # Background task processors

│ │ │ ├── \__init_\_.py

│ │ │ ├── base_worker.py # Abstract worker class

│ │ │ ├── comment_worker.py

│ │ │ ├── reaction_worker.py

│ │ │ ├── warming_worker.py

│ │ │ ├── parsing_worker.py

│ │ │ ├── protection_worker.py # Pattern analysis

│ │ │ ├── analytics_worker.py # Snapshot aggregation

│ │ │ └── supervisor.py # Worker lifecycle manager

│ │ │

│ │ ├── telegram/ # Telegram client abstraction

│ │ │ ├── \__init_\_.py

│ │ │ ├── client_manager.py # Connection pool

│ │ │ ├── session_manager.py # tdata→session conversion

│ │ │ ├── account_actions.py # High-level TG actions

│ │ │ ├── channel_actions.py # Channel-specific actions

│ │ │ ├── message_monitor.py # Post detection

│ │ │ ├── flood_handler.py # FloodWait handling

│ │ │ └── exceptions.py # TG-specific exceptions

│ │ │

│ │ ├── core/ # Shared utilities

│ │ │ ├── \__init_\_.py

│ │ │ ├── database.py # SQLAlchemy async engine

│ │ │ ├── redis.py # Redis connection pool

│ │ │ ├── queue.py # Redis Streams queue

│ │ │ ├── events.py # Internal event bus

│ │ │ ├── scheduler.py # APScheduler wrapper

│ │ │ ├── security.py # Encryption for sensitive data

│ │ │ ├── logging.py # Structured logging config

│ │ │ └── exceptions.py # Custom exceptions

│ │ │

│ │ └── ai/ # AI/LLM subsystem

│ │ ├── \__init_\_.py

│ │ ├── llm_client.py # OpenAI/local LLM abstraction

│ │ ├── prompt_engine.py # Prompt templating + selection

│ │ ├── pattern_analyzer.py # Ban pattern detection

│ │ ├── behavior_generator.py # Human behavior simulation

│ │ └── keyword_expander.py # Channel search expansion

│ │

│ ├── migrations/ # Alembic migrations

│ │ ├── alembic.ini

│ │ └── versions/

│ │

│ ├── tests/

│ │ ├── unit/

│ │ ├── integration/

│ │ └── fixtures/

│ │

│ └── scripts/

│ ├── seed_data.py

│ ├── import_accounts_batch.py

│ └── export_analytics.py

│

├── frontend/

│ ├── Dockerfile

│ ├── package.json

│ ├── vite.config.ts

│ ├── tailwind.config.ts

│ ├── tsconfig.json

│ │

│ ├── src/

│ │ ├── main.tsx

│ │ ├── App.tsx

│ │ │

│ │ ├── pages/

│ │ │ ├── Dashboard.tsx

│ │ │ ├── Accounts.tsx

│ │ │ ├── AccountDetail.tsx

│ │ │ ├── Proxies.tsx

│ │ │ ├── Channels.tsx

│ │ │ ├── ChannelParser.tsx

│ │ │ ├── Commenting.tsx

│ │ │ ├── Reactions.tsx

│ │ │ ├── Warming.tsx

│ │ │ ├── Prompts.tsx

│ │ │ ├── Analytics.tsx

│ │ │ ├── Protection.tsx

│ │ │ └── Settings.tsx

│ │ │

│ │ ├── components/

│ │ │ ├── layout/

│ │ │ │ ├── Sidebar.tsx

│ │ │ │ ├── Header.tsx

│ │ │ │ └── PageWrapper.tsx

│ │ │ ├── accounts/

│ │ │ │ ├── AccountTable.tsx

│ │ │ │ ├── AccountImportModal.tsx

│ │ │ │ ├── AccountCard.tsx

│ │ │ │ ├── AccountStatusBadge.tsx

│ │ │ │ └── ProfileEditor.tsx

│ │ │ ├── channels/

│ │ │ │ ├── ChannelTable.tsx

│ │ │ │ ├── ChannelParserConfig.tsx

│ │ │ │ ├── ChannelCard.tsx

│ │ │ │ └── FolderBuilder.tsx

│ │ │ ├── commenting/

│ │ │ │ ├── CommentingConfig.tsx

│ │ │ │ ├── PromptEditor.tsx

│ │ │ │ ├── ThreadManager.tsx

│ │ │ │ └── LiveCommentFeed.tsx

│ │ │ ├── reactions/

│ │ │ │ ├── ReactionConfig.tsx

│ │ │ │ └── ReactionFeed.tsx

│ │ │ ├── warming/

│ │ │ │ ├── WarmingScheduler.tsx

│ │ │ │ └── WarmingProgress.tsx

│ │ │ ├── analytics/

│ │ │ │ ├── StatsCard.tsx

│ │ │ │ ├── TimeSeriesChart.tsx

│ │ │ │ ├── BanRateChart.tsx

│ │ │ │ └── ConversionFunnel.tsx

│ │ │ └── common/

│ │ │ ├── DataTable.tsx

│ │ │ ├── StatusIndicator.tsx

│ │ │ ├── LogViewer.tsx

│ │ │ ├── ConfirmDialog.tsx

│ │ │ └── MetricCard.tsx

│ │ │

│ │ ├── hooks/

│ │ │ ├── useWebSocket.ts

│ │ │ ├── useAccounts.ts

│ │ │ ├── useCommenting.ts

│ │ │ ├── useAnalytics.ts

│ │ │ └── useRealtimeLogs.ts

│ │ │

│ │ ├── lib/

│ │ │ ├── api.ts # Axios/fetch wrapper

│ │ │ ├── websocket.ts # WS client

│ │ │ ├── utils.ts

│ │ │ └── constants.ts

│ │ │

│ │ ├── stores/ # Zustand state management

│ │ │ ├── accountStore.ts

│ │ │ ├── commentingStore.ts

│ │ │ └── dashboardStore.ts

│ │ │

│ │ └── types/ # TypeScript interfaces

│ │ ├── account.ts

│ │ ├── channel.ts

│ │ ├── commenting.ts

│ │ └── analytics.ts

│ │

│ └── public/

│

└── docs/

├── architecture.md

├── api.md

└── deployment.md

\`\`\`

\---

\## 4. Detailed Component Design

\### 4.1 Telegram Client Manager

This is the most critical component - it manages all Telegram connections.

\`\`\`

┌──────────────────────────────────────────────────────────────┐

│ TELETHON CLIENT MANAGER │

│ │

│ ┌─────────────────────────────────────────────────────────┐ │

│ │ Session Registry │ │

│ │ │ │

│ │ account_id → { │ │

│ │ session_string: str (encrypted, in DB) │ │

│ │ client: Telethon client instance (in memory) │ │

│ │ status: CONNECTING | CONNECTED | BANNED | FLOOD_WAIT │ │

│ │ last_active: timestamp │ │

│ │ current_action: str | None │ │

│ │ flood_wait_until: timestamp | None │ │

│ │ } │ │

│ └─────────────────────────────────────────────────────────┘ │

│ │

│ ┌─────────────────────────────────────────────────────────┐ │

│ │ Connection Pool │ │

│ │ │ │

│ │ Max concurrent connections: configurable (default 50) │ │

│ │ Connection lifecycle: │ │

│ │ 1. Lazy connect (only when needed) │ │

│ │ 2. Keep-alive pings every 60s │ │

│ │ 3. Auto-reconnect on disconnect (max 3 retries) │ │

│ │ 4. Graceful shutdown on ban detection │ │

│ └─────────────────────────────────────────────────────────┘ │

│ │

│ ┌─────────────────────────────────────────────────────────┐ │

│ │ Rate Limiter │ │

│ │ │ │

│ │ Per-account sliding window: │ │

│ │ - Actions per minute │ │

│ │ - Actions per hour │ │

│ │ - Actions per day │ │

│ │ │ │

│ │ Per-channel limits: │ │

│ │ - Comments per hour in same channel │ │

│ │ - Reactions per minute in same chat │ │

│ │ │ │

│ │ Global limits: │ │

│ │ - Total actions across all accounts per minute │ │

│ └─────────────────────────────────────────────────────────┘ │

│ │

│ ┌─────────────────────────────────────────────────────────┐ │

│ │ Flood Wait Handler │ │

│ │ │ │

│ │ On FloodWaitError: │ │

│ │ 1. Parse wait_seconds from exception │ │

│ │ 2. Mark account as FLOOD_WAIT │ │

│ │ 3. Schedule retry after wait_seconds + buffer │ │

│ │ 4. Log event for pattern analysis │ │

│ │ 5. Notify worker to switch to next account │ │

│ │ │ │

│ │ Escalation: │ │

│ │ - First flood: wait as requested │ │

│ │ - 3 floods in 1 hour: pause account 4 hours │ │

│ │ - 5 floods in 24 hours: mark for review │ │

│ └─────────────────────────────────────────────────────────┘ │

└──────────────────────────────────────────────────────────────┘

\`\`\`

\*\*Key Implementation Details:\*\*

\*\*tdata Import Process:\*\*

1\. Receive uploaded tdata zip/folder

2\. Extract \`key_data\`, \`map\`, \`settings\`, \`userconf\` files

3\. Parse Telegram Desktop's binary format to extract session keys

4\. Create Telethon \`StringSession\` from extracted keys

5\. Attempt connection to validate session

6\. On success: encrypt session string, store in DB, mark account as VALID

7\. On failure: mark as INVALID, store error reason

\*\*Session String Storage:\*\*

\- Each session string is AES-256 encrypted before DB storage

\- Encryption key derived from application master key + account_id (unique IV)

\- Decrypted only in memory, never written to disk unencrypted

\- Master key loaded from environment variable at startup

\*\*Connection Lifecycle:\*\*

\`\`\`

1\. Worker needs account X

2\. ClientManager.get_client(account_id)

3\. Check if client exists in memory AND is connected

4\. If not: create Telethon(StringSession(decrypt(session_string)))

5\. Connect to Telegram

6\. Validate session (get_me())

7\. Return client

8\. After action: client returned to pool (kept alive for reuse)

9\. Periodic cleanup: disconnect idle clients after 5 minutes

\`\`\`

\### 4.2 Session Manager (tdata Conversion)

\`\`\`

Input: tdata folder (extracted)

│

├── Parse key_data (contains authorization key)

│ ├── Read binary format

│ ├── Extract DC ID

│ ├── Extract auth key (256 bytes)

│ └── Extract server address

│

├── Parse map (contains user info)

│ ├── Extract user ID

│ ├── Extract phone number

│ └── Extract DC configuration

│

├── Create Telethon StringSession

│ ├── Encode DC ID (1 byte)

│ ├── Encode server address (variable)

│ ├── Encode auth key (256 bytes)

│ └── Base64 encode entire string

│

├── Validate session

│ ├── Connect using StringSession

│ ├── Call get_me()

│ ├── Verify user matches expected

│ └── Disconnect

│

└── Output: {

session_string: str,

user_id: int,

phone: str,

dc_id: int,

is_premium: bool,

first_name: str,

last_name: str | None,

username: str | None

}

\`\`\`

\### 4.3 Comment Worker Design

\`\`\`

┌──────────────────────────────────────────────────────────────────┐

│ COMMENT WORKER (Single Instance) │

│ │

│ ┌─────────────────────────────────────────────────────────────┐ │

│ │ Main Loop (async while True) │ │

│ │ │ │

│ │ 1. Fetch next job from Redis Stream │ │

│ │ (consumer group: "comment_workers", consumer: worker_id)│ │

│ │ │ │

│ │ 2. Job contains: │ │

│ │ { │ │

│ │ job_id: UUID, │ │

│ │ account_id: UUID, │ │

│ │ target_channel: str, │ │

│ │ post_id: int, │ │

│ │ post_text: str, │ │

│ │ post_language: str, │ │

│ │ prompt_id: UUID, │ │

│ │ protection_level: enum, │ │

│ │ scheduled_at: timestamp, │ │

│ │ priority: int │ │

│ │ } │ │

│ │ │ │

│ │ 3. Pre-action protection delay │ │

│ │ - Get delay from ProtectionService │ │

│ │ - Delay = base + random(0, variance