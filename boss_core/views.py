from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from team.models import Employee, Absence, Birthday
from initiatives.models import Initiative, Quarter, InitiativeUpdate


@login_required
def home(request):
    """Vista principal del dashboard"""
    # Obtener datos del usuario actual
    try:
        current_employee = request.user.employee_profile
    except:
        current_employee = None
    
    # Quarter activo
    active_quarter = Quarter.objects.filter(is_active=True).first()
    
    # Estadísticas rápidas
    stats = {
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'current_absences': Absence.objects.filter(
            start_date__lte=date.today(),
            end_date__gte=date.today()
        ).count(),
    }
    
    if active_quarter:
        initiatives = Initiative.objects.filter(quarter=active_quarter)
        stats.update({
            'total_initiatives': initiatives.count(),
            'initiatives_in_progress': initiatives.filter(status='IN_PROGRESS').count(),
            'initiatives_blocked': initiatives.filter(status='BLOCKED').count(),
        })
    else:
        stats.update({
            'total_initiatives': 0,
            'initiatives_in_progress': 0,
            'initiatives_blocked': 0,
        })
    
    # Próximos cumpleaños (7 días)
    upcoming_birthdays = Birthday.get_upcoming_birthdays(days=7)[:5]
    
    # Actualizaciones recientes
    recent_updates = InitiativeUpdate.objects.select_related(
        'initiative', 'created_by'
    ).order_by('-created_at')[:5]
    
    # Mis iniciativas (si es empleado)
    my_initiatives = []
    if current_employee:
        my_initiatives = Initiative.objects.filter(
            owner=current_employee,
            status__in=['IN_PROGRESS', 'BLOCKED']
        ).select_related('initiative_type')[:5]
    
    context = {
        'current_employee': current_employee,
        'active_quarter': active_quarter,
        'stats': stats,
        'upcoming_birthdays': upcoming_birthdays,
        'recent_updates': recent_updates,
        'my_initiatives': my_initiatives,
    }
    
    return render(request, 'home.html', context)
