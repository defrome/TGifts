# Dockerfile
FROM python:3.11-slim AS builder

# Build-time args
ARG GIT_TOKEN
ARG CERT_PEM_B64
ARG KEY_PEM_B64

WORKDIR /TGifts

# Clone private repo
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/* \
 && git clone https://${GIT_TOKEN}@github.com/defrome/TGifts.git . \
 && unset GIT_TOKEN

# Decode certificates
RUN mkdir -p /certs \
 && echo "${CERT_PEM_B64}" | base64 -d > /certs/cert.pem \
 && echo "${KEY_PEM_B64}"  | base64 -d > /certs/key.pem

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Final image
FROM python:3.11-slim

WORKDIR /TGifts

# Copy application + certs from builder
COPY --from=builder /TGifts /TGifts
COPY --from=builder /certs /certs

EXPOSE 443

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "443", \
     "--ssl-keyfile", "/certs/key.pem", \
     "--ssl-certfile", "/certs/cert.pem"]
