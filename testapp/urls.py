from django.urls import path
from . import views

urlpatterns = [
    path('error/', views.trigger_error, name='trigger_error'),
    path('unhandled/', views.unhandled_exception, name='unhandled_exception'),
    path('capture/', views.capture_exception, name='capture_exception'),
    path('message/', views.capture_message, name='capture_message'),
    path('context/', views.error_with_context, name='error_with_context'),
    path('transaction/', views.performance_transaction, name='performance_transaction'),
    path('success/', views.success_endpoint, name='success_endpoint'),
]
