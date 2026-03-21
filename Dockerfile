FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/
RUN uv sync --frozen --no-dev --extra skills 2>/dev/null || uv sync --frozen --no-dev
RUN uv pip install gunicorn uvicorn --python .venv/bin/python
ENV PATH="/app/.venv/bin:$PATH"
ENV TOOLUNIVERSE_LAZY_LOADING=true
EXPOSE 8000
CMD ["gunicorn", "labclaw.skills.server:app", \
     "-w", "2", "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", "--preload", \
     "--timeout", "120", \
     "--max-requests", "1000", "--max-requests-jitter", "50"]
