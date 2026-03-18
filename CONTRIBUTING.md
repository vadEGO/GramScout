# Contributing to GramScout

Thank you for your interest in contributing to GramScout!

## Getting Started

```bash
git clone https://github.com/vadEGO/GramScout.git
cd GramScout
cp .env.example .env
docker compose up -d
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/         # REST API routes (110 endpoints)
│   ├── models/          # SQLAlchemy ORM models
│   ├── services/        # Business logic
│   ├── telegram/        # Telethon client manager
│   ├── ai/              # OpenRouter LLM integration
│   └── core/            # Database, Redis, logging
frontend/
├── src/
│   ├── pages/           # 14 page components
│   ├── data/            # Static data (countries)
│   └── ThemeContext.tsx  # Light/dark/auto theme
```

## Development

```bash
# Backend
cd backend
pip install -r requirements/dev.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Adding Features

1. Create a model in `backend/app/models/`
2. Add a service in `backend/app/services/`
3. Add API routes in `backend/app/api/v1/`
4. Update the router in `backend/app/api/v1/router.py`
5. Add a UI page in `frontend/src/pages/`
6. Register the route in `frontend/src/App.tsx`

## Testing

```bash
# Run API tests
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/accounts

# Run all tests
for endpoint in health accounts proxies channels commenting reactions warming parser prompts logs analytics settings agent revenue; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/$endpoint
done
```

## Code Style

- Python: PEP 8, type hints
- TypeScript: Strict mode, functional components
- CSS: CSS variables, no hardcoded colors
- Commits: Conventional commits (feat, fix, chore, docs)

## Areas for Contribution

- [ ] WebSocket real-time updates
- [ ] Proper Alembic migrations
- [ ] Mobile app (React Native)
- [ ] More LLM providers
- [ ] Analytics dashboards
- [ ] i18n support
- [ ] Test coverage
