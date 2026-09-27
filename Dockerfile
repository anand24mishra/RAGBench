FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd --create-home --uid 10001 ragbench

COPY requirements.txt pyproject.toml ./
COPY ragbench ./ragbench
COPY evaluation ./evaluation
COPY experiments ./experiments
RUN python -m pip install --upgrade pip && python -m pip install . -r requirements.txt

USER ragbench
EXPOSE 8000

CMD ["uvicorn", "ragbench.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
