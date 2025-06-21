FROM python:3.11-slim

WORKDIR /TGifts

ARG GIT_TOKEN
ENV GIT_TOKEN=${GIT_TOKEN}

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/* \
 && git clone https://${GIT_TOKEN}@github.com/defrome/TGifts.git . \
 && unset GIT_TOKEN

COPY certs/*.pem /certs/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 443

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "443", \
     "--ssl-keyfile", "/certs/key.pem", \
     "--ssl-certfile", "/certs/cert.pem"]
