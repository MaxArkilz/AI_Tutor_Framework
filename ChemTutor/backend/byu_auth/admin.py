from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import NewUser

if not NewUser._meta.swapped:
    admin.site.register(NewUser, UserAdmin)
