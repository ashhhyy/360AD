import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the deployment administrator from environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "admin").strip()
        email = os.environ.get("ADMIN_EMAIL", "").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not password:
            self.stdout.write(self.style.WARNING("ADMIN_PASSWORD is not set; administrator creation skipped."))
            return
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(username=username, defaults={"email": email})
        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Administrator '{username}' {action}."))
