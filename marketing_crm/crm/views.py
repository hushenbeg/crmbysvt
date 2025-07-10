from django.core.mail import send_mail
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from django.shortcuts import render
from .models import UploadedFile, CustomerData, VisitorCounter, Profile
from django.utils.timezone import now
from django.conf import settings
from datetime import datetime
from django.contrib import messages
from openpyxl import Workbook, load_workbook
from django.core.cache import cache
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm, ProfileUpdateForm, ProfileForm   # Import the custom form
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from collections import Counter
from django.db.models import Count
from django.core.serializers.json import DjangoJSONEncoder
import json
from reportlab.lib.styles import getSampleStyleSheet
from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user
from django.views import View
from django.shortcuts import render
from django.db.models import Count, Sum
from .models import ImportedFile
# Create your views here.
# def index(request):

class ViewImportedFiles(View):
    def get(self, request):
        # Get basic file information first
        files = ImportedFile.objects.all().order_by('-uploaded_at')
        
        # Get counts separately in a single query
        counts = ImportedFile.objects.values('id').annotate(
            record_count=Count('dynamicdata')
        ).order_by('-uploaded_at')
        
        # Convert counts to a dictionary for easy lookup
        count_dict = {item['id']: item['record_count'] for item in counts}
        
        # Prepare files data with counts
        files_data = []
        total_records = 0
        
        for file in files:
            record_count = count_dict.get(file.id, 0)
            total_records += record_count
            files_data.append({
                'id': file.id,
                'file_name': file.file_name,
                'uploaded_at': file.uploaded_at,
                'file_type': file.file_type,
                'record_count': record_count
            })
        
        return render(request, 'crm/imported_files.html', {
            'files': files_data,
            'total_records': total_records
        })

@login_required(login_url='/login/')
def upload_file(request):
    user = get_user(request)  # resolves LazyObject issue
    if not user.is_authenticated:
        return redirect('/login/')
    if not request.session.get('has_visited'):
        counter, created = VisitorCounter.objects.get_or_create(pk=1)
        counter.count += 1
        counter.save()
        request.session['has_visited'] = True

    # Get visitor count from DB
    visitor_count = VisitorCounter.objects.first()

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")  # Get file safely
        if uploaded_file:
            try:
                # Save file instance
                file_instance = UploadedFile.objects.create(file=uploaded_file, uploaded_by=request.user)

                # Ensure the file is saved before reading it
                file_path = file_instance.file.path

                # Read Excel file
                df = pd.read_excel(file_path)

                # Rename Excel columns to match model fields
                df.rename(columns={
                    'Company name': 'company_name',
                    'Location': 'location',
                    'Person name': 'person_name',
                    'Contact No': 'contact_no',
                    'EMAIL ID': 'email_id',
                    'Remark': 'remark',
                    'Date': 'date'
                }, inplace=True)

                # Insert each row into the CustomerData model
                for _, row in df.iterrows():
                    try:
                        # Get and sanitize the date
                        raw_date = row.get("date")

                        if pd.isna(raw_date):
                            formatted_date = now().date()  # Use today's date if empty
                        else:
                            formatted_date = pd.to_datetime(raw_date).date()  # Convert to datetime.date object

                        # # Convert date format
                        # raw_date = row.get("date", now().date())
                        # if pd.isna(raw_date):
                        #     formatted_date = now().strftime('%m-%d-%y')  # Default to current date
                        # else:
                        #     formatted_date = pd.to_datetime(raw_date).strftime('%m-%d-%y')
                        user = request.user
                        if not user or not user.is_authenticated:
                            return HttpResponse("User not authenticated", status=401)
                        email_val = row.get("email_id")
                        email_val = email_val if pd.notna(email_val) and str(email_val).strip() != '' else None
                        CustomerData.objects.create(
                            user=user,
                            date=formatted_date,  # Now formatted as MM-DD-YY
                            company_name=row.get("company_name", "Unknown"),
                            location=row.get("location", "Not Provided"),
                            person_name=row.get("person_name", "Unknown"),
                            contact_no=row.get("contact_no", ""),
                            email_id=email_val,
                            remark=row.get("remark", "")
                        )
                    except Exception as row_error:
                        print(f"Skipping row due to error: {row_error}")

                return redirect("index")
            except Exception as e:
                return HttpResponse(f"Error processing file: {str(e)}", status=400)
        else:
            return HttpResponse("No file uploaded. Please select a file.", status=400)

    context = {
        'visitor_count':visitor_count.count if visitor_count else 0
    }

    return render(request, "crm/upload.html", context)

#
# Dashboard with Visualization
@login_required(login_url='/login/')
def dashboard(request):
    user = get_user(request)  # resolves LazyObject issue
    if not user.is_authenticated:
        return redirect('/login/')
    if not request.session.get('has_visited'):
        counter, created = VisitorCounter.objects.get_or_create(pk=1)
        counter.count += 1
        counter.save()
        request.session['has_visited'] = True

    # Get parameters
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    filter_triggered = request.GET.get('filter_triggered')
    person_search = request.GET.get('person_search')

    is_admin = getattr(request.user, 'is_admin', False)

    # Base queryset
    # data = CustomerData.objects.all().order_by('-date', '-id')
    if is_admin:
        data = CustomerData.objects.all().order_by('-date', '-id')
    else:
        data = CustomerData.objects.filter(user=request.user).order_by('-date', '-id')

    # Apply search filter (by person or company name)
    if search_query:
        data = data.filter(
            Q(person_name__icontains=search_query) |
            Q(company_name__icontains=search_query)|
            Q(email_id__icontains=search_query)
        )


    # Filter only if user clicked the Filter button
    if filter_triggered and start_date and end_date:
        data = data.filter(date__range=[start_date, end_date])
    else:
        # Reset start and end date for clarity in template if not filtered
        start_date = end_date = None

    # Pagination
    paginator = Paginator(data, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Smart page range for display
    current_page = page_obj.number
    total_pages = paginator.num_pages
    start_page = max(current_page - 2, 1)
    end_page = min(current_page + 2, total_pages) + 1
    custom_page_range = range(start_page, end_page)

    # Get visitor count from DB
    visitor_count = VisitorCounter.objects.first()

    # Count customer entries by location
    # location_counts = CustomerData.objects.values('location').annotate(count=Count('location'))
    if is_admin:
        location_counts = CustomerData.objects.values('location').annotate(count=Count('location'))
    else:
        location_counts = CustomerData.objects.filter(user=request.user).values('location').annotate(count=Count('location'))


    # Prepare serialized data for Chart.js
    json_data = json.dumps(list(data.values()), cls=DjangoJSONEncoder)

    context = {
        'data': page_obj,         # for table display
        'custom_page_range': custom_page_range,
        'chart_data': json_data,  # for JS chart
        'start_date': start_date,
        'end_date': end_date,
        'visitor_count': visitor_count.count if visitor_count else 0

    }

    return render(request, 'crm/dashboard.html', context)

@login_required
def generate_chart(request):
    customers = CustomerData.objects.all()
    data = [c.created_at.date() for c in customers]
    plt.figure(figsize=(8,4))
    sns.histplot(data, bins=10, kde=True)
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")

# Export Reports to PDF
@login_required(login_url='/login/')
def export_pdf(request):
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    person_search = request.GET.get('person_search')
    # filter_triggered = request.GET.get('filter_triggered')

    # Base queryset
    queryset = CustomerData.objects.all().order_by('-date')

    if start_date and end_date:
        # Make sure dates are parsed correctly
        parsed_start = parse_date(start_date)
        parsed_end = parse_date(end_date)
        if parsed_start and parsed_end:
            queryset = queryset.filter(date__range=[parsed_start, parsed_end])

    if person_search:
        queryset = queryset.filter(person_name__icontains=person_search)

    # Prepare PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="customer_data.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []

    # Table Header
    data = [
        ["Date", "Company Name", "Location", "Person Name", "Contact No", "Email Id", "Remark"]
    ]

    # Table Body
    for customer in queryset:
        data.append([
            customer.date.strftime("%m-%d-%y"),
            customer.company_name,
            customer.location,
            customer.person_name,
            customer.contact_no,
            customer.email_id,
            customer.remark if customer.remark else "",
        ])

    # Column widths
    col_widths = [70, 110, 100, 100, 90, 150, 130]

    # Wrap content using Paragraphs
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    wrapped_data = [[Paragraph(str(cell), styleN) for cell in row] for row in data]

    table = Table(wrapped_data, colWidths=col_widths)

    # Table Styling
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ])
    table.setStyle(style)

    elements.append(table)
    doc.build(elements)
    return response


# Login View
def user_login(request):
    if 'next' in request.GET:
        messages.info(request, "Please login to continue.")

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard after login
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'crm/login.html')

# Logout View
def user_logout(request):
    logout(request)
    return redirect('login')

def user_register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'crm/register.html', {'form': form})

@login_required(login_url='/login/')
def profile_view(request):
    # Track visitor count
    if not request.session.get('has_visited'):
        counter, created = VisitorCounter.objects.get_or_create(pk=1)
        counter.count += 1
        counter.save()
        request.session['has_visited'] = True

    # Get visitor count
    visitor_count = VisitorCounter.objects.first()

    user = request.user

    # ✅ Safely get or create the user’s profile
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form = ProfileUpdateForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'crm/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'visitor_count': visitor_count.count if visitor_count else 0
    })

def insert_data_by_form(request):
    if not request.session.get('has_visited'):
        counter, created = VisitorCounter.objects.get_or_create(pk=1)
        counter.count += 1
        counter.save()
        request.session['has_visited'] = True
    # Get visitor count from DB
    visitor_count = VisitorCounter.objects.first()

    if request.method == 'POST':
        try:
            # Get form data with proper defaults
            date = request.POST.get('date', timezone.now())
            company_name = request.POST.get('company_name', '')
            location = request.POST.get('location', 'Unknown')
            person_name = request.POST.get('person_name', 'Anonymous')
            contact_no = request.POST.get('contact_no', '0000000000')
            email_id = request.POST.get('email_id', 'noemail@example.com')
            remark = request.POST.get('remark', '')

            # Create and save new CustomerData instance
            CustomerData.objects.create(
                user = request.user,
                date=date,
                company_name=company_name,
                location=location,
                person_name=person_name,
                contact_no=contact_no,
                email_id=email_id,
                remark=remark
            )

            messages.success(request, 'Customer data added successfully to database!')
            return redirect('index')

        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error occurred: {str(e)}')

        return redirect('index')

    return render(request, 'crm/insert_data_by_form.html', {'visitor_count': visitor_count.count if visitor_count else 0})

@login_required(login_url='/login/')
def export_to_excel(request):
    person_search = request.GET.get('person_search')
    # Add filters if needed
    queryset = CustomerData.objects.all()

    # Apply date filter if provided
    if request.GET.get('start_date'):
        queryset = queryset.filter(date__gte=request.GET['start_date'])
    if request.GET.get('end_date'):
        queryset = queryset.filter(date__lte=request.GET['end_date'])

    if person_search:
        queryset = queryset.filter(person_name__icontains=person_search)

    # Prepare data
    data = queryset.values(
        'date', 'company_name', 'location',
        'person_name', 'contact_no', 'email_id', 'remark'
    )

    # Create DataFrame
    df = pd.DataFrame.from_records(data)

    # Add current date to filename
    export_date = timezone.now().strftime('%Y-%m-%d')
    filename = f"customer_data_export_{export_date}.xlsx"

    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Export
    df.to_excel(response, index=False)
    return response

from .forms import CustomerDataForm  # ✅ Import the form
def edit_customer(request, id):
    customer = get_object_or_404(CustomerData, id=id)
    if request.method == 'POST':
        form = CustomerDataForm(request.POST, instance=customer)
        if form.is_valid():
            updated_customer = form.save(commit=False)
            updated_customer.date = timezone.now()  # 🔥 Keep existing or set now
            updated_customer.save()
            messages.success(request, 'Customer updated successfully!')
            return redirect('dashboard')
    else:
        form = CustomerDataForm(instance=customer)
    return render(request, 'crm/edit_customer.html', {'form': form})

def delete_customer(request, id):
    customer = get_object_or_404(CustomerData, id=id)
    customer.delete()
    messages.warning(request, 'Customer deleted successfully.')
    return redirect('dashboard')


import pandas as pd
from django.shortcuts import render, redirect
from django.views import View
from .forms import ExcelUploadForm
from .models import ImportedFile, DynamicData

class ExcelUploadView(View):
    def get(self, request):
        form = ExcelUploadForm()
        return render(request, 'crm/upload_excel.html', {'form': form})
    def post(self, request):
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            
            try:
                df = pd.read_excel(excel_file)
                
                # Convert Timestamps to strings
                for col in df.select_dtypes(include=['datetime']).columns:
                    df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Convert other non-JSON-serializable types
                df = df.applymap(lambda x: str(x) if isinstance(x, (pd.Timestamp, pd.Timedelta)) else x)
                
                # Save file metadata with user association
                imported_file = ImportedFile(
                    file_name=form.cleaned_data['file_name'],
                    file_type=form.cleaned_data['file_type'],
                    notes=form.cleaned_data['notes'],
                    original_columns=list(df.columns),
                    user=request.user  # THIS IS WHERE YOU ADD THE USER
                )
                imported_file.save()  # Save the instance after setting all fields
                
                # Convert each row to a serializable dictionary
                for _, row in df.iterrows():
                    row_dict = row.to_dict()
                    
                    # Ensure all values are JSON-serializable
                    for key, value in row_dict.items():
                        if isinstance(value, (pd.Timestamp, pd.Timedelta)):
                            row_dict[key] = str(value)
                        elif pd.isna(value):
                            row_dict[key] = None
                    
                    DynamicData.objects.create(
                        source_file=imported_file,
                        row_data=row_dict
                    )
                
                return redirect('view_imported_files')
                
            except Exception as e:
                return render(request, 'crm/upload_excel.html', {
                    'form': form,
                    'error': f'Error processing file: {str(e)}'
                })

        return render(request, 'crm/upload_excel.html', {'form': form})

from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from .models import ImportedFile

class ViewImportedFiles(LoginRequiredMixin, View):
    login_url = '/login/'  # Specify your login URL

    def get(self, request):
        # Get basic file information first
        if request.user.is_superuser or request.user.is_staff:
            files = ImportedFile.objects.all().order_by('-uploaded_at')
            total_records = sum(file.record_count for file in files)
        else:
            files = ImportedFile.objects.filter(user=request.user).order_by('-uploaded_at')
            total_records = sum(file.record_count for file in files)

        # Get counts separately in a single query
        counts = ImportedFile.objects.values('id').annotate(
            record_count=Count('dynamicdata')
        ).order_by('-uploaded_at')
        
        # Convert counts to a dictionary for easy lookup
        count_dict = {item['id']: item['record_count'] for item in counts}
        
        # Prepare files data with counts
        files_data = []
        total_records = 0
        
        for file in files:
            record_count = count_dict.get(file.id, 0)
            total_records += record_count
            files_data.append({
                'id': file.id,
                'file_name': file.file_name,
                'uploaded_at': file.uploaded_at,
                'file_type': file.file_type,
                'record_count': record_count
            })
        
        return render(request, 'crm/imported_files.html', {
            'files': files_data,
            'total_records': total_records,
            'is_admin': request.user.is_superuser or request.user.is_staff
        })

class ViewFileData(View):
    def get(self, request, file_id):
        imported_file = ImportedFile.objects.get(id=file_id)
        data = DynamicData.objects.filter(source_file=imported_file)
        
        # Get all unique keys across all rows for table headers
        all_keys = set()
        for item in data:
            all_keys.update(item.row_data.keys())
        headers = sorted(all_keys)
        
        return render(request, 'crm/file_data.html', {
            'file': imported_file,
            'data': data,
            'headers': headers
        })

from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import ImportedFile

class DeleteUploadedFile(DeleteView):
    model = ImportedFile
    success_url = reverse_lazy('view_imported_files')  # Redirect to files list after deletion
    template_name = 'crm/confirm_delete.html'  # Optional confirmation template

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'File and its data deleted successfully')
        return response
    

from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import DynamicData

class DeleteDataRowView(View):
    def post(self, request, row_id):
        try:
            row = get_object_or_404(DynamicData, id=row_id)
            
            # Verify ownership (now that user field exists)
            if not request.user.is_authenticated:
                return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
                
            if row.source_file.user != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            row.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


