# Self-hosting image: runs the Flask API (5001) and the Vite dev server (3000)
# together via `npm run dev`. Production hosting uses Render + Vercel instead.
FROM python:3.11-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs npm \
 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Lockfiles first so dependency layers stay cached across code changes.
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json frontend/
COPY backend/pyproject.toml backend/uv.lock backend/
RUN npm ci && npm ci --prefix frontend && uv sync --frozen --project backend

COPY . .

EXPOSE 3000 5001
CMD ["npm", "run", "dev"]
