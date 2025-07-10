from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UploadedFile, CustomerData, Task, ImportedFile

# Register CustomUser in Admin
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_admin", "is_marketer", "is_staff", "is_active")
    list_filter = ("is_admin", "is_marketer", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_admin", "is_marketer", "is_staff", "is_active", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    search_fields = ("username", "email")
    ordering = ("username",)

admin.site.register(CustomUser, CustomUserAdmin)

# Register Other Models
@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("file", "uploaded_at", "uploaded_by")

@admin.register(CustomerData)
class CustomerDataAdmin(admin.ModelAdmin):
    list_display = ('date', 'company_name', 'location', 'person_name', 'contact_no', 'email_id', 'remark')

# admin.site.register(CustomerData, CustomerDataAdmin)
# class CustomerDataAdmin(admin.ModelAdmin):
#     list_display = ("name", "email", "phone", "created_at")

# from django.contrib import admin
# from .models import CustomerData



@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "assigned_to", "due_date", "completed")
    list_filter = ("completed",)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile

# admin.site.register(CustomUser)
admin.site.register(Profile)

@admin.register(ImportedFile)
class ImportedFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'user', 'uploaded_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
