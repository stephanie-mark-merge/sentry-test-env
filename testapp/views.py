import json
import logging
import os

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import requests
import sentry_sdk
from opentelemetry import trace

logger = logging.getLogger(__name__)

# OpenTelemetry tracer for Honeycomb custom spans
tracer = trace.get_tracer("sandbox-app")


def _flush_traces():
    """Force flush spans so they're sent to Honeycomb immediately."""
    provider = trace.get_tracer_provider()
    if hasattr(provider, 'force_flush'):
        provider.force_flush(timeout_millis=5000)


def index(request):
    """Home page with links to test endpoints."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Integration Test Sandbox</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #362d59; }
            .endpoint { margin: 15px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            a { color: #6c5ce7; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
            code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; }
            .description { color: #666; margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>Integration Test Sandbox</h1>

        <h2 style="color: #362d59;">Sentry Endpoints</h2>
        <p>Use these endpoints to test your Sentry integration:</p>

        <div class="endpoint">
            <a href="/test/error/">/test/error/</a>
            <div class="description">Triggers a basic <code>ZeroDivisionError</code></div>
        </div>

        <div class="endpoint">
            <a href="/test/unhandled/">/test/unhandled/</a>
            <div class="description">Triggers an unhandled <code>ValueError</code> exception</div>
        </div>

        <div class="endpoint">
            <a href="/test/capture/">/test/capture/</a>
            <div class="description">Manually captures an exception using <code>sentry_sdk.capture_exception()</code></div>
        </div>

        <div class="endpoint">
            <a href="/test/message/">/test/message/</a>
            <div class="description">Sends a custom message using <code>sentry_sdk.capture_message()</code></div>
        </div>

        <div class="endpoint">
            <a href="/test/context/">/test/context/</a>
            <div class="description">Error with custom context, tags, and user info</div>
        </div>

        <div class="endpoint">
            <a href="/test/transaction/">/test/transaction/</a>
            <div class="description">Creates a performance transaction with spans</div>
        </div>

        <div class="endpoint">
            <a href="/test/issue/">/test/issue/</a>
            <div class="description">Creates a Sentry issue via <code>capture_message()</code>. Params: <code>?title=...&level=error|warning|info</code></div>
        </div>

        <div class="endpoint">
            <a href="/test/success/">/test/success/</a>
            <div class="description">A successful endpoint (no errors) for baseline testing</div>
        </div>

        <h2 style="color: #f5a623;">Honeycomb Endpoints</h2>
        <p>Use these endpoints to test your Honeycomb integration (via OpenTelemetry):</p>
        <p><strong>Note:</strong> Run with <code>opentelemetry-instrument python manage.py runserver</code> to enable auto-instrumentation.</p>

        <div class="endpoint">
            <a href="/test/honeycomb/trace/">/test/honeycomb/trace/</a>
            <div class="description">Creates a custom trace with nested spans (simulates DB + API + processing)</div>
        </div>

        <div class="endpoint">
            <a href="/test/honeycomb/attributes/">/test/honeycomb/attributes/</a>
            <div class="description">Trace with custom attributes, events, and status codes</div>
        </div>

        <div class="endpoint">
            <a href="/test/honeycomb/error/">/test/honeycomb/error/</a>
            <div class="description">Trace that records an exception (visible in Honeycomb as an error span)</div>
        </div>

        <div class="endpoint">
            <a href="/test/honeycomb/nested/">/test/honeycomb/nested/</a>
            <div class="description">Deeply nested spans to test Honeycomb's trace waterfall view</div>
        </div>

        <hr style="margin: 30px 0;">
        <p><strong>Setup:</strong> Set <code>SENTRY_DSN</code> for Sentry and <code>OTEL_EXPORTER_OTLP_HEADERS</code> for Honeycomb. See <code>.env.example</code>.</p>
    </body>
    </html>
    """
    return HttpResponse(html)


def trigger_error(request):
    """Trigger a basic division by zero error."""
    division_by_zero = 1 / 0
    return HttpResponse("This will never be reached")


def unhandled_exception(request):
    """Trigger an unhandled ValueError."""
    raise ValueError("This is an unhandled test exception from Django sandbox!")


def capture_exception(request):
    """Manually capture an exception."""
    try:
        raise RuntimeError("This is a manually captured exception")
    except Exception as e:
        sentry_sdk.capture_exception(e)
    return JsonResponse({"status": "Exception captured and sent to Sentry"})


def capture_message(request):
    """Send a custom message to Sentry."""
    sentry_sdk.capture_message("Test message from Django sandbox!", level="info")
    return JsonResponse({"status": "Message sent to Sentry"})


def error_with_context(request):
    """Error with custom context, tags, and user info."""
    # Set user context
    sentry_sdk.set_user({
        "id": "test-user-123",
        "email": "test@example.com",
        "username": "sandbox_tester"
    })

    # Set custom tags
    sentry_sdk.set_tag("test_type", "context_test")
    sentry_sdk.set_tag("sandbox", "true")

    # Set extra context
    sentry_sdk.set_context("test_data", {
        "request_id": "abc-123-xyz",
        "feature_flags": ["new_ui", "beta_api"],
        "user_preferences": {
            "theme": "dark",
            "notifications": True
        }
    })

    # Add breadcrumb
    sentry_sdk.add_breadcrumb(
        category="test",
        message="About to trigger test error with context",
        level="info"
    )

    raise Exception("Test error with rich context!")


def performance_transaction(request):
    """Create a performance transaction with spans."""
    import time

    with sentry_sdk.start_transaction(op="test", name="sandbox-performance-test") as transaction:
        # Simulate database operation
        with sentry_sdk.start_span(op="db", name="fetch_user_data"):
            time.sleep(0.1)  # Simulate DB latency

        # Simulate API call
        with sentry_sdk.start_span(op="http", name="external_api_call"):
            time.sleep(0.2)  # Simulate API latency

        # Simulate data processing
        with sentry_sdk.start_span(op="process", name="data_processing"):
            time.sleep(0.05)  # Simulate processing

    return JsonResponse({
        "status": "Performance transaction completed",
        "transaction_id": str(transaction.trace_id)
    })


def create_issue(request):
    """Create a Sentry issue via capture_message with configurable level and details."""
    title = request.GET.get("title", "Test issue from Django sandbox")
    level = request.GET.get("level", "error")  # debug, info, warning, error, fatal

    with sentry_sdk.push_scope() as scope:
        scope.set_tag("source", "manual_issue")
        scope.set_tag("issue.type", "custom")
        scope.set_context("issue_details", {
            "created_by": "sandbox_endpoint",
            "title": title,
            "level": level,
        })
        event_id = sentry_sdk.capture_message(title, level=level)

    return JsonResponse({
        "status": "Issue sent to Sentry",
        "event_id": str(event_id),
        "title": title,
        "level": level,
    })


def success_endpoint(request):
    """A successful endpoint for baseline testing."""
    return JsonResponse({
        "status": "success",
        "message": "This endpoint works correctly!",
        "sentry_dsn_configured": bool(sentry_sdk.get_client().dsn)
    })


# ---- Honeycomb / OpenTelemetry Test Endpoints ----

def honeycomb_trace(request):
    """Create a custom trace with nested spans for Honeycomb."""
    import time

    with tracer.start_as_current_span("sandbox-trace-test") as span:
        span.set_attribute("test.type", "trace")
        span.set_attribute("sandbox", True)

        # Simulate database operation
        with tracer.start_as_current_span("db.query") as db_span:
            db_span.set_attribute("db.system", "sqlite")
            db_span.set_attribute("db.statement", "SELECT * FROM users WHERE active = true")
            time.sleep(0.1)

        # Simulate external API call
        with tracer.start_as_current_span("http.request") as http_span:
            http_span.set_attribute("http.method", "GET")
            http_span.set_attribute("http.url", "https://api.example.com/data")
            http_span.set_attribute("http.status_code", 200)
            time.sleep(0.2)

        # Simulate data processing
        with tracer.start_as_current_span("process.data") as proc_span:
            proc_span.set_attribute("records.count", 42)
            time.sleep(0.05)

    _flush_traces()
    return JsonResponse({
        "status": "Trace sent to Honeycomb",
        "trace_id": format(span.get_span_context().trace_id, '032x'),
    })


def honeycomb_attributes(request):
    """Trace with custom attributes, events, and status."""
    with tracer.start_as_current_span("sandbox-attributes-test") as span:
        # Set various attribute types
        span.set_attribute("user.id", "test-user-123")
        span.set_attribute("user.email", "test@example.com")
        span.set_attribute("feature.flags", ["new_ui", "beta_api"])
        span.set_attribute("request.priority", 1)
        span.set_attribute("request.is_authenticated", True)

        # Add span events (like breadcrumbs/logs within the span)
        span.add_event("cache.miss", {"cache.key": "user:123"})
        span.add_event("validation.passed", {"fields": 5})

        # Set status to OK
        span.set_status(trace.StatusCode.OK, "All checks passed")

    _flush_traces()
    return JsonResponse({
        "status": "Trace with attributes sent to Honeycomb",
        "trace_id": format(span.get_span_context().trace_id, '032x'),
    })


def honeycomb_error(request):
    """Trace that records an exception for Honeycomb."""
    with tracer.start_as_current_span("sandbox-error-test") as span:
        span.set_attribute("test.type", "error")
        try:
            # Intentional error
            result = 1 / 0
        except Exception as e:
            span.set_status(trace.StatusCode.ERROR, str(e))
            span.record_exception(e)

    _flush_traces()
    return JsonResponse({
        "status": "Error trace sent to Honeycomb",
        "trace_id": format(span.get_span_context().trace_id, '032x'),
    })


def honeycomb_nested(request):
    """Deeply nested spans to test Honeycomb's trace waterfall."""
    import time

    with tracer.start_as_current_span("request.handler") as root:
        root.set_attribute("handler", "honeycomb_nested")

        with tracer.start_as_current_span("auth.check"):
            time.sleep(0.02)

            with tracer.start_as_current_span("auth.token_validate"):
                time.sleep(0.01)

        with tracer.start_as_current_span("business.logic"):
            time.sleep(0.03)

            with tracer.start_as_current_span("db.read"):
                time.sleep(0.05)

                with tracer.start_as_current_span("db.deserialize"):
                    time.sleep(0.01)

            with tracer.start_as_current_span("transform.data"):
                time.sleep(0.02)

        with tracer.start_as_current_span("response.serialize"):
            time.sleep(0.01)

    _flush_traces()
    return JsonResponse({
        "status": "Nested trace sent to Honeycomb",
        "trace_id": format(root.get_span_context().trace_id, '032x'),
    })


# ---- Sentry → PagerDuty Webhook Relay ----

PAGERDUTY_EVENTS_URL = "https://events.pagerduty.com/v2/enqueue"


@csrf_exempt
@require_POST
def sentry_to_pagerduty(request):
    """Receive a Sentry webhook and forward it to PagerDuty Events API v2."""
    routing_key = os.environ.get("PAGERDUTY_ROUTING_KEY", "")
    if not routing_key:
        return JsonResponse({"error": "PAGERDUTY_ROUTING_KEY not configured"}, status=500)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    action = payload.get("action")
    data = payload.get("data", {})

    # Sentry sends different resource types (issue, error, comment, etc.)
    # For issues: action can be "created", "resolved", "archived", etc.
    issue = data.get("issue", data)

    title = issue.get("title", "Sentry Alert")
    culprit = issue.get("culprit", "")
    issue_url = issue.get("url", "")
    project = issue.get("project", {}).get("name", "unknown")
    level = issue.get("level", "error")

    # Map Sentry actions to PagerDuty event actions
    if action == "resolved":
        pd_event_action = "resolve"
    elif action == "archived":
        pd_event_action = "resolve"
    else:
        pd_event_action = "trigger"

    # Map Sentry levels to PagerDuty severity
    severity_map = {
        "fatal": "critical",
        "error": "error",
        "warning": "warning",
        "info": "info",
        "debug": "info",
    }
    severity = severity_map.get(level, "error")

    # Build a stable dedup key so PagerDuty groups updates to the same issue
    dedup_key = f"sentry-{issue.get('id', title)}"

    pd_payload = {
        "routing_key": routing_key,
        "event_action": pd_event_action,
        "dedup_key": dedup_key,
        "payload": {
            "summary": f"[{project}] {title}",
            "source": project,
            "severity": severity,
            "custom_details": {
                "culprit": culprit,
                "issue_url": issue_url,
                "level": level,
                "action": action,
            },
        },
    }

    if issue_url:
        pd_payload["links"] = [{"href": issue_url, "text": "View in Sentry"}]

    resp = requests.post(PAGERDUTY_EVENTS_URL, json=pd_payload, timeout=10)

    logger.info(
        "Forwarded Sentry webhook to PagerDuty: action=%s status=%s dedup_key=%s",
        action, resp.status_code, dedup_key,
    )

    return JsonResponse({
        "status": "forwarded",
        "pagerduty_status": resp.status_code,
        "pagerduty_response": resp.json() if resp.ok else resp.text,
        "dedup_key": dedup_key,
    })
