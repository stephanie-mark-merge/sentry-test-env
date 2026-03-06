# Integration Test Sandbox
For testing Sentry and Honeycomb integrations

## Setup

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install django sentry-sdk opentelemetry-distro opentelemetry-exporter-otlp opentelemetry-api opentelemetry-instrumentation-django
```

2. Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

## Running

### Sentry only (standard Django):
```bash
source venv/bin/activate
export SENTRY_DSN=your-dsn-here
python manage.py runserver
```

### Sentry + Honeycomb (with OpenTelemetry auto-instrumentation):
```bash
source venv/bin/activate
export SENTRY_DSN=your-dsn-here
export DJANGO_SETTINGS_MODULE=sandbox_project.settings
export OTEL_SERVICE_NAME=sentry-honeycomb-sandbox
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=your-api-key"
venv/bin/opentelemetry-instrument venv/bin/python manage.py runserver
```

## Test Endpoints

### Sentry
| Endpoint | Description |
|---|---|
| `/test/error/` | Triggers a `ZeroDivisionError` |
| `/test/unhandled/` | Triggers an unhandled `ValueError` |
| `/test/capture/` | Manually captures exception via `sentry_sdk.capture_exception()` |
| `/test/message/` | Sends custom message via `sentry_sdk.capture_message()` |
| `/test/context/` | Error with custom context, tags, and user info |
| `/test/transaction/` | Performance transaction with spans |
| `/test/success/` | Successful endpoint for baseline testing |

### Honeycomb (OpenTelemetry)
| Endpoint | Description |
|---|---|
| `/test/honeycomb/trace/` | Custom trace with nested spans (DB + API + processing) |
| `/test/honeycomb/attributes/` | Trace with custom attributes, events, and status |
| `/test/honeycomb/error/` | Trace that records an exception |
| `/test/honeycomb/nested/` | Deeply nested spans for waterfall view testing |

Last updated Feb 13, 2026
