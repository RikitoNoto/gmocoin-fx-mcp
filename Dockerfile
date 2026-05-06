FROM python:3.12-slim

ENV TZ=Asia/Tokyo
RUN pip install uv

WORKDIR /app

# Copy only dependency files first (layer cache)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy the rest of the project
COPY src/ ./src/
COPY .env ./.env

CMD ["uv", "run", "src/main.py"]
