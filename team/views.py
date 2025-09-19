from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta
from .models import Employee, Absence, Vacation, Birthday, AbsenceType


@login_required
def team_dashboard(request):
    """Dashboard principal del módulo de equipo"""
    employees = Employee.objects.filter(is_active=True).select_related('user')
    
    # Próximos cumpleaños (30 días)
    upcoming_birthdays = Birthday.get_upcoming_birthdays(days=30)
    
    # Ausencias actuales
    today = date.today()
    current_absences = Absence.objects.filter(
        start_date__lte=today,
        end_date__gte=today
    ).select_related('employee', 'absence_type')
    
    # Próximas ausencias (7 días)
    upcoming_absences = Absence.objects.filter(
        start_date__gt=today,
        start_date__lte=today + timedelta(days=7)
    ).select_related('employee', 'absence_type')
    
    context = {
        'employees': employees,
        'upcoming_birthdays': upcoming_birthdays,
        'current_absences': current_absences,
        'upcoming_absences': upcoming_absences,
        'total_employees': employees.count(),
    }
    
    return render(request, 'team/dashboard.html', context)


@login_required
def employee_list(request):
    """Lista de empleados"""
    queryset = Employee.objects.select_related('user')
    
    # Filtros
    search = request.GET.get('search', '')
    department = request.GET.get('department', '')
    status = request.GET.get('status', '')
    
    if search:
        queryset = queryset.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(employee_id__icontains=search) |
            Q(position__icontains=search)
        )
    
    if department:
        queryset = queryset.filter(department=department)
    
    if status:
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
    
    # Obtener departamentos únicos para el filtro
    departments = Employee.objects.values_list('department', flat=True).distinct()
    
    context = {
        'employees': queryset,
        'departments': departments,
        'search': search,
        'selected_department': department,
        'selected_status': status,
    }
    
    return render(request, 'team/employee_list.html', context)


@login_required
def employee_detail(request, pk):
    """Detalle de empleado"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # Historial de ausencias
    absences = employee.absences.all().order_by('-start_date')[:10]
    
    # Control de vacaciones
    current_year = date.today().year
    vacation_records = employee.vacations.filter(
        year__in=[current_year-1, current_year, current_year+1]
    ).order_by('-year')
    
    context = {
        'employee': employee,
        'absences': absences,
        'vacation_records': vacation_records,
    }
    
    return render(request, 'team/employee_detail.html', context)


@login_required
def absence_list(request):
    """Lista de ausencias"""
    queryset = Absence.objects.select_related('employee', 'absence_type')
    
    # Filtros
    employee_id = request.GET.get('employee', '')
    absence_type_id = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if employee_id:
        queryset = queryset.filter(employee_id=employee_id)
    
    if absence_type_id:
        queryset = queryset.filter(absence_type_id=absence_type_id)
    
    if date_from:
        queryset = queryset.filter(start_date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(end_date__lte=date_to)
    
    # Datos para filtros
    employees = Employee.objects.filter(is_active=True).select_related('user')
    absence_types = AbsenceType.objects.all()
    
    context = {
        'absences': queryset.order_by('-start_date'),
        'employees': employees,
        'absence_types': absence_types,
        'selected_employee': employee_id,
        'selected_type': absence_type_id,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'team/absence_list.html', context)


@login_required
def vacation_summary(request):
    """Resumen de vacaciones"""
    current_year = date.today().year
    
    # Obtener registros de vacaciones del año actual
    vacation_records = Vacation.objects.filter(
        year=current_year
    ).select_related('employee__user').order_by('employee__user__first_name')
    
    # Estadísticas generales
    total_entitled = sum(v.days_entitled for v in vacation_records)
    total_taken = sum(v.days_taken for v in vacation_records)
    total_pending = sum(v.days_pending for v in vacation_records)
    
    context = {
        'vacation_records': vacation_records,
        'current_year': current_year,
        'total_entitled': total_entitled,
        'total_taken': total_taken,
        'total_pending': total_pending,
    }
    
    return render(request, 'team/vacation_summary.html', context)


@login_required
def birthday_calendar(request):
    """Calendario de cumpleaños"""
    # Obtener mes actual o el seleccionado
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    
    # Obtener empleados con cumpleaños en el mes
    employees = Employee.objects.filter(
        is_active=True,
        birth_date__month=month
    ).select_related('user').order_by('birth_date__day')
    
    birthdays = []
    for emp in employees:
        birthday_date = date(year, month, emp.birth_date.day)
        age = year - emp.birth_date.year
        birthdays.append({
            'employee': emp,
            'date': birthday_date,
            'age': age
        })
    
    # Generar lista de meses para navegación
    months = [
        (i, date(2000, i, 1).strftime('%B'))
        for i in range(1, 13)
    ]
    
    context = {
        'birthdays': birthdays,
        'selected_month': month,
        'selected_year': year,
        'months': months,
        'month_name': date(year, month, 1).strftime('%B'),
    }
    
    return render(request, 'team/birthday_calendar.html', context)