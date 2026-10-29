from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "role",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )
    search_fields = (
        "username",
        "email",
    )
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Informasi LMS",
            {
                "fields": ("role",),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Informasi LMS",
            {
                "fields": ("role",),
            },
        ),
    )
