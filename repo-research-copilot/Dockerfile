ARG RUNTIME_IMAGE=gcr.io/distroless/python3-debian12:nonroot@sha256:7d1042ce588ab97019fe95c24ffca7bc5a82ccdac572511d5e09bda4435c89c5
ARG BUILDER_IMAGE=cgr.dev/chainguard/python:latest-dev@sha256:cc44af329fb005726e90f7927bc53a7335497e361ab782e703ba118db1b0d46b

FROM ${RUNTIME_IMAGE} AS runtime-base

FROM ${BUILDER_IMAGE} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY src ./src

FROM runtime-base

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY --from=builder /install /usr/local
COPY --from=builder /app/src ./src

EXPOSE 8010

CMD ["-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8010"]
