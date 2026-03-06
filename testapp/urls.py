from django.urls import path
from . import views

urlpatterns = [
    # Sentry test endpoints
    path('error/', views.trigger_error, name='trigger_error'),
    path('unhandled/', views.unhandled_exception, name='unhandled_exception'),
    path('capture/', views.capture_exception, name='capture_exception'),
    path('message/', views.capture_message, name='capture_message'),
    path('context/', views.error_with_context, name='error_with_context'),
    path('transaction/', views.performance_transaction, name='performance_transaction'),
    path('issue/', views.create_issue, name='create_issue'),
    path('success/', views.success_endpoint, name='success_endpoint'),

    # Honeycomb / OpenTelemetry test endpoints
    path('honeycomb/trace/', views.honeycomb_trace, name='honeycomb_trace'),
    path('honeycomb/attributes/', views.honeycomb_attributes, name='honeycomb_attributes'),
    path('honeycomb/error/', views.honeycomb_error, name='honeycomb_error'),
    path('honeycomb/nested/', views.honeycomb_nested, name='honeycomb_nested'),
]
