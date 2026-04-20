# views.py (organized)

import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.utils import timezone

from ultralytics import YOLO

from .models import Profile, Region, RegionalManager, Employee, Report, Alert, ComplianceHistory
from .forms import LoginForm, RegionForm, CreateRMForm, EditRMForm, CreateEmployeeForm
from .decorators import role_required


# -------------------------
# YOLO Models (global)
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cons_model = YOLO(os.path.join(BASE_DIR, 'cons.pt'))
id_model = YOLO(os.path.join(BASE_DIR, 'id.pt'))


# -------------------------
# Common Views
# -------------------------
def home(request):
    return render(request, "home.html")


from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Redirect based on role
            profile = getattr(user, 'profile', None)
            if profile:
                if profile.role == 'admin':
                    return redirect('admin_panel')
                elif profile.role == 'regional_manager':
                    return redirect('rm_dashboard')
                elif profile.role == 'employee':
                    return redirect('employee_dashboard')
            # fallback
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect('home')


# =========================
# Admin Views
# =========================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Region, RegionalManager

@login_required
def admin_panel(request):
    # Example counts
    total_rms = RegionalManager.objects.count()
    total_employees = sum(rm.employees.count() for rm in RegionalManager.objects.all())
    region_data = Region.objects.all()

    # Prepare labels for chart (if needed)
    region_labels = [r.name for r in region_data]
    rms_counts = [RegionalManager.objects.filter(region=r).count() for r in region_data]

    return render(request, "admin_panel.html", {
        "total_rms": total_rms,
        "total_employees": total_employees,
        "region_data": region_data,
        "region_labels": region_labels,
        "rms_counts": rms_counts,
    })
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Region, RegionalManager, Employee

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Region, RegionalManager, Employee

@login_required
def admin_dashboard(request):
    # Summary counts
    total_rms = RegionalManager.objects.count()
    total_employees = Employee.objects.count()
    total_regions = Region.objects.count()

    # Example: ongoing projects (replace with actual logic)
    ongoing_projects = [
        {"name": "Project Alpha", "progress": 70},
        {"name": "Project Beta", "progress": 40},
    ]
    outline_projects = [
        {"name": "Project Gamma", "progress": 20},
        {"name": "Project Delta", "progress": 90},
    ]

    # Calculate total ongoing projects
    total_ongoing_projects = len(ongoing_projects)

    # Graph data: regional growth
    region_labels = [r.name for r in Region.objects.all()]
    rms_counts = [RegionalManager.objects.filter(region=r).count() for r in Region.objects.all()]

    return render(request, "admin_dashboard.html", {
        "total_rms": total_rms,
        "total_employees": total_employees,
        "total_regions": total_regions,
        "ongoing_projects": ongoing_projects,
        "outline_projects": outline_projects,
        "total_ongoing_projects": total_ongoing_projects,  # Pass total count
        "region_labels": region_labels,
        "rms_counts": rms_counts,
    })


@login_required
@role_required('admin')
def create_region(request):
    if request.method == "POST":
        form = RegionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_panel')
    else:
        form = RegionForm()
    return render(request, "create_region.html", {"form": form})


@login_required
@role_required('admin')
def list_regions(request):
    regions = Region.objects.all()
    return render(request, "list_regions.html", {"regions": regions})


@login_required
@role_required('admin')
def list_rms(request):
    rms = RegionalManager.objects.select_related('user', 'region').all()
    return render(request, "list_rms.html", {"rms": rms})


from django.contrib.auth.models import User
from core.models import RegionalManager, Profile

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Profile, RegionalManager, Region

@login_required
@role_required('admin')
@transaction.atomic
def create_rm(request):
    error = None
    regions = Region.objects.all()

    if request.method == "POST":
        region_id = request.POST.get("region")
        manager_id = request.POST.get("manager_id")
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            error = "Username already exists"
        else:
            # Create User
            user = User.objects.create_user(
                username=username,
                password=password
            )

            # Set role to regional_manager
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = "regional_manager"
            profile.save()

            # Create Regional Manager
            RegionalManager.objects.create(
                user=user,
                manager_id=manager_id,
                region_id=region_id if region_id else None
            )

            return redirect("list_rms")

    return render(request, "create_rm.html", {
        "regions": regions,
        "error": error,
        "username": request.POST.get("username", ""),
        "manager_id": request.POST.get("manager_id", ""),
        "region_selected": request.POST.get("region", "")
    })

@login_required
@role_required('admin')
@transaction.atomic
def edit_rm(request, rm_id):
    rm = get_object_or_404(RegionalManager, id=rm_id)
    if request.method == "POST":
        form = EditRMForm(request.POST)
        form.fields['region'].queryset = Region.objects.all()
        if form.is_valid():
            rm.manager_id = form.cleaned_data['manager_id']
            rm.region = form.cleaned_data['region']
            rm.user.username = form.cleaned_data['username']
            rm.user.save()
            rm.save()
            return redirect('list_rms')
    else:
        form = EditRMForm(initial={
            "region": rm.region,
            "manager_id": rm.manager_id,
            "username": rm.user.username
        })
        form.fields['region'].queryset = Region.objects.all()
    return render(request, "edit_rm.html", {"form": form, "rm": rm})


@login_required
@role_required('admin')
@transaction.atomic
def delete_rm(request, rm_id):
    rm = get_object_or_404(RegionalManager, id=rm_id)
    user = rm.user
    rm.delete()
    if user:
        user.delete()
    return redirect('list_rms')


@login_required
@role_required('admin')
@transaction.atomic
def create_employee(request):
    if request.method == "POST":
        form = CreateEmployeeForm(request.POST)
        form.fields['regional_manager'].queryset = RegionalManager.objects.all()

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            employee_id = form.cleaned_data['employee_id']
            rm = form.cleaned_data['regional_manager']

            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Username already exists.')
                return render(request, "create_employee.html", {"form": form})

            user = User.objects.create_user(username=username, password=password)

            # Create Profile safely
            Profile.objects.get_or_create(user=user, defaults={'role': 'employee'})

            Employee.objects.create(user=user, employee_id=employee_id, regional_manager=rm)

            return redirect('admin_panel')
    else:
        form = CreateEmployeeForm()
        form.fields['regional_manager'].queryset = RegionalManager.objects.all()

    return render(request, "create_employee.html", {"form": form})


@login_required
@role_required('admin')
def analytics_data(request):
    regions = list(Region.objects.values_list('name', flat=True))
    rm_counts = [RegionalManager.objects.filter(region=r).count() for r in Region.objects.all()]
    return JsonResponse({"regions": regions, "rm_counts": rm_counts})


@login_required
@role_required('admin')
def admin_compliance_overview(request):
    regions = RegionalManager.objects.values_list("region__name", flat=True).distinct()
    data = []

    for region_name in regions:
        rms = RegionalManager.objects.filter(region__name=region_name)
        region_employees = [e for rm in rms for e in rm.employees.all()]
        total = len(region_employees) or 1
        helmet_avg = sum(sum(h.helmet for h in e.compliance_history.all()) for e in region_employees) * 100 / total
        mask_avg = sum(sum(h.mask for h in e.compliance_history.all()) for e in region_employees) * 100 / total
        data.append({
            "region": region_name,
            "helmet_avg": int(helmet_avg),
            "mask_avg": int(mask_avg)
        })

    return render(request, "admin_compliance_overview.html", {"data": data})
@login_required
@role_required('admin')
def list_employees(request):
    employees = Employee.objects.select_related('user', 'regional_manager').all()
    return render(request, "list_employees.html", {"employees": employees})

@login_required
@role_required("admin")
def admin_live_logs(request):
    records = SafetyViolation.objects.all().order_by("-timestamp")
    return render(request, "admin_live_logs.html", {"records": records})

@login_required
@role_required('admin')
def face_recognition_admin(request):
   pass
# =========================
# Regional Manager Views
# =========================
from django.db.models import Count
from django.utils import timezone
import random

@login_required
@role_required('regional_manager')
def rm_dashboard(request):
    rm = get_object_or_404(RegionalManager, user=request.user)
    employees = Employee.objects.filter(regional_manager=rm)

    context = {
        "rm": rm,
        "kpi": {
            "employees": employees.count(),
            "projects": 5,
            "avg_compliance": 84,
            "alerts": 3,
        },
        "projects": [
            {"name": "Site A Safety Upgrade", "progress": 70},
            {"name": "Factory B PPE Rollout", "progress": 45},
            {"name": "Warehouse C Audit", "progress": 90},
        ],
        "profit_loss": [120, 150, 90, 180, 140, 200],
        "employee_progress": [60, 80, 70, 90, 50],
    }
    return render(request, "rm_dashboard.html", context)

@login_required
@role_required('regional_manager')
def rm_compliance_dashboard(request):
    rm = RegionalManager.objects.get(user=request.user)
    employees = rm.employees.all()
    summary = []

    for emp in employees:
        total = emp.compliance_history.count() or 1
        helmet = sum(h.helmet for h in emp.compliance_history.all()) * 100 / total
        mask = sum(h.mask for h in emp.compliance_history.all()) * 100 / total
        suit = sum(h.suit for h in emp.compliance_history.all()) * 100 / total
        id_card = sum(h.id_card for h in emp.compliance_history.all()) * 100 / total

        def badge_cls(val):
            if val >= 80: return "good"
            elif val >= 50: return "avg"
            else: return "low"

        summary.append({
            "employee": emp,
            "helmet": round(helmet,1),
            "mask": round(mask,1),
            "suit": round(suit,1),
            "id_card": round(id_card,1),
            "helmet_cls": badge_cls(helmet),
            "mask_cls": badge_cls(mask),
            "suit_cls": badge_cls(suit),
            "id_card_cls": badge_cls(id_card)
        })

    alerts_qs = Alert.objects.filter(related_employee__in=employees, acknowledged=False)
    alerts = []
    for a in alerts_qs:
        if a.level == "critical":
            cls = "low"
        elif a.level == "warning":
            cls = "avg"
        else:
            cls = "good"
        alerts.append({"title": a.title, "level": a.level, "cls": cls})

    return render(request, "rm_compliance_dashboard.html", {
        "rm": rm,
        "summary": summary,
        "alerts": alerts
    })


# views.py (Employee section)
@login_required
@role_required('employee')
def employee_dashboard(request):
    """Dashboard showing available compliance tasks"""
    tasks = [
        {"name": "Helmet Detection", "icon": "😷"},
        {"name": "Mask Detection", "icon": "😷"},
        {"name": "ID Card Verification", "icon": "🪪"},
        {"name": "Person Recognition", "icon": "👤"}
    ]
    return render(request, "employee_dashboard.html", {"tasks": tasks})



@login_required
@role_required('employee')
def employee_compliance_dashboard(request):
    """View personal compliance history and stats"""
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return HttpResponse("Employee profile not found.")

    history = employee.compliance_history.all()
    total_entries = history.count() or 1

    compliance = {
        "Helmet": int(sum(h.helmet for h in history) * 100 / total_entries),
        "Mask": int(sum(h.mask for h in history) * 100 / total_entries),
        "Suit": int(sum(h.suit for h in history) * 100 / total_entries),
        "ID Card": int(sum(h.id_card for h in history) * 100 / total_entries),
    }

    return render(request, "employee_compliance_dashboard.html", {
        "history": history,
        "compliance": compliance
    })


@login_required
@role_required('employee')
@transaction.atomic
def record_compliance(request):
    """Record a compliance entry manually"""
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return HttpResponse("Employee profile not found.")

    if request.method == "POST":
        helmet = int(request.POST.get("helmet", 0))
        mask = int(request.POST.get("mask", 0))
        suit = int(request.POST.get("suit", 0))
        id_card = int(request.POST.get("id_card", 0))

        ComplianceHistory.objects.create(
            employee=employee,
            helmet=helmet,
            mask=mask,
            suit=suit,
            id_card=id_card
        )
        return redirect("employee_compliance_dashboard")

    return render(request, "record_compliance.html")



# =========================
# Live Detection View
# =========================
# =========================
# Live Detection View (2 Second Live Mode)
# =========================
# =========================
# Live Detection View (2 Second Live Mode + Full Logging)
# =========================

@login_required
def face_recognition_dashboard(request):
    """
    Renders the face recognition page with webcam and Teachable Machine model
    """
    return render(request, "face_recognition.html")


@login_required
def store_face_recognition(request):
    """
    Receives AJAX POST from frontend with recognized class and probability.
    Stores it only if probability >= 0.8 (80%).
    """
    if request.method == "POST":
        user = request.user
        data = request.POST
        recognized_class = data.get("recognized_class")
        probability = float(data.get("probability", 0))

        if probability >= 0.8:  # Only store high-confidence predictions
            FaceRecognitionResult.objects.create(
                user=user,
                recognized_class=recognized_class,
                probability=probability
            )
            return JsonResponse({"status": "stored"})
        else:
            return JsonResponse({"status": "ignored, low probability"})
    
    return JsonResponse({"status": "invalid request"}, status=400)


import base64, uuid, cv2, numpy as np
from django.core.files.base import ContentFile
from .models import SafetyViolation, Report, Employee


# ─── YOLO already loaded at top of your views.py ────────────────────────────
# cons_model = YOLO(os.path.join(BASE_DIR, "cons.pt"))
# id_model   = YOLO(os.path.join(BASE_DIR, "id.pt"))


# ─────────────────────────────────────────────────────────────────────────────
# 1. live_detection  (was: pass)
#    URL: /live-detection/
#    Role: employee
#    Flow: Face recognised on frontend (Teachable Machine) → name sent with
#          webcam frame → YOLO checks helmet + mask → saves SafetyViolation
#          + creates a live Report entry visible in admin_live_logs
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@role_required("employee")
def live_detection(request):

    if request.method == "POST":

        image_data = request.POST.get("image")
        name = request.POST.get("name", "Unknown")

        # Decode image from browser
        format, imgstr = image_data.split(';base64,')
        img_bytes = base64.b64decode(imgstr)

        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = cons_model(img)

        helmet = "Helmet not worn"
        mask = "Mask not worn"

        # YOLO detection
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = r.names[cls].lower()

                if label == "hardhat":
                    helmet = "Helmet worn"

                if label == "mask":
                    mask = "Mask worn"

        image_file = None

        # Save image if violation
        if helmet == "Helmet not worn" or mask == "Mask not worn":
            file_name = str(uuid.uuid4()) + ".jpg"
            _, buffer = cv2.imencode(".jpg", img)
            image_file = ContentFile(buffer.tobytes(), name=file_name)

        # Link to Employee if possible
        employee = None
        try:
            linked_user = User.objects.get(username=name)
            employee = linked_user.employee_profile
        except Exception:
            pass

        # Save record
        SafetyViolation.objects.create(
            employee=employee,
            recognized_name=name,
            helmet_status=helmet,
            mask_status=mask,
            image=image_file
        )

        result = [name, helmet, mask]

        return JsonResponse({"result": result})

    return render(request, "live_detection.html")


# ─────────────────────────────────────────────────────────────────────────────
# 2. upload_compliance_image  (was: fake_detection placeholder)
#    URL: /employee/upload/
#    Role: employee
#    Flow: Employee selects task + uploads image → real YOLO runs → result shown
# ─────────────────────────────────────────────────────────────────────────────
@login_required
@role_required("employee")
def upload_compliance_image(request):
    """
    Replaces fake_detection() with real YOLO inference.
    - Helmet / Mask  → cons_model  (cons.pt)
    - ID Card        → id_model    (id.pt)
    - Person         → cons_model  (person class in COCO)
    Also saves a ComplianceHistory entry for the employee.
    """
    tasks = [
        {"name": "Helmet Detection",     "icon": "⛑️"},
        {"name": "Mask Detection",       "icon": "😷"},
        {"name": "ID Card Verification", "icon": "🪪"},
        {"name": "Person Recognition",   "icon": "👤"},
    ]

    result        = None
    selected_task = None

    if request.method == "POST":
        selected_task = request.POST.get("task")
        image_file    = request.FILES.get("image")

        if selected_task and image_file:
            # ── Read uploaded image into OpenCV ──────────────────────────────
            img_bytes = image_file.read()
            nparr     = np.frombuffer(img_bytes, np.uint8)
            img       = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # ── Run correct model based on task ──────────────────────────────
            detected   = False
            detail_msg = ""

            if selected_task in ("Helmet Detection", "Mask Detection"):
                yolo_results = cons_model(img)
                target_label = "hardhat" if selected_task == "Helmet Detection" else "mask"

                for r in yolo_results:
                    for box in r.boxes:
                        cls   = int(box.cls[0])
                        label = r.names[cls].lower()
                        if label == target_label:
                            detected   = True
                            conf       = float(box.conf[0]) * 100
                            detail_msg = f"{label} ({conf:.1f}% confidence)"
                            break

            elif selected_task == "ID Card Verification":
                yolo_results = id_model(img)
                for r in yolo_results:
                    for box in r.boxes:
                        cls   = int(box.cls[0])
                        label = r.names[cls].lower()
                        if "id" in label or "card" in label:
                            detected   = True
                            conf       = float(box.conf[0]) * 100
                            detail_msg = f"{label} ({conf:.1f}% confidence)"
                            break

            elif selected_task == "Person Recognition":
                yolo_results = cons_model(img)
                for r in yolo_results:
                    for box in r.boxes:
                        cls   = int(box.cls[0])
                        label = r.names[cls].lower()
                        if "person" in label or "worker" in label:
                            detected   = True
                            conf       = float(box.conf[0]) * 100
                            detail_msg = f"{label} ({conf:.1f}% confidence)"
                            break

            result = {
                "task":       selected_task,
                "status":     "Detected ✅" if detected else "Not Detected ❌",
                "detail":     detail_msg,
                "detected":   detected,
            }

            # ── Save ComplianceHistory entry for this employee ────────────────
            try:
                employee = request.user.employee_profile
                ComplianceHistory.objects.create(
                    employee = employee,
                    helmet   = (selected_task == "Helmet Detection"     and detected),
                    mask     = (selected_task == "Mask Detection"       and detected),
                    id_card  = (selected_task == "ID Card Verification" and detected),
                    # suit stays False — no suit model yet
                )
            except Exception:
                pass   # employee profile missing — skip silently

    return render(request, "upload_compliance.html", {
        "tasks":         tasks,
        "result":        result,
        "selected_task": selected_task,
    })
