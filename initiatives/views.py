from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from datetime import date, timedelta
from .models import (
    Initiative, Quarter, Sprint, InitiativeUpdate, 
    InitiativeMetric, OperationalTask, InitiativeType
)
from team.models import Employee


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
        'operational_details': operational_details,
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
    }
    
    return render(request, 'initiatives/operational_tasks.html', context)


@login_required
def sprint_board(request):
    """Tablero de sprint (estilo Kanban)"""
    # Obtener sprint activo
    active_sprint = Sprint.objects.filter(is_active=True).first()
    
    if active_sprint:
        # Iniciativas del sprint agrupadas por estado
        initiatives_by_status = {}
        for status_code, status_name in Initiative.STATUS_CHOICES:
            initiatives = Initiative.objects.filter(
                quarter=active_sprint.quarter,
                status=status_code
            ).select_related('owner', 'initiative_type')
            initiatives_by_status[status_name] = initiatives
    else:
        initiatives_by_status = {}
    
    # Todos los sprints para navegación
    sprints = Sprint.objects.all().order_by('-quarter', '-sprint_number')
    
    context = {
        'active_sprint': active_sprint,
        'initiatives_by_status': initiatives_by_status,
        'sprints': sprints,
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