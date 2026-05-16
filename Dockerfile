FROM python:3.12-slim

ENV TZ=Asia/Tokyo
LABEL io.modelcontextprotocol.server.name="io.github.rikitonoto/gmocoin-fx-mcp"
RUN pip install uv

WORKDIR /app

# Copy only dependency files first (layer cache)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy the rest of the project
COPY src/ ./src/

EXPOSE 8000

CMD ["uv", "run", "src/main.py"]
