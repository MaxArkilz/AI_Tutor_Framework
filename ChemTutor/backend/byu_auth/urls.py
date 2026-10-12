from django.urls import path
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from . import views

if settings.AUTH_TYPE=='OKTA':
    urlpatterns = [
        path('admin/', admin.site.urls),
        path("login", views.login, name="login"),
        path("callback", views.callback, name="callback"),
        path("logout", views.logout, name="logout"),
        path("logout/callback", views.logout_callback, name="logout_callback"),        
    ]
else:
    urlpatterns = [
        path('login_page/', views.logging_in, name = 'login_page'),
        path('login', views.to_login, name = 'login'),
        path('logout', LogoutView.as_view(next_page= settings.LOGOUT_ENDPOINT), name='logout')
        
    ]