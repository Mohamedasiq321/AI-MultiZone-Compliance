# urls.py
from django.urls import path
from . import views  

urlpatterns = [
    # Home & Auth
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Admin Panel
path("admin-panel/", views.admin_panel, name="admin_panel"),
    path("admin-panel/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/regions/create/", views.create_region, name="create_region"),
    path("admin-panel/regions/", views.list_regions, name="list_regions"),
    path("admin-panel/rms/", views.list_rms, name="list_rms"),
    path("admin-panel/rms/create/", views.create_rm, name="create_rm"),
    path("admin-panel/rms/<int:rm_id>/edit/", views.edit_rm, name="edit_rm"),
    path("admin-panel/rms/<int:rm_id>/delete/", views.delete_rm, name="delete_rm"),
    path("admin-panel/employees/create/", views.create_employee, name="create_employee"),
    path("admin-panel/employees/", views.list_employees, name="list_employees"),
    path("admin-panel/analytics-data/", views.analytics_data, name="analytics_data"),
    path("admin/compliance/", views.admin_compliance_overview, name="admin_compliance_overview"),
    path("admin-face-recognition/", views.admin_live_logs, name="face_recognition_admin"),
    # Regional Manager
    path("rm/dashboard/", views.rm_dashboard, name="rm_dashboard"),
    path("rm/compliance/", views.rm_compliance_dashboard, name="rm_compliance_dashboard"),

    # Employee
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee/upload/', views.upload_compliance_image, name='upload_compliance_image'),
    path('employee/compliance/', views.employee_compliance_dashboard, name='employee_compliance_dashboard'),
    path('employee/record/', views.record_compliance, name='record_compliance'),

    # Live Detection
    path("live-detection/", views.live_detection, name="live_detection"),
path("live-logs/", views.admin_live_logs, name="admin_live_logs"),


    path("face-recognition/", views.face_recognition_dashboard, name="face_recognition_dashboard"),
    path("face-recognition/store/", views.store_face_recognition, name="store_face_recognition"),
]
