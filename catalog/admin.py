from django.contrib import admin

from .models import (
    Assignment,
    Course,
    Enrollment,
    Lesson,
    Submission,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "lecturer", "is_active")
    search_fields = ("code", "title")
    list_filter = ("is_active",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "order")
    search_fields = ("title", "course__title")
    list_filter = ("course",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "enrolled_at")
    search_fields = ("student__username", "course__title")
    list_filter = ("course",)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "deadline")
    search_fields = ("title", "course__title")
    list_filter = ("course",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assignment",
        "student",
        "submitted_at",
        "grade",
    )
    list_filter = ("submitted_at",)
    search_fields = (
        "student__username",
        "assignment__title",
    )
