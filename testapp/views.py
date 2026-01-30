from django.http import HttpResponse, JsonResponse
import sentry_sdk


def index(request):
    """Home page with links to test endpoints."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sentry Django Sandbox</title>
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
        <h1>Sentry Django Sandbox</h1>
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
            <a href="/test/success/">/test/success/</a>
            <div class="description">A successful endpoint (no errors) for baseline testing</div>
        </div>

        <hr style="margin: 30px 0;">
        <p><strong>Setup:</strong> Make sure to set your <code>SENTRY_DSN</code> environment variable!</p>
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


def success_endpoint(request):
    """A successful endpoint for baseline testing."""
    return JsonResponse({
        "status": "success",
        "message": "This endpoint works correctly!",
        "sentry_dsn_configured": bool(sentry_sdk.get_client().dsn)
    })
