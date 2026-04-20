# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

ROLE_CHOICES = (
    ("admin", "Admin"),
    ("regional_manager", "Regional Manager"),
    ("employee", "Employee"),
)

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Profile(models.Model):
    """
    Lightweight profile to store role. Created automatically via signals.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="employee")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class RegionalManager(models.Model):
    """
    Each RegionalManager is linked to a User. To avoid migration issues when adding this field
    to an existing table, the OneToOneField allows null=True, blank=True.
    Once all rows have an associated user, you can remove null=True to enforce the constraint.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regional_manager_profile"
    )
    manager_id = models.CharField(max_length=50, unique=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name="regional_managers")
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # if you prefer username as primary reference, keep user; else you can use manager_id

    class Meta:
        ordering = ["manager_id"]

    def __str__(self):
        user_part = self.user.username if self.user else "UnlinkedUser"
        region_part = self.region.name if self.region else "NoRegion"
        return f"{user_part} — {self.manager_id} ({region_part})"


class Employee(models.Model):
    """
    Employee linked to User and optionally assigned to a RegionalManager.
    `user` allows null so migrations won't fail when existing rows exist.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile"
    )
    employee_id = models.CharField(max_length=50, unique=True)
    regional_manager = models.ForeignKey(RegionalManager, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees")
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    joined_on = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee_id"]

    def __str__(self):
        user_part = self.user.username if self.user else "UnlinkedUser"
        rm_part = self.regional_manager.manager_id if self.regional_manager else "NoRM"
        return f"{user_part} — {self.employee_id} (RM: {rm_part})"


# Optional / Additional models useful for admin features you mentioned

class Camera(models.Model):
    """
    Represents a camera / device used for live detection or reporting.
    """
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=200, blank=True, null=True)
    rtsp_url = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — {self.location or 'Unknown'}"


class Attendance(models.Model):
    """
    Basic attendance record — can be extended to store face-embeddings / images if needed.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances")
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(blank=True, null=True)
    source = models.CharField(max_length=60, blank=True, null=True)  # e.g., "webcam", "manual", "mobile"
    camera = models.ForeignKey(Camera, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-check_in"]

    def duration_seconds(self):
        if self.check_out:
            return int((self.check_out - self.check_in).total_seconds())
        return None

    def __str__(self):
        return f"Attendance: {self.employee.employee_id} @ {self.check_in}"


class Alert(models.Model):
    """
    Alerts generated from live-detection or admin actions.
    """
    LEVEL_CHOICES = (("info", "Info"), ("warning", "Warning"), ("critical", "Critical"))

    title = models.CharField(max_length=200)
    message = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="info")
    camera = models.ForeignKey(Camera, on_delete=models.SET_NULL, null=True, blank=True)
    related_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="acknowledged_alerts")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.level.upper()}] {self.title}"


class Report(models.Model):
    """
    Simple report store — can be generated by admin (attendance summary, detection summary).
    """
    title = models.CharField(max_length=200)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField(blank=True, null=True)  # could store JSON or HTML
    file = models.FileField(upload_to="reports/", blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Report: {self.title} @ {self.generated_at:%Y-%m-%d %H:%M}"


class ActivityLog(models.Model):
    """
    Lightweight audit trail for admin actions.
    """
    ACTION_CHOICES = (
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("login", "Login"),
        ("logout", "Logout"),
        ("other", "Other"),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=120, blank=True, null=True)
    object_id = models.CharField(max_length=120, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        who = self.user.username if self.user else "System"
        return f"{who} — {self.action} — {self.object_type or 'N/A'}"


# End of models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Existing models: Employee, RegionalManager, Report, Alert

# New: ComplianceHistory
class ComplianceHistory(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name="compliance_history")
    date = models.DateField(default=timezone.now)
    helmet = models.BooleanField(default=False)
    mask = models.BooleanField(default=False)
    suit = models.BooleanField(default=False)
    id_card = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date}"

# Update Report to store summary JSON
class Report(models.Model):
    title = models.CharField(max_length=200)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField(blank=True, null=True)  # JSON summary
    file = models.FileField(upload_to="reports/", blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    period = models.CharField(max_length=50, default="daily")  # daily / weekly / monthly

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Report: {self.title} @ {self.generated_at:%Y-%m-%d %H:%M}"


    # models.py
# core/models.py
from django.db import models
from django.contrib.auth.models import User

class FaceRecognitionResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recognized_class = models.CharField(max_length=100)
    probability = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.recognized_class} ({self.probability:.2f})"
    

# ─────────────────────────────────────────────────────────────────────────────
# ADD THIS CLASS to your core/models.py
# Place it after the ComplianceHistory model
# Then run: python manage.py makemigrations && python manage.py migrate
# ─────────────────────────────────────────────────────────────────────────────

class SafetyViolation(models.Model):
    """
    Stores every live-detection frame result.
    - Linked to Employee via face recognition name
    - Saves violation image only when helmet or mask is missing
    - Admin sees these via admin_live_logs (through Report with period='live')
    """
    employee = models.ForeignKey(
        'Employee', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="safety_violations"
    )
    recognized_name = models.CharField(max_length=100, default="Unknown")
    helmet_status   = models.CharField(max_length=50)   # "Helmet worn" / "Helmet not worn"
    mask_status     = models.CharField(max_length=50)   # "Mask worn"   / "Mask not worn"
    image           = models.ImageField(upload_to="violations/", null=True, blank=True)
    timestamp       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def has_violation(self):
        return (
            self.helmet_status == "Helmet not worn" or
            self.mask_status   == "Mask not worn"
        )

    def __str__(self):
        return f"{self.recognized_name} — {self.timestamp:%Y-%m-%d %H:%M}"