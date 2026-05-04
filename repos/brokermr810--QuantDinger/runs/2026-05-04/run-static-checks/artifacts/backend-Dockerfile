# QuantDinger Backend API Dockerfile
# BASE_IMAGE can be overridden from docker-compose (e.g. IMAGE_PREFIX for mirror pulls).
ARG BASE_IMAGE=python:3.12-slim-bookworm
FROM ${BASE_IMAGE}

WORKDIR /app

# Apt: try Aliyun Debian mirror first (typical win in mainland); on failure restore official.
# No env vars — same Dockerfile works abroad (falls back) and in CN (usually hits mirror).
RUN set -eux; \
    APT_TIMEOUT='Acquire::http::Timeout=35'; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      cp /etc/apt/sources.list.d/debian.sources /tmp/debian.sources.bak; \
      sed -i -E \
        's|https?://deb.debian.org|https://mirrors.aliyun.com|g; s|https?://security.debian.org|https://mirrors.aliyun.com|g' \
        /etc/apt/sources.list.d/debian.sources; \
      if ! apt-get -o "$APT_TIMEOUT" -o Acquire::https::Timeout=35 update; then \
        cp /tmp/debian.sources.bak /etc/apt/sources.list.d/debian.sources; \
        sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/*.sources 2>/dev/null || true; \
        apt-get -o "$APT_TIMEOUT" update; \
      fi; \
    else \
      sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/*.sources 2>/dev/null || true; \
      apt-get -o "$APT_TIMEOUT" update; \
    fi; \
    apt-get install -y --no-install-recommends --fix-missing \
      ca-certificates \
      curl \
      build-essential \
      python3-dev \
      libffi-dev \
      libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Pip: try Aliyun PyPI first; on any failure retry default index (PyPI.org).
RUN set -eux; \
    pip install --no-cache-dir --prefer-binary --timeout 180 \
        -i https://mirrors.aliyun.com/pypi/simple/ \
        -r requirements.txt \
      || pip install --no-cache-dir --prefer-binary --timeout 180 -r requirements.txt; \
    apt-get purge -y --auto-remove build-essential python3-dev libffi-dev libssl-dev; \
    rm -rf /var/lib/apt/lists/*

COPY . .

COPY docker-entrypoint.sh /usr/local/bin/
RUN sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
    && chmod +x /usr/local/bin/docker-entrypoint.sh

RUN mkdir -p logs data/memory

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV PYTHON_API_HOST=0.0.0.0
ENV PYTHON_API_PORT=5000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn_config.py", "run:app"]
