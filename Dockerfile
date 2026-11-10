FROM python:3.12-slim

WORKDIR /srv/inventory

RUN groupadd -g 10005 svc && \
    useradd -u 10005 -g svc -M -s /usr/sbin/nologin svc

COPY app.py ./

RUN mkdir -p /data && chown -R svc:svc /data /srv/inventory

USER svc:10005

ENV PORT=8005 \
    MESSAGE="Inventory online" \
    APP_VERSION="1.0" \
    PYTHONUNBUFFERED=1

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8005/health', timeout=3).status==200 else 1)"

CMD ["python", "app.py"]