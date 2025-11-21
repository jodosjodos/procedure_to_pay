from django.core.management.base import BaseCommand

from accounts.models import User


DEFAULT_USERS = [
    ("staff@company.com", "Staff User", User.Roles.STAFF),
    ("approver1@company.com", "Approver L1", User.Roles.APPROVER_L1),
    ("approver2@company.com", "Approver L2", User.Roles.APPROVER_L2),
    ("finance@company.com", "Finance User", User.Roles.FINANCE),
]


class Command(BaseCommand):
    help = "Seed demo users with known credentials for the ProcurePay frontend"

    def add_arguments(self, parser):
        parser.add_argument("--password", default="Password123!", help="Password to use for all demo users")

    def handle(self, *args, **options):
        password = options["password"]
        created = 0

        for email, name, role in DEFAULT_USERS:
            user, was_created = User.objects.get_or_create(
                email=email,
                defaults={"name": name, "role": role},
            )
            if was_created:
                self.stdout.write(self.style.SUCCESS(f"Created {email} ({role})"))
                created += 1
            else:
                self.stdout.write(f"{email} already exists, ensuring role is {role}")
                user.role = role
            user.set_password(password)
            user.save(update_fields=["password", "role", "name"])

        if not created:
            self.stdout.write(self.style.WARNING("No new users were created"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Seeded {created} users"))

