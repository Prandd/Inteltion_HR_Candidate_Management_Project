FROM python:3.11-slim

WORKDIR /app

# Microsoft ODBC Driver 18 for SQL Server - needed by pyodbc for the Azure SQL
# Database (free tier) DATABASE_URL. curl/gnupg only exist to fetch and verify
# Microsoft's apt repo; ACCEPT_EULA=Y is required non-interactively by the
# package itself, not something we're skipping past.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg \
    && curl -sSL -O https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev \
    && apt-get purge -y --auto-remove curl gnupg \
    && rm -rf /var/lib/apt/lists/*

# Build context is the repo root (see docker-compose.yml), so paths are backend/*
COPY backend/requirements.txt ./requirements.txt
# python:3.11-slim ships pip 24.0, which crashes resolving the PyPI JSON simple
# API (Link.from_json UnboundLocalError). Upgrade before installing.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
