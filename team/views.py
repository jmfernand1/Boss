from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
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
    
    # Agregar información de alerta para vacaciones con muchos días pendientes
    for vacation in vacation_records:
        vacation.has_many_pending_days = vacation.days_pending > 10
    
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
    
    # Calcular porcentaje de utilización
    utilization_percentage = 0
    if total_entitled > 0:
        utilization_percentage = round((total_taken / total_entitled) * 100)
    
    # Top 5 empleados con más días pendientes
    top_pending_employees = sorted(
        [v for v in vacation_records if v.days_pending > 0],
        key=lambda x: x.days_pending,
        reverse=True
    )[:5]
    
    context = {
        'vacation_records': vacation_records,
        'current_year': current_year,
        'total_entitled': total_entitled,
        'total_taken': total_taken,
        'total_pending': total_pending,
        'utilization_percentage': utilization_percentage,
        'top_pending_employees': top_pending_employees,
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
    
    # Generar lista de meses para navegación (en español)
    months = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    # Generar lista de años (5 años antes y después del año actual)
    current_year = date.today().year
    years = list(range(current_year - 5, current_year + 6))
    
    # Obtener nombre del mes seleccionado
    month_names = dict(months)
    selected_month_name = month_names.get(month, '')
    
    # Calcular navegación anterior y siguiente
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'birthdays': birthdays,
        'selected_month': month,
        'selected_year': year,
        'months': months,
        'years': years,
        'month_name': selected_month_name,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'prev_month_name': month_names.get(prev_month, ''),
        'next_month': next_month,
        'next_year': next_year,
        'next_month_name': month_names.get(next_month, ''),
    }
    
    return render(request, 'team/birthday_calendar.html', context)


# ============================================================================
# VISTAS CRUD
# ============================================================================

@login_required
def employee_create(request):
    """Crear nuevo empleado"""
    from .forms import EmployeeForm
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Empleado {employee.full_name} creado exitosamente.')
            return redirect('team:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm()
    
    return render(request, 'team/employee_form.html', {
        'form': form,
        'title': 'Nuevo Empleado',
        'action': 'create',
        'back_url': reverse('team:employee_list')
    })


@login_required
def employee_edit(request, pk):
    """Editar empleado existente"""
    from .forms import EmployeeForm
    
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Empleado {employee.full_name} actualizado exitosamente.')
            return redirect('team:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)
    
    return render(request, 'team/employee_form.html', {
        'form': form,
        'employee': employee,
        'title': f'Editar - {employee.full_name}',
        'action': 'edit',
        'back_url': reverse('team:employee_detail', args=[employee.pk])
    })


def _check_employee_deletion_constraints(employee):
    """
    Verifica todas las restricciones que pueden impedir la eliminación de un empleado.
    Retorna un diccionario con información sobre las restricciones.
    """
    from initiatives.models import InitiativeUpdate
    
    constraints = {
        'can_delete': True,
        'blocking_reasons': [],
        'warnings': [],
        'owned_initiatives': [],
        'assigned_stories': [],
        'assigned_tasks': [],
        'collaborated_initiatives': [],
        'created_updates': [],
        'absences_count': 0,
        'vacations_count': 0,
    }
    
    # Verificar iniciativas donde es propietario (PROTECT)
    owned_initiatives = employee.owned_initiatives.all()
    if owned_initiatives.exists():
        constraints['can_delete'] = False
        constraints['blocking_reasons'].append(
            f'Es propietario de {owned_initiatives.count()} iniciativa(s)'
        )
        constraints['owned_initiatives'] = list(owned_initiatives)
    
    # Verificar actualizaciones de iniciativas creadas por el usuario (PROTECT)
    # Como Employee tiene OneToOne con User, verificamos las actualizaciones del usuario
    created_updates = InitiativeUpdate.objects.filter(created_by=employee.user)
    if created_updates.exists():
        constraints['can_delete'] = False
        constraints['blocking_reasons'].append(
            f'Ha creado {created_updates.count()} actualización(es) de iniciativas'
        )
        constraints['created_updates'] = list(created_updates)
    
    # Verificar historias de usuario asignadas (SET_NULL - no bloquea)
    assigned_stories = employee.assigned_stories.all()
    if assigned_stories.exists():
        constraints['warnings'].append(
            f'Tiene {assigned_stories.count()} historia(s) de usuario asignada(s) (se desasignarán)'
        )
        constraints['assigned_stories'] = list(assigned_stories)
    
    # Verificar tareas asignadas (SET_NULL - no bloquea)
    assigned_tasks = employee.assigned_tasks.all()
    if assigned_tasks.exists():
        constraints['warnings'].append(
            f'Tiene {assigned_tasks.count()} tarea(s) asignada(s) (se desasignarán)'
        )
        constraints['assigned_tasks'] = list(assigned_tasks)
    
    # Verificar iniciativas donde colabora (ManyToMany - no bloquea)
    collaborated_initiatives = employee.collaborated_initiatives.all()
    if collaborated_initiatives.exists():
        constraints['warnings'].append(
            f'Colabora en {collaborated_initiatives.count()} iniciativa(s) (se removerá como colaborador)'
        )
        constraints['collaborated_initiatives'] = list(collaborated_initiatives)
    
    # Contar ausencias y vacaciones (CASCADE - se eliminarán)
    absences_count = employee.absences.count()
    vacations_count = employee.vacations.count()
    
    if absences_count > 0:
        constraints['warnings'].append(f'Tiene {absences_count} ausencia(s) (se eliminarán)')
        constraints['absences_count'] = absences_count
    
    if vacations_count > 0:
        constraints['warnings'].append(f'Tiene {vacations_count} registro(s) de vacaciones (se eliminarán)')
        constraints['vacations_count'] = vacations_count
    
    return constraints


@login_required
def employee_delete(request, pk):
    """Eliminar empleado"""
    employee = get_object_or_404(Employee, pk=pk)
    
    # Verificar todas las restricciones
    constraints = _check_employee_deletion_constraints(employee)
    
    if request.method == 'POST':
        if not constraints['can_delete']:
            blocking_reasons = '; '.join(constraints['blocking_reasons'])
            messages.error(
                request, 
                f'No se puede eliminar a {employee.full_name} porque: {blocking_reasons}. '
                'Debe resolver estas restricciones antes de eliminar.'
            )
            return redirect('team:employee_detail', pk=employee.pk)
        
        try:
            employee_name = employee.full_name
            user_to_delete = employee.user  # Guardar referencia al usuario
            
            # Eliminar el empleado (esto también eliminará el usuario por CASCADE)
            employee.delete()
            
            messages.success(request, f'Empleado {employee_name} eliminado exitosamente.')
            return redirect('team:employee_list')
            
        except Exception as e:
            messages.error(
                request, 
                f'Error al eliminar el empleado: {str(e)}. '
                'Verifique que no tenga registros relacionados que impidan la eliminación.'
            )
            return redirect('team:employee_detail', pk=employee.pk)
    
    context = {
        'employee': employee,
        'constraints': constraints,
        'owned_initiatives': constraints['owned_initiatives'],
        'assigned_stories': constraints['assigned_stories'],
        'assigned_tasks': constraints['assigned_tasks'],
        'collaborated_initiatives': constraints['collaborated_initiatives'],
        'blocking_initiatives': not constraints['can_delete'],
    }
    
    return render(request, 'team/employee_confirm_delete.html', context)


@login_required
def absence_create(request):
    """Crear nueva ausencia"""
    from .forms import AbsenceForm
    
    if request.method == 'POST':
        form = AbsenceForm(request.POST)
        if form.is_valid():
            absence = form.save()
            messages.success(request, f'Ausencia registrada para {absence.employee.full_name}.')
            return redirect('team:absence_list')
    else:
        form = AbsenceForm()
        # Pre-seleccionar empleado si viene en query params
        employee_id = request.GET.get('employee')
        if employee_id:
            try:
                employee = Employee.objects.get(pk=employee_id)
                form.fields['employee'].initial = employee
            except Employee.DoesNotExist:
                pass
    
    return render(request, 'team/absence_form.html', {
        'form': form,
        'title': 'Nueva Ausencia',
        'action': 'create',
        'back_url': reverse('team:absence_list')
    })


@login_required
def absence_edit(request, pk):
    """Editar ausencia existente"""
    from .forms import AbsenceForm
    
    absence = get_object_or_404(Absence, pk=pk)
    
    if request.method == 'POST':
        form = AbsenceForm(request.POST, instance=absence)
        if form.is_valid():
            absence = form.save()
            messages.success(request, f'Ausencia de {absence.employee.full_name} actualizada.')
            return redirect('team:absence_list')
    else:
        form = AbsenceForm(instance=absence)
    
    return render(request, 'team/absence_form.html', {
        'form': form,
        'absence': absence,
        'title': f'Editar Ausencia - {absence.employee.full_name}',
        'action': 'edit'
    })


@login_required
def absence_delete(request, pk):
    """Eliminar ausencia"""
    absence = get_object_or_404(Absence, pk=pk)
    
    if request.method == 'POST':
        employee_name = absence.employee.full_name
        absence_type = absence.absence_type.name
        absence.delete()
        messages.success(request, f'Ausencia ({absence_type}) de {employee_name} eliminada.')
        return redirect('team:absence_list')
    
    return render(request, 'team/absence_confirm_delete.html', {
        'absence': absence
    })


@login_required
def vacation_create(request):
    """Crear nuevo registro de vacaciones"""
    from .forms import VacationForm
    
    if request.method == 'POST':
        form = VacationForm(request.POST)
        if form.is_valid():
            vacation = form.save()
            messages.success(request, f'Control de vacaciones creado para {vacation.employee.full_name}.')
            return redirect('team:vacation_summary')
    else:
        form = VacationForm()
        # Pre-seleccionar empleado si viene en query params
        employee_id = request.GET.get('employee')
        if employee_id:
            try:
                employee = Employee.objects.get(pk=employee_id)
                form.fields['employee'].initial = employee
            except Employee.DoesNotExist:
                pass
    
    return render(request, 'team/vacation_form.html', {
        'form': form,
        'title': 'Nuevo Control de Vacaciones',
        'action': 'create'
    })


@login_required
def vacation_edit(request, pk):
    """Editar registro de vacaciones"""
    from .forms import VacationForm
    
    vacation = get_object_or_404(Vacation, pk=pk)
    
    if request.method == 'POST':
        form = VacationForm(request.POST, instance=vacation)
        if form.is_valid():
            vacation = form.save()
            messages.success(request, f'Control de vacaciones de {vacation.employee.full_name} actualizado.')
            return redirect('team:vacation_summary')
    else:
        form = VacationForm(instance=vacation)
    
    return render(request, 'team/vacation_form.html', {
        'form': form,
        'vacation': vacation,
        'title': f'Editar Vacaciones - {vacation.employee.full_name} ({vacation.year})',
        'action': 'edit'
    })


@login_required
def vacation_delete(request, pk):
    """Eliminar registro de vacaciones"""
    vacation = get_object_or_404(Vacation, pk=pk)
    
    if request.method == 'POST':
        employee_name = vacation.employee.full_name
        year = vacation.year
        vacation.delete()
        messages.success(request, f'Control de vacaciones de {employee_name} ({year}) eliminado.')
        return redirect('team:vacation_summary')
    
    return render(request, 'team/vacation_confirm_delete.html', {
        'vacation': vacation
    })


@login_required
def absence_type_list(request):
    """Lista de tipos de ausencia"""
    absence_types = AbsenceType.objects.all().order_by('name')
    
    context = {
        'absence_types': absence_types,
    }
    
    return render(request, 'team/absence_type_list.html', context)


@login_required
def absence_type_create(request):
    """Crear nuevo tipo de ausencia"""
    from .forms import AbsenceTypeForm
    
    if request.method == 'POST':
        form = AbsenceTypeForm(request.POST)
        if form.is_valid():
            absence_type = form.save()
            messages.success(request, f'Tipo de ausencia "{absence_type.name}" creado exitosamente.')
            return redirect('team:absence_type_list')
    else:
        form = AbsenceTypeForm()
    
    return render(request, 'team/absence_type_form.html', {
        'form': form,
        'title': 'Nuevo Tipo de Ausencia',
        'action': 'create'
    })


@login_required
def absence_type_edit(request, pk):
    """Editar tipo de ausencia"""
    from .forms import AbsenceTypeForm
    
    absence_type = get_object_or_404(AbsenceType, pk=pk)
    
    if request.method == 'POST':
        form = AbsenceTypeForm(request.POST, instance=absence_type)
        if form.is_valid():
            absence_type = form.save()
            messages.success(request, f'Tipo de ausencia "{absence_type.name}" actualizado.')
            return redirect('team:absence_type_list')
    else:
        form = AbsenceTypeForm(instance=absence_type)
    
    return render(request, 'team/absence_type_form.html', {
        'form': form,
        'absence_type': absence_type,
        'title': f'Editar Tipo - {absence_type.name}',
        'action': 'edit'
    })


@login_required
def absence_type_delete(request, pk):
    """Eliminar tipo de ausencia"""
    absence_type = get_object_or_404(AbsenceType, pk=pk)
    
    # Verificar si el tipo está siendo usado
    if absence_type.absence_set.exists():
        messages.error(request, f'No se puede eliminar "{absence_type.name}" porque está siendo usado en ausencias existentes.')
        return redirect('team:absence_type_list')
    
    if request.method == 'POST':
        type_name = absence_type.name
        absence_type.delete()
        messages.success(request, f'Tipo de ausencia "{type_name}" eliminado exitosamente.')
        return redirect('team:absence_type_list')
    
    return render(request, 'team/absence_type_confirm_delete.html', {
        'absence_type': absence_type
    })


@login_required
def quick_absence(request):
    """Vista para registro rápido de ausencias (AJAX)"""
    from .forms import QuickAbsenceForm
    
    if request.method == 'POST':
        form = QuickAbsenceForm(request.POST)
        if form.is_valid():
            absence = form.save()
            messages.success(request, f'Ausencia registrada para {absence.employee.full_name}.')
            return redirect('team:team_dashboard')
    else:
        form = QuickAbsenceForm()
    
    return render(request, 'team/quick_absence_form.html', {
        'form': form
    })