from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import signals and attempt to create a default admin user if none exists.
        # This is safe to run; during migrations DB access might fail so we wrap exceptions.
        try:
            import core.signals  # register signals
            from django.contrib.auth.models import User
            from django.db.utils import OperationalError, ProgrammingError
            from .models import Profile
            # Create default admin only if no user with role admin exists
            if not User.objects.filter(is_superuser=False, username="admin").exists():
                # try to find any Profile with role admin
                admin_profile_exists = Profile.objects.filter(role="admin").exists()
                if not admin_profile_exists and not User.objects.filter(username="admin").exists():
                    u = User.objects.create_user(username="admin", password="admin123")
                    Profile.objects.filter(user=u).update(role='admin')  # ensure role set
                    # If profile object didn't exist yet, create it
                    if not hasattr(u, 'profile'):
                        Profile.objects.create(user=u, role='admin')
                    print("Default admin created -> username: admin password: admin123")
        except (OperationalError, ProgrammingError, Exception):
            # DB isn't ready yet (migrations running) — skip quietly.
            pass
