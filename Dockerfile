FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system --gid 10001 siptic \
    && useradd --system --uid 10001 --gid siptic --home /app siptic

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt

COPY --chown=siptic:siptic . .
RUN chmod 755 /app/deploy/docker/web/entrypoint.sh

USER siptic

EXPOSE 8000

ENTRYPOINT ["/app/deploy/docker/web/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
