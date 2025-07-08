from django.contrib import admin
from django.urls import path
from crm.views import upload_file, dashboard, generate_chart, export_pdf,index,user_login, user_logout, user_register, profile_view
from . import views

urlpatterns = [
    path('', index, name="index"),
    path("upload/", upload_file, name="upload"),
    path("dashboard/", dashboard, name="dashboard"),
    path("chart/", generate_chart, name="chart"),
    path("export_pdf/", export_pdf, name="export_pdf"),
    path('profile/', profile_view, name='profile'),
    # path('profile/', views.user_profile, name='profile'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', user_register, name='register'),
    path('insert/', views.insert_data_by_form, name='insert_data_by_form'),
    path('export_to_excel/', views.export_to_excel, name='export_to_excel'),
    path('edit/<int:id>/', views.edit_customer, name='edit_customer'),
    path('delete/<int:id>/', views.delete_customer, name='delete_customer'),
    # path('export/csv/', views.export_customer_data_csv, name='export_csv'),
    # path('upload/', views.upload_file, name='upload_file'),
    # path('upload/preview/', views.preview_upload, name='preview_upload'),
    # path('upload/save/<int:file_id>/<str:sheet_name>/', views.save_sheet_to_db, name='save_sheet_to_db'),
]