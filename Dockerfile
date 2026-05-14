# Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Build final image
FROM python:3.12-slim
WORKDIR /app

# Install uv for fast Python package management
RUN pip install uv

# Copy and install API dependencies
COPY api/pyproject.toml api/uv.lock ./api/
WORKDIR /app/api
RUN uv sync --frozen --no-dev

# Copy API source
COPY api/app ./app/

# Copy built frontend
COPY --from=frontend-build /app/web/dist /app/web/dist

# Copy templates and skills (needed for the app)
COPY templates /app/templates
COPY skills /app/skills

# Create plans directory
RUN mkdir -p /app/.cursor/plans

ENV UIPLAN_PLANS_ROOT=/app/.cursor/plans
ENV PYTHONUNBUFFERED=1

# Serve frontend via API (add static file serving)
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
