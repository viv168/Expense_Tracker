from django.contrib import admin
from django.urls import path
from .views import RegistrationView,VerifivationView, UsernameValidationView, EmailValidationView, LoginView, LogoutView, RequestPasswordResetEmail, CompletePasswordReset
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('register', RegistrationView.as_view(), name='register'),
    path('validate-username', csrf_exempt(UsernameValidationView.as_view()), name='validate-username'),
    path('validate-email', csrf_exempt(EmailValidationView.as_view()), name='validate-email'),
    path('activate/<uid>/<token>', VerifivationView.as_view(), name='activate'),
    path('request-reset-link', RequestPasswordResetEmail.as_view(), name='request-password'),
    path('set-new-password/<uid>/<token>', CompletePasswordReset.as_view(), name='reset-user-password'),
]