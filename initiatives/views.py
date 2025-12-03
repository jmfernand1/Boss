from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import date, timedelta
from .models import (
    Initiative, Quarter, Sprint, InitiativeUpdate, 
    InitiativeMetric, OperationalTask, InitiativeType,
    UserStory, Task
)
from team.models import Employee
from .forms import (
    InitiativeForm, QuarterForm, InitiativeTypeForm, SprintForm,
    OperationalTaskForm, InitiativeUpdateForm, InitiativeMetricForm,
    QuickInitiativeForm, UserStoryForm, TaskForm, QuickUserStoryForm, QuickTaskForm
)


@login_required
def initiatives_dashboard(request):
    """Dashboard principal del módulo de iniciativas"""
    # Obtener Q activo
    active_quarter = Quarter.objects.filter(is_active=True).first()
    
    if active_quarter:
        # Iniciativas del Q activo
        initiatives = Initiative.objects.filter(
            quarter=active_quarter
        ).select_related('owner', 'initiative_type')
        
        # Estadísticas
        stats = {
            'total': initiatives.count(),
            'in_progress': initiatives.filter(status='IN_PROGRESS').count(),
            'completed': initiatives.filter(status='COMPLETED').count(),
            'blocked': initiatives.filter(status='BLOCKED').count(),
            'operational': initiatives.filter(is_operational=True).count(),
            'avg_progress': initiatives.aggregate(Avg('progress'))['progress__avg'] or 0,
        }
        
        # Sprint activo
        active_sprint = Sprint.objects.filter(
            quarter=active_quarter,
            is_active=True
        ).first()
        
        # Actualizaciones recientes
        recent_updates = InitiativeUpdate.objects.filter(
            initiative__quarter=active_quarter
        ).select_related('initiative', 'created_by')[:10]
        
    else:
        initiatives = Initiative.objects.none()
        stats = {
            'total': 0,
            'in_progress': 0,
            'completed': 0,
            'blocked': 0,
            'operational': 0,
            'avg_progress': 0,
        }
        active_sprint = None
        recent_updates = []
    
    context = {
        'active_quarter': active_quarter,
        'initiatives': initiatives[:10],  # Últimas 10
        'stats': stats,
        'active_sprint': active_sprint,
        'recent_updates': recent_updates,
    }
    
    return render(request, 'initiatives/dashboard.html', context)


@login_required
def initiative_list(request):
    """Lista de iniciativas"""
    queryset = Initiative.objects.select_related('owner', 'initiative_type', 'quarter')
    
    # Filtros
    quarter_id = request.GET.get('quarter', '')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    owner_id = request.GET.get('owner', '')
    initiative_type_id = request.GET.get('type', '')
    search = request.GET.get('search', '')
    
    if quarter_id:
        queryset = queryset.filter(quarter_id=quarter_id)
    else:
        # Por defecto mostrar Q activo
        active_quarter = Quarter.objects.filter(is_active=True).first()
        if active_quarter:
            queryset = queryset.filter(quarter=active_quarter)
    
    if status:
        queryset = queryset.filter(status=status)
    
    if priority:
        queryset = queryset.filter(priority=priority)
    
    if owner_id:
        queryset = queryset.filter(owner_id=owner_id)
    
    if initiative_type_id:
        queryset = queryset.filter(initiative_type_id=initiative_type_id)
    
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Datos para filtros
    quarters = Quarter.objects.all().order_by('-year', '-quarter')
    employees = Employee.objects.filter(is_active=True).select_related('user')
    initiative_types = InitiativeType.objects.all()
    
    context = {
        'initiatives': queryset,
        'quarters': quarters,
        'employees': employees,
        'initiative_types': initiative_types,
        'status_choices': Initiative.STATUS_CHOICES,
        'priority_choices': Initiative.PRIORITY_CHOICES,
        'selected_quarter': quarter_id,
        'selected_status': status,
        'selected_priority': priority,
        'selected_owner': owner_id,
        'selected_type': initiative_type_id,
        'search': search,
        'today': date.today(),
    }
    
    return render(request, 'initiatives/initiative_list.html', context)


@login_required
def initiative_detail(request, pk):
    """Detalle de iniciativa"""
    initiative = get_object_or_404(Initiative, pk=pk)
    
    # Actualizaciones
    updates = initiative.updates.all().order_by('-created_at')
    
    # Métricas
    metrics = initiative.metrics.all().order_by('metric_name')
    
    # Historias de usuario
    user_stories = initiative.user_stories.all().select_related('assignee', 'sprint').order_by('-priority', '-created_at')
    
    # Estadísticas de historias de usuario
    story_stats = {
        'total': user_stories.count(),
        'backlog': user_stories.filter(status='BACKLOG').count(),
        'in_progress': user_stories.filter(status='IN_PROGRESS').count(),
        'done': user_stories.filter(status='DONE').count(),
        'total_story_points': sum(story.story_points or 0 for story in user_stories),
        'completed_story_points': sum(story.story_points or 0 for story in user_stories.filter(status='DONE')),
    }
    
    # Detalles operativos si aplica
    operational_details = None
    if initiative.is_operational:
        try:
            operational_details = initiative.operational_details
        except OperationalTask.DoesNotExist:
            pass
    
    context = {
        'initiative': initiative,
        'updates': updates,
        'metrics': metrics,
        'user_stories': user_stories,
        'story_stats': story_stats,
        'operational_details': operational_details,
        'today': date.today(),
    }
    
    return render(request, 'initiatives/initiative_detail.html', context)


@login_required
def operational_tasks(request):
    """Vista de tareas operativas"""
    tasks = OperationalTask.objects.select_related(
        'initiative', 'initiative__owner'
    ).order_by('frequency', 'initiative__title')
    
    # Filtros
    frequency = request.GET.get('frequency', '')
    owner_id = request.GET.get('owner', '')
    
    if frequency:
        tasks = tasks.filter(frequency=frequency)
    
    if owner_id:
        tasks = tasks.filter(initiative__owner_id=owner_id)
    
    # Agrupar por frecuencia
    tasks_by_frequency = {}
    for task in tasks:
        freq = task.get_frequency_display()
        if freq not in tasks_by_frequency:
            tasks_by_frequency[freq] = []
        tasks_by_frequency[freq].append(task)
    
    # Datos para filtros
    employees = Employee.objects.filter(is_active=True).select_related('user')
    
    context = {
        'tasks_by_frequency': tasks_by_frequency,
        'frequency_choices': OperationalTask.FREQUENCY_CHOICES,
        'employees': employees,
        'selected_frequency': frequency,
        'selected_owner': owner_id,
        'today': date.today(),
    }
    
    return render(request, 'initiatives/operational_tasks.html', context)


@login_required
def sprint_board(request):
    """Tablero de sprint (estilo Monday.com)"""
    # Obtener sprint seleccionado o activo
    selected_sprint_id = request.GET.get('sprint')
    if selected_sprint_id:
        active_sprint = get_object_or_404(Sprint, id=selected_sprint_id)
    else:
        active_sprint = Sprint.objects.filter(is_active=True).first()
    
    # Obtener todos los sprints para el dropdown
    sprints = Sprint.objects.select_related('quarter').order_by('-quarter__year', '-quarter__quarter', '-sprint_number')
    
    # Obtener tareas del sprint activo agrupadas por sprint
    tasks_by_sprint = {}
    if active_sprint:
        # Tareas del sprint activo
        tasks = Task.objects.filter(
            user_story__sprint=active_sprint
        ).select_related(
            'user_story__initiative', 
            'assignee__user', 
            'user_story__initiative__initiative_type'
        ).order_by('status', '-created_at')
        
        tasks_by_sprint[active_sprint] = tasks
        
        # Calcular estadísticas del sprint
        sprint_stats = {
            'total_tasks': tasks.count(),
            'done_tasks': tasks.filter(status='DONE').count(),
            'in_progress_tasks': tasks.filter(status='IN_PROGRESS').count(),
            'blocked_tasks': tasks.filter(status='BLOCKED').count(),
            'total_story_points': sum(task.user_story.story_points or 0 for task in tasks),
        }
        
        if sprint_stats['total_tasks'] > 0:
            sprint_stats['completion_percentage'] = round(
                (sprint_stats['done_tasks'] / sprint_stats['total_tasks']) * 100, 1
            )
        else:
            sprint_stats['completion_percentage'] = 0
    else:
        sprint_stats = {
            'total_tasks': 0,
            'done_tasks': 0,
            'in_progress_tasks': 0,
            'blocked_tasks': 0,
            'total_story_points': 0,
            'completion_percentage': 0,
        }
    
    # Datos para el modal de creación rápida
    employees = Employee.objects.filter(is_active=True).select_related('user')
    initiative_types = InitiativeType.objects.all()

    context = {
        'active_sprint': active_sprint,
        'tasks_by_sprint': tasks_by_sprint,
        'sprints': sprints,
        'sprint_stats': sprint_stats,
        'today': date.today(),
        'employees': employees,
        'initiative_types': initiative_types,
        'priority_choices': Initiative.PRIORITY_CHOICES,
        'task_status_choices': Task.STATUS_CHOICES,
        'task_type_choices': Task.TASK_TYPE_CHOICES,
    }
    
    return render(request, 'initiatives/sprint_board.html', context)


@login_required
def quarter_summary(request, pk=None):
    """Resumen del Quarter"""
    if pk:
        quarter = get_object_or_404(Quarter, pk=pk)
    else:
        quarter = Quarter.objects.filter(is_active=True).first()
    
    if quarter:
        # Iniciativas del quarter
        initiatives = Initiative.objects.filter(
            quarter=quarter
        ).select_related('owner', 'initiative_type')
        
        # Estadísticas por tipo
        stats_by_type = initiatives.values(
            'initiative_type__name'
        ).annotate(
            count=Count('id'),
            avg_progress=Avg('progress')
        )
        
        # Estadísticas por empleado
        stats_by_owner = initiatives.values(
            'owner__user__first_name',
            'owner__user__last_name'
        ).annotate(
            count=Count('id'),
            avg_progress=Avg('progress')
        )
        
        # Métricas agregadas
        total_metrics = InitiativeMetric.objects.filter(
            initiative__quarter=quarter
        ).count()
    else:
        initiatives = Initiative.objects.none()
        stats_by_type = []
        stats_by_owner = []
        total_metrics = 0
    
    # Todos los quarters para navegación
    quarters = Quarter.objects.all().order_by('-year', '-quarter')
    
    context = {
        'quarter': quarter,
        'quarters': quarters,
        'initiatives': initiatives,
        'stats_by_type': stats_by_type,
        'stats_by_owner': stats_by_owner,
        'total_metrics': total_metrics,
    }
    
    return render(request, 'initiatives/quarter_summary.html', context)


# ============================================================================
# VISTAS CRUD - INITIATIVES
# ============================================================================

@login_required
def initiative_create(request):
    """Crear nueva iniciativa"""
    if request.method == 'POST':
        form = InitiativeForm(request.POST)
        if form.is_valid():
            initiative = form.save()
            messages.success(request, f'Iniciativa "{initiative.title}" creada exitosamente.')
            return redirect('initiatives:initiative_detail', pk=initiative.pk)
    else:
        form = InitiativeForm()
        # Pre-seleccionar datos si vienen en query params
        quarter_id = request.GET.get('quarter')
        type_id = request.GET.get('type')
        owner_id = request.GET.get('owner')
        
        if quarter_id:
            try:
                form.fields['quarter'].initial = Quarter.objects.get(pk=quarter_id)
            except Quarter.DoesNotExist:
                pass
        
        if type_id:
            try:
                form.fields['initiative_type'].initial = InitiativeType.objects.get(pk=type_id)
            except InitiativeType.DoesNotExist:
                pass
                
        if owner_id:
            try:
                form.fields['owner'].initial = Employee.objects.get(pk=owner_id)
            except Employee.DoesNotExist:
                pass
    
    return render(request, 'initiatives/initiative_form.html', {
        'form': form,
        'title': 'Nueva Iniciativa',
        'action': 'create',
        'back_url': reverse('initiatives:initiative_list'),
        'icon': 'fas fa-plus'
    })


@login_required
def initiative_edit(request, pk):
    """Editar iniciativa existente"""
    initiative = get_object_or_404(Initiative, pk=pk)
    
    if request.method == 'POST':
        form = InitiativeForm(request.POST, instance=initiative)
        if form.is_valid():
            initiative = form.save()
            messages.success(request, f'Iniciativa "{initiative.title}" actualizada exitosamente.')
            return redirect('initiatives:initiative_detail', pk=initiative.pk)
    else:
        form = InitiativeForm(instance=initiative)
    
    return render(request, 'initiatives/initiative_form.html', {
        'form': form,
        'initiative': initiative,
        'title': f'Editar - {initiative.title}',
        'action': 'edit',
        'back_url': reverse('initiatives:initiative_detail', args=[initiative.pk]),
        'icon': 'fas fa-edit'
    })


@login_required
def initiative_delete(request, pk):
    """Eliminar iniciativa"""
    initiative = get_object_or_404(Initiative, pk=pk)
    
    if request.method == 'POST':
        # Validación de confirmación
        confirmation = request.POST.get('confirmation', '')
        understand = request.POST.get('understand', '')
        
        if confirmation == initiative.title and understand:
            initiative_title = initiative.title
            initiative.delete()
            messages.success(request, f'Iniciativa "{initiative_title}" eliminada exitosamente.')
            return redirect('initiatives:initiative_list')
        else:
            messages.error(request, 'La confirmación no coincide con el título de la iniciativa.')
    
    return render(request, 'initiatives/initiative_confirm_delete.html', {
        'initiative': initiative
    })


@login_required
def quick_initiative_create(request):
    """Crear iniciativa rápida desde el dashboard (AJAX)"""
    if request.method == 'POST':
        form = QuickInitiativeForm(request.POST)
        if form.is_valid():
            try:
                initiative = form.save()
                messages.success(request, f'Iniciativa "{initiative.title}" creada exitosamente.')
                return JsonResponse({
                    'success': True,
                    'message': f'Iniciativa "{initiative.title}" creada exitosamente.',
                    'initiative_id': initiative.pk,
                    'redirect_url': reverse('initiatives:initiative_detail', args=[initiative.pk])
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error en el formulario',
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


# ============================================================================
# VISTAS CRUD - QUARTERS
# ============================================================================

@login_required
def quarter_list(request):
    """Lista de quarters"""
    quarters = Quarter.objects.all().order_by('-year', '-quarter')
    
    # Estadísticas por quarter
    quarter_stats = []
    for quarter in quarters:
        initiatives = Initiative.objects.filter(quarter=quarter)
        quarter_stats.append({
            'quarter': quarter,
            'total_initiatives': initiatives.count(),
            'completed_initiatives': initiatives.filter(status='COMPLETED').count(),
            'avg_progress': initiatives.aggregate(Avg('progress'))['progress__avg'] or 0,
        })
    
    context = {
        'quarter_stats': quarter_stats,
    }
    
    return render(request, 'initiatives/quarter_list.html', context)


@login_required
def quarter_create(request):
    """Crear nuevo quarter"""
    if request.method == 'POST':
        form = QuarterForm(request.POST)
        if form.is_valid():
            quarter = form.save()
            messages.success(request, f'Periodo {quarter} creado exitosamente.')
            return redirect('initiatives:quarter_summary_detail', pk=quarter.pk)
    else:
        form = QuarterForm()
    
    return render(request, 'initiatives/quarter_form.html', {
        'form': form,
        'title': 'Nuevo Periodo (Q)',
        'action': 'create',
        'back_url': reverse('initiatives:quarter_list'),
        'icon': 'fas fa-calendar-plus'
    })


@login_required
def quarter_edit(request, pk):
    """Editar quarter existente"""
    quarter = get_object_or_404(Quarter, pk=pk)
    
    if request.method == 'POST':
        form = QuarterForm(request.POST, instance=quarter)
        if form.is_valid():
            quarter = form.save()
            messages.success(request, f'Periodo {quarter} actualizado exitosamente.')
            return redirect('initiatives:quarter_summary_detail', pk=quarter.pk)
    else:
        form = QuarterForm(instance=quarter)
    
    return render(request, 'initiatives/quarter_form.html', {
        'form': form,
        'quarter': quarter,
        'title': f'Editar - {quarter}',
        'action': 'edit',
        'back_url': reverse('initiatives:quarter_summary_detail', args=[quarter.pk]),
        'icon': 'fas fa-calendar-edit'
    })


@login_required
def quarter_delete(request, pk):
    """Eliminar quarter"""
    quarter = get_object_or_404(Quarter, pk=pk)
    
    # Verificar si el quarter tiene iniciativas
    initiatives_count = quarter.initiative_set.count()
    
    if request.method == 'POST':
        if initiatives_count > 0:
            messages.error(request, f'No se puede eliminar {quarter} porque tiene {initiatives_count} iniciativas asociadas.')
            return redirect('initiatives:quarter_list')
        
        quarter_name = str(quarter)
        quarter.delete()
        messages.success(request, f'Periodo {quarter_name} eliminado exitosamente.')
        return redirect('initiatives:quarter_list')
    
    return render(request, 'initiatives/quarter_confirm_delete.html', {
        'quarter': quarter,
        'initiatives_count': initiatives_count
    })


# ============================================================================
# VISTAS CRUD - INITIATIVE TYPES
# ============================================================================

@login_required
def initiative_type_list(request):
    """Lista de tipos de iniciativa"""
    initiative_types = InitiativeType.objects.all().order_by('category', 'name')
    
    # Añadir estadísticas de uso
    for initiative_type in initiative_types:
        initiative_type.total_initiatives = initiative_type.initiative_set.count()
        initiative_type.active_initiatives = initiative_type.initiative_set.filter(
            status__in=['PLANNED', 'IN_PROGRESS']
        ).count()
    
    context = {
        'initiative_types': initiative_types,
    }
    
    return render(request, 'initiatives/initiative_type_list.html', context)


@login_required
def initiative_type_create(request):
    """Crear nuevo tipo de iniciativa"""
    if request.method == 'POST':
        form = InitiativeTypeForm(request.POST)
        if form.is_valid():
            initiative_type = form.save()
            messages.success(request, f'Tipo de iniciativa "{initiative_type.name}" creado exitosamente.')
            return redirect('initiatives:initiative_type_list')
    else:
        form = InitiativeTypeForm()
    
    return render(request, 'initiatives/initiative_type_form.html', {
        'form': form,
        'title': 'Nuevo Tipo de Iniciativa',
        'action': 'create',
        'back_url': reverse('initiatives:initiative_type_list'),
        'icon': 'fas fa-tag'
    })


@login_required
def initiative_type_edit(request, pk):
    """Editar tipo de iniciativa"""
    initiative_type = get_object_or_404(InitiativeType, pk=pk)
    
    if request.method == 'POST':
        form = InitiativeTypeForm(request.POST, instance=initiative_type)
        if form.is_valid():
            initiative_type = form.save()
            messages.success(request, f'Tipo de iniciativa "{initiative_type.name}" actualizado exitosamente.')
            return redirect('initiatives:initiative_type_list')
    else:
        form = InitiativeTypeForm(instance=initiative_type)
    
    return render(request, 'initiatives/initiative_type_form.html', {
        'form': form,
        'initiative_type': initiative_type,
        'title': f'Editar - {initiative_type.name}',
        'action': 'edit',
        'back_url': reverse('initiatives:initiative_type_list'),
        'icon': 'fas fa-edit'
    })


@login_required
def initiative_type_delete(request, pk):
    """Eliminar tipo de iniciativa"""
    initiative_type = get_object_or_404(InitiativeType, pk=pk)
    
    # Verificar si el tipo está siendo usado
    initiatives_count = initiative_type.initiative_set.count()
    
    if request.method == 'POST':
        if initiatives_count > 0:
            messages.error(request, f'No se puede eliminar "{initiative_type.name}" porque está siendo usado en {initiatives_count} iniciativas.')
            return redirect('initiatives:initiative_type_list')
        
        type_name = initiative_type.name
        initiative_type.delete()
        messages.success(request, f'Tipo de iniciativa "{type_name}" eliminado exitosamente.')
        return redirect('initiatives:initiative_type_list')
    
    return render(request, 'initiatives/initiative_type_confirm_delete.html', {
        'initiative_type': initiative_type,
        'initiatives_count': initiatives_count
    })


# ============================================================================
# VISTAS CRUD - SPRINTS
# ============================================================================

@login_required
def sprint_list(request):
    """Lista de sprints"""
    sprints = Sprint.objects.select_related('quarter').order_by('-quarter__year', '-quarter__quarter', '-sprint_number')
    
    # Añadir estadísticas por sprint
    for sprint in sprints:
        if sprint.quarter:
            initiatives = Initiative.objects.filter(quarter=sprint.quarter)
            sprint.total_initiatives = initiatives.count()
            sprint.completed_initiatives = initiatives.filter(status='COMPLETED').count()
    
    context = {
        'sprints': sprints,
        'today': date.today(),
    }
    
    return render(request, 'initiatives/sprint_list.html', context)


@login_required
def sprint_create(request):
    """Crear nuevo sprint"""
    if request.method == 'POST':
        form = SprintForm(request.POST)
        if form.is_valid():
            sprint = form.save()
            messages.success(request, f'Sprint "{sprint.name}" creado exitosamente.')
            return redirect('initiatives:sprint_board')
    else:
        form = SprintForm()
    
    return render(request, 'initiatives/sprint_form.html', {
        'form': form,
        'title': 'Nuevo Sprint',
        'action': 'create',
        'back_url': reverse('initiatives:sprint_list'),
        'icon': 'fas fa-running'
    })


@login_required
def sprint_edit(request, pk):
    """Editar sprint"""
    sprint = get_object_or_404(Sprint, pk=pk)
    
    if request.method == 'POST':
        form = SprintForm(request.POST, instance=sprint)
        if form.is_valid():
            sprint = form.save()
            messages.success(request, f'Sprint "{sprint.name}" actualizado exitosamente.')
            return redirect('initiatives:sprint_board')
    else:
        form = SprintForm(instance=sprint)
    
    return render(request, 'initiatives/sprint_form.html', {
        'form': form,
        'sprint': sprint,
        'title': f'Editar - {sprint.name}',
        'action': 'edit',
        'back_url': reverse('initiatives:sprint_board'),
        'icon': 'fas fa-edit'
    })


@login_required
def sprint_delete(request, pk):
    """Eliminar sprint"""
    sprint = get_object_or_404(Sprint, pk=pk)
    
    if request.method == 'POST':
        sprint_name = sprint.name
        sprint.delete()
        messages.success(request, f'Sprint "{sprint_name}" eliminado exitosamente.')
        return redirect('initiatives:sprint_list')
    
    return render(request, 'initiatives/sprint_confirm_delete.html', {
        'sprint': sprint
    })


# ============================================================================
# VISTAS CRUD - INITIATIVE UPDATES
# ============================================================================

@login_required
def initiative_update_create(request, initiative_pk):
    """Crear nueva actualización de iniciativa"""
    initiative = get_object_or_404(Initiative, pk=initiative_pk)
    
    if request.method == 'POST':
        form = InitiativeUpdateForm(request.POST, initiative=initiative)
        if form.is_valid():
            update = form.save(commit=False)
            update.created_by = request.user
            update.save()
            messages.success(request, 'Actualización agregada exitosamente.')
            return redirect('initiatives:initiative_detail', pk=initiative.pk)
    else:
        form = InitiativeUpdateForm(initiative=initiative)
    
    return render(request, 'initiatives/initiative_update_form.html', {
        'form': form,
        'initiative': initiative,
        'title': f'Nueva Actualización - {initiative.title}',
        'action': 'create',
        'back_url': reverse('initiatives:initiative_detail', args=[initiative.pk])
    })


@login_required
def initiative_update_edit(request, pk):
    """Editar actualización de iniciativa"""
    update = get_object_or_404(InitiativeUpdate, pk=pk)
    
    if request.method == 'POST':
        form = InitiativeUpdateForm(request.POST, instance=update)
        if form.is_valid():
            update = form.save()
            messages.success(request, 'Actualización modificada exitosamente.')
            return redirect('initiatives:initiative_detail', pk=update.initiative.pk)
    else:
        form = InitiativeUpdateForm(instance=update)
    
    return render(request, 'initiatives/initiative_update_form.html', {
        'form': form,
        'update': update,
        'initiative': update.initiative,
        'title': f'Editar Actualización - {update.title}',
        'action': 'edit',
        'back_url': reverse('initiatives:initiative_detail', args=[update.initiative.pk])
    })


@login_required
def initiative_update_delete(request, pk):
    """Eliminar actualización de iniciativa"""
    update = get_object_or_404(InitiativeUpdate, pk=pk)
    initiative = update.initiative
    
    if request.method == 'POST':
        update_title = update.title
        update.delete()
        messages.success(request, f'Actualización "{update_title}" eliminada exitosamente.')
        return redirect('initiatives:initiative_detail', pk=initiative.pk)
    
    return render(request, 'initiatives/initiative_update_confirm_delete.html', {
        'update': update,
        'initiative': initiative
    })


# ============================================================================
# VISTAS CRUD - INITIATIVE METRICS
# ============================================================================

@login_required
def initiative_metric_create(request, initiative_pk):
    """Crear nueva métrica de iniciativa"""
    initiative = get_object_or_404(Initiative, pk=initiative_pk)
    
    if request.method == 'POST':
        form = InitiativeMetricForm(request.POST, initiative=initiative)
        if form.is_valid():
            metric = form.save()
            messages.success(request, f'Métrica "{metric.metric_name}" agregada exitosamente.')
            return redirect('initiatives:initiative_detail', pk=initiative.pk)
    else:
        form = InitiativeMetricForm(initiative=initiative)
    
    return render(request, 'initiatives/initiative_metric_form.html', {
        'form': form,
        'initiative': initiative,
        'title': f'Nueva Métrica - {initiative.title}',
        'action': 'create',
        'back_url': reverse('initiatives:initiative_detail', args=[initiative.pk])
    })


@login_required
def initiative_metric_edit(request, pk):
    """Editar métrica de iniciativa"""
    metric = get_object_or_404(InitiativeMetric, pk=pk)
    
    if request.method == 'POST':
        form = InitiativeMetricForm(request.POST, instance=metric)
        if form.is_valid():
            metric = form.save()
            messages.success(request, f'Métrica "{metric.metric_name}" actualizada exitosamente.')
            return redirect('initiatives:initiative_detail', pk=metric.initiative.pk)
    else:
        form = InitiativeMetricForm(instance=metric)
    
    return render(request, 'initiatives/initiative_metric_form.html', {
        'form': form,
        'metric': metric,
        'initiative': metric.initiative,
        'title': f'Editar Métrica - {metric.metric_name}',
        'action': 'edit',
        'back_url': reverse('initiatives:initiative_detail', args=[metric.initiative.pk])
    })


@login_required
def initiative_metric_delete(request, pk):
    """Eliminar métrica de iniciativa"""
    metric = get_object_or_404(InitiativeMetric, pk=pk)
    initiative = metric.initiative
    
    if request.method == 'POST':
        metric_name = metric.metric_name
        metric.delete()
        messages.success(request, f'Métrica "{metric_name}" eliminada exitosamente.')
        return redirect('initiatives:initiative_detail', pk=initiative.pk)
    
    return render(request, 'initiatives/initiative_metric_confirm_delete.html', {
        'metric': metric,
        'initiative': initiative
    })


# ============================================================================
# VISTAS CRUD - OPERATIONAL TASKS
# ============================================================================

@login_required
def operational_task_create(request):
    """Crear nueva tarea operativa"""
    
    if request.method == 'POST':
        form = OperationalTaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Tarea operativa para "{task.initiative.title}" creada exitosamente.')
            return redirect('initiatives:operational_tasks')
    else:
        form = OperationalTaskForm()
        
        # Pre-seleccionar iniciativa si viene en query params
        initiative_id = request.GET.get('initiative')
        if initiative_id:
            try:
                form.fields['initiative'].initial = Initiative.objects.get(pk=initiative_id, is_operational=True)
            except Initiative.DoesNotExist:
                pass
    
    # Verificar que hay iniciativas operativas disponibles
    operational_count = Initiative.objects.filter(is_operational=True).count()
    if operational_count == 0:
        messages.warning(request, 'No hay iniciativas operativas disponibles. Debe crear una iniciativa y marcarla como operativa.')
    
    return render(request, 'initiatives/operational_task_form.html', {
        'form': form,
        'title': 'Nueva Tarea Operativa',
        'action': 'create',
        'back_url': reverse('initiatives:operational_tasks'),
    })


@login_required
def operational_task_edit(request, pk):
    """Editar tarea operativa"""
    task = get_object_or_404(OperationalTask, pk=pk)
    
    if request.method == 'POST':
        form = OperationalTaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Tarea operativa actualizada exitosamente.')
            return redirect('initiatives:operational_tasks')
    else:
        form = OperationalTaskForm(instance=task)
    
    return render(request, 'initiatives/operational_task_form.html', {
        'form': form,
        'task': task,
        'title': f'Editar Tarea - {task.initiative.title}',
        'action': 'edit',
        'back_url': reverse('initiatives:operational_tasks')
    })


@login_required
def operational_task_delete(request, pk):
    """Eliminar tarea operativa"""
    task = get_object_or_404(OperationalTask, pk=pk)
    
    if request.method == 'POST':
        initiative_title = task.initiative.title
        task.delete()
        messages.success(request, f'Tarea operativa de "{initiative_title}" eliminada exitosamente.')
        return redirect('initiatives:operational_tasks')
    
    return render(request, 'initiatives/operational_task_confirm_delete.html', {
        'task': task
    })


@login_required
@require_http_methods(["POST"])
def operational_task_mark_executed(request, pk):
    """Marcar tarea operativa como ejecutada (AJAX)"""
    task = get_object_or_404(OperationalTask, pk=pk)
    
    # Actualizar última ejecución
    from datetime import datetime
    task.last_execution = datetime.now()
    task.next_execution = task.calculate_next_execution()
    task.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Tarea de "{task.initiative.title}" marcada como ejecutada.',
        'last_execution': task.last_execution.strftime('%d/%m/%Y %H:%M') if task.last_execution else None,
        'next_execution': task.next_execution.strftime('%d/%m/%Y %H:%M') if task.next_execution else None
    })


# ============================================================================
# VISTAS AUXILIARES
# ============================================================================

@login_required
@require_http_methods(["POST"])
def initiative_change_status(request, pk):
    """Cambiar estado de iniciativa (AJAX para Kanban)"""
    initiative = get_object_or_404(Initiative, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(Initiative.STATUS_CHOICES):
        old_status = initiative.get_status_display()
        initiative.status = new_status
        
        # Auto-completar fecha si se marca como completado
        if new_status == 'COMPLETED' and not initiative.completion_date:
            initiative.completion_date = date.today()
            initiative.progress = 100
        elif new_status != 'COMPLETED':
            initiative.completion_date = None
        
        initiative.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Estado cambiado de "{old_status}" a "{initiative.get_status_display()}"',
            'new_status': initiative.get_status_display(),
            'progress': initiative.progress
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Estado no válido'
    })


# ============================================================================
# VISTAS CRUD - USER STORIES
# ============================================================================

@login_required
def user_story_create(request, initiative_pk):
    """Crear nueva historia de usuario"""
    initiative = get_object_or_404(Initiative, pk=initiative_pk)
    
    if request.method == 'POST':
        form = UserStoryForm(request.POST, initiative=initiative)
        if form.is_valid():
            user_story = form.save()
            messages.success(request, f'Historia de usuario "{user_story.title}" creada exitosamente.')
            return redirect('initiatives:initiative_detail', pk=initiative.pk)
    else:
        form = UserStoryForm(initiative=initiative)
    
    return render(request, 'initiatives/user_story_form.html', {
        'form': form,
        'initiative': initiative,
        'title': f'Nueva Historia de Usuario - {initiative.title}',
        'action': 'create',
        'back_url': reverse('initiatives:initiative_detail', args=[initiative.pk])
    })


@login_required
def user_story_detail(request, pk):
    """Detalle de historia de usuario"""
    user_story = get_object_or_404(UserStory, pk=pk)
    
    # Tareas de la historia
    tasks = user_story.tasks.all().select_related('assignee').order_by('status', '-created_at')
    
    # Estadísticas de tareas
    task_stats = {
        'total': tasks.count(),
        'todo': tasks.filter(status='TODO').count(),
        'in_progress': tasks.filter(status='IN_PROGRESS').count(),
        'done': tasks.filter(status='DONE').count(),
        'blocked': tasks.filter(status='BLOCKED').count(),
        'total_estimated': sum(task.estimated_hours or 0 for task in tasks),
        'total_actual': sum(task.actual_hours or 0 for task in tasks),
    }
    
    context = {
        'user_story': user_story,
        'tasks': tasks,
        'task_stats': task_stats,
        'today': date.today(),
    }
    
    return render(request, 'initiatives/user_story_detail.html', context)


@login_required
def user_story_edit(request, pk):
    """Editar historia de usuario"""
    user_story = get_object_or_404(UserStory, pk=pk)
    
    if request.method == 'POST':
        form = UserStoryForm(request.POST, instance=user_story)
        if form.is_valid():
            user_story = form.save()
            messages.success(request, f'Historia de usuario "{user_story.title}" actualizada exitosamente.')
            return redirect('initiatives:user_story_detail', pk=user_story.pk)
    else:
        form = UserStoryForm(instance=user_story)
    
    return render(request, 'initiatives/user_story_form.html', {
        'form': form,
        'user_story': user_story,
        'initiative': user_story.initiative,
        'title': f'Editar - {user_story.title}',
        'action': 'edit',
        'back_url': reverse('initiatives:user_story_detail', args=[user_story.pk])
    })


@login_required
def user_story_delete(request, pk):
    """Eliminar historia de usuario"""
    user_story = get_object_or_404(UserStory, pk=pk)
    initiative = user_story.initiative
    
    if request.method == 'POST':
        story_title = user_story.title
        user_story.delete()
        messages.success(request, f'Historia de usuario "{story_title}" eliminada exitosamente.')
        return redirect('initiatives:initiative_detail', pk=initiative.pk)
    
    return render(request, 'initiatives/user_story_confirm_delete.html', {
        'user_story': user_story,
        'initiative': initiative
    })


@login_required
def quick_user_story_create(request):
    """Crear historia de usuario rápida (AJAX)"""
    if request.method == 'POST':
        initiative_id = request.POST.get('initiative_id')
        initiative = get_object_or_404(Initiative, pk=initiative_id)
        
        form = QuickUserStoryForm(request.POST)
        if form.is_valid():
            try:
                user_story = form.save(initiative)
                messages.success(request, f'Historia de usuario "{user_story.title}" creada exitosamente.')
                return JsonResponse({
                    'success': True,
                    'message': f'Historia de usuario "{user_story.title}" creada exitosamente.',
                    'user_story_id': user_story.pk,
                    'redirect_url': reverse('initiatives:user_story_detail', args=[user_story.pk])
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error en el formulario',
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@require_http_methods(["POST"])
def user_story_change_status(request, pk):
    """Cambiar estado de historia de usuario (AJAX)"""
    user_story = get_object_or_404(UserStory, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(UserStory.STATUS_CHOICES):
        old_status = user_story.get_status_display()
        user_story.status = new_status
        user_story.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Estado cambiado de "{old_status}" a "{user_story.get_status_display()}"',
            'new_status': user_story.get_status_display(),
            'progress': user_story.progress_percentage
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Estado no válido'
    })


# ============================================================================
# VISTAS CRUD - TASKS
# ============================================================================

@login_required
def task_create(request, story_pk):
    """Crear nueva tarea"""
    user_story = get_object_or_404(UserStory, pk=story_pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, user_story=user_story)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Tarea "{task.title}" creada exitosamente.')
            return redirect('initiatives:user_story_detail', pk=user_story.pk)
    else:
        form = TaskForm(user_story=user_story)
    
    return render(request, 'initiatives/task_form.html', {
        'form': form,
        'user_story': user_story,
        'title': f'Nueva Tarea - {user_story.title}',
        'action': 'create',
        'back_url': reverse('initiatives:user_story_detail', args=[user_story.pk])
    })


@login_required
def task_detail(request, pk):
    """Detalle de tarea"""
    task = get_object_or_404(Task, pk=pk)
    
    # Estadísticas de la historia de usuario
    user_story = task.user_story
    total_tasks = user_story.tasks.count()
    completed_tasks = user_story.tasks.filter(status='DONE').count()
    
    context = {
        'task': task,
        'user_story': user_story,
        'initiative': user_story.initiative,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'today': date.today(),
    }
    
    return render(request, 'initiatives/task_detail.html', context)


@login_required
def task_edit(request, pk):
    """Editar tarea"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Tarea "{task.title}" actualizada exitosamente.')
            return redirect('initiatives:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'initiatives/task_form.html', {
        'form': form,
        'task': task,
        'user_story': task.user_story,
        'title': f'Editar - {task.title}',
        'action': 'edit',
        'back_url': reverse('initiatives:task_detail', args=[task.pk])
    })


@login_required
def task_delete(request, pk):
    """Eliminar tarea"""
    task = get_object_or_404(Task, pk=pk)
    user_story = task.user_story
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Tarea "{task_title}" eliminada exitosamente.')
        return redirect('initiatives:user_story_detail', pk=user_story.pk)
    
    return render(request, 'initiatives/task_confirm_delete.html', {
        'task': task,
        'user_story': user_story
    })


@login_required
def quick_task_create(request):
    """Crear tarea rápida (AJAX)"""
    if request.method == 'POST':
        story_id = request.POST.get('user_story_id')
        user_story = get_object_or_404(UserStory, pk=story_id)
        
        form = QuickTaskForm(request.POST)
        if form.is_valid():
            try:
                task = form.save(user_story)
                messages.success(request, f'Tarea "{task.title}" creada exitosamente.')
                return JsonResponse({
                    'success': True,
                    'message': f'Tarea "{task.title}" creada exitosamente.',
                    'task_id': task.pk,
                    'redirect_url': reverse('initiatives:task_detail', args=[task.pk])
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error en el formulario',
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@require_http_methods(["POST"])
def task_change_status(request, pk):
    """Cambiar estado de tarea (AJAX)"""
    task = get_object_or_404(Task, pk=pk)
    new_status = request.POST.get('status')
    
    if new_status in dict(Task.STATUS_CHOICES):
        old_status = task.get_status_display()
        task.status = new_status
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Estado cambiado de "{old_status}" a "{task.get_status_display()}"',
            'new_status': task.get_status_display()
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Estado no válido'
    })