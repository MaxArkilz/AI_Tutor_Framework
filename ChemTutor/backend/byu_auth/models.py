from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
# Create your models here.

class NewUser(AbstractUser):
    username = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.CharField(max_length=128, null=True, blank=True)

    #permissions
    is_inspector = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    

def create_user(user_info):
    groups = user_info.get("groups", [])
    
    user = NewUser()
    user.username = user_info["net_id"]
    user.first_name = user_info["first_name"]
    user.last_name = user_info["last_name"]
    user.email = user_info["email"]
    
    # Set permssions using gro groups
    user.is_staff = bool(settings.FACULTY_GROUPS.intersection(groups))
    user.is_superuser = bool(settings.ADMIN_GROUPS.intersection(groups))
    user.is_inspector = bool(settings.INSPECTOR_GROUPS.intersection(groups))

    # Set mandatory Django attributes
    user.set_unusable_password()  # Makes it so users can't log in without going through OKTA or CAS
    user.is_active = True # Django checks this to see if it is allowed to log in a user

    user.save()
    return user