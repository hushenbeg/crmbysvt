from django.contrib import admin
from django.urls import path
from crm.views import (
    upload_file, dashboard, generate_chart, export_pdf,
    user_login, user_logout, user_register, profile_view,
    ExcelUploadView, ViewImportedFiles,DeleteUploadedFile, ViewFileData, DeleteDataRowView 
)
from . import views

urlpatterns = [
    path('', ViewImportedFiles.as_view(), name="index"),
    path("upload_excel/", ExcelUploadView.as_view(), name="upload_excel"),  # Class-based view
    # path("dashboard/", dashboard, name="dashboard"),
    # path('dashboard/', views.ViewImportedFiles.as_view(), name='view_imported_files'),
    path("dashboard/", ViewImportedFiles.as_view(), name="dashboard"),
    path("chart/", generate_chart, name="chart"),
    path("export_pdf/", export_pdf, name="export_pdf"),
    path('profile/', profile_view, name='profile'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('register/', user_register, name='register'),
    path('insert/', views.insert_data_by_form, name='insert_data_by_form'),
    path('export_to_excel/', views.export_to_excel, name='export_to_excel'),
    path('edit/<int:id>/', views.edit_customer, name='edit_customer'),
    path('delete/<int:id>/', views.delete_customer, name='delete_customer'),
    path('files/', ViewImportedFiles.as_view(), name='view_imported_files'),
    path('files/<int:file_id>/', ViewFileData.as_view(), name='view_file_data'),
    # path('files/delete/<int:file_id>/', views.delete_uploaded_file, name='delete_uploaded_file'),
     path('files/delete/<int:pk>/', DeleteUploadedFile.as_view(), name='delete_uploaded_file'),
     path('data/delete/<int:row_id>/', DeleteDataRowView.as_view(), name='delete_data_row'),
    #  path('data/update/<int:row_id>/', UpdateDataRowView.as_view(), name='update_data_row'),
]