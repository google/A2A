FROM python:3.13-slim

WORKDIR /app

COPY . .

WORKDIR /app/samples/python
RUN pip install "uv>=0.1.24"
RUN uv pip install -e . --system
WORKDIR /app/samples/python/agents/ag2

CMD ["uv", "run", "."]
