from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, Group, Permission, User
from django.db.models import Q

# Create your models here.


# User Model with Roles
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    is_admin = models.BooleanField(default=False)
    is_marketer = models.BooleanField(default=True)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_groups",  # Fixes clash with auth.User.groups
        blank=True
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions",  # Fixes clash with auth.User.user_permissions
        blank=True
    )

# File Upload Model
class UploadedFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

class CustomerData(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default="Unknown")  # Default value
    person_name = models.CharField(max_length=255, default="Anonymous")  # Default value
    contact_no = models.CharField(max_length=20, default="0000000000")  # Default value
    # email_id = models.EmailField(null=True, default="noemail@example.com")  # Default value
    email_id = models.EmailField(null=True, blank=True, default=None)
    remark = models.TextField(blank=True, null=True)

    def clean(self):
        # Validate email format if not using default
        if self.email_id != 'noemail@example.com':
            from django.core.validators import validate_email
            validate_email(self.email_id)

        # Validate contact number if not using default
        if self.contact_no != '0000000000':
            if not self.contact_no.isdigit():
                raise ValidationError({'contact_no': 'Contact number should contain only digits'})


    def __str__(self):
        return f"{self.company_name} - {self.person_name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'email_id'],
                name='unique_email_per_user',
                condition=Q(email_id__isnull=False)
            )
        ]

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(fields=['user', 'email_id'], name='unique_email_per_user')
    #     ]

# Task Management Model
class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    due_date = models.DateField()
    completed = models.BooleanField(default=False)


from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='profile_pics/', default='default.jpg')
    #user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    #image = models.ImageField(upload_to='profile_pics/', default='default.jpg', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'


class VisitorCounter(models.Model):
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Total Visitors: {self.count}"




from django.db import models
from django.contrib.postgres.fields import JSONField  # For PostgreSQL
# For SQLite, use:
from django.db.models import JSONField
from django.conf import settings
class ImportedFile(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_columns = JSONField()  # Stores the column names from the Excel
    file_type = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    @property
    def record_count(self):
        return self.dynamicdata.count()

class DynamicData(models.Model):
    # source_file = models.ForeignKey(ImportedFile, on_delete=models.CASCADE)
    source_file = models.ForeignKey(ImportedFile, on_delete=models.CASCADE, related_name='dynamicdata')
    row_data = JSONField()  # Stores all data from the Excel row
    created_at = models.DateTimeField(auto_now_add=True)