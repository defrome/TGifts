# Dockerfile
# enable BuildKit secrets support
# syntax=docker/dockerfile:1.4

FROM python:3.11-slim AS builder
WORKDIR /TGifts

# copy source (checked out by GitHub Actions)
COPY . .

# decode and write certs via BuildKit secrets
RUN --mount=type=secret,id=backend_cert \
    --mount=type=secret,id=backend_key \
    mkdir -p /certs && \
    cat /run/secrets/backend_cert | base64 -d > /certs/cert.pem && \
    cat /run/secrets/backend_key  | base64 -d > /certs/key.pem

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /TGifts

# copy app and certs from builder
COPY --from=builder /TGifts /TGifts
COPY --from=builder /certs /certs

EXPOSE 443
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "443", \
     "--ssl-keyfile", "/certs/key.pem", "--ssl-certfile", "/certs/cert.pem"]
