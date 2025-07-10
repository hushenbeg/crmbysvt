from django.db import migrations
from django.conf import settings  # Import settings to get AUTH_USER_MODEL

def assign_default_user(apps, schema_editor):
    """
    Assigns all NULL user records to an admin user or creates a fallback user.
    """
    ImportedFile = apps.get_model('crm', 'ImportedFile')
    CustomUser = apps.get_model(settings.AUTH_USER_MODEL.split('.')[0], settings.AUTH_USER_MODEL.split('.')[1])  # Get custom user model
    
    # Try to find an admin user
    default_user = CustomUser.objects.filter(is_superuser=True).first() or \
                  CustomUser.objects.filter(is_active=True).first()
    
    # Create a fallback user if none exists
    if not default_user:
        default_user = CustomUser.objects.create(
            username='legacy_files_user',
            is_active=False,
            is_staff=False,
            is_superuser=False
        )
        print(f"Created fallback user: {default_user.username}")

    # Assign files to the selected user
    updated_count = ImportedFile.objects.filter(user__isnull=True).update(user=default_user)
    print(f"Assigned {updated_count} files to user: {default_user.username}")

def reverse_assignment(apps, schema_editor):
    """Reverse migration: Set user=NULL for all files."""
    ImportedFile = apps.get_model('crm', 'ImportedFile')
    ImportedFile.objects.filter(user__isnull=False).update(user=None)

class Migration(migrations.Migration):
    dependencies = [
        ('crm', '0004_importedfile_user'),  # Previous migration
    ]

    operations = [
        migrations.RunPython(assign_default_user, reverse_code=reverse_assignment),
    ]