from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    # Dashboard y vistas principales
    path('', views.team_dashboard, name='dashboard'),
    path('dashboard/', views.team_dashboard, name='team_dashboard'),
    
    # Empleados
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    
    # Ausencias
    path('absences/', views.absence_list, name='absence_list'),
    path('absences/create/', views.absence_create, name='absence_create'),
    path('absences/<int:pk>/edit/', views.absence_edit, name='absence_edit'),
    path('absences/<int:pk>/delete/', views.absence_delete, name='absence_delete'),
    path('absences/quick/', views.quick_absence, name='quick_absence'),
    
    # Vacaciones
    path('vacations/', views.vacation_summary, name='vacation_summary'),
    path('vacations/create/', views.vacation_create, name='vacation_create'),
    path('vacations/<int:pk>/edit/', views.vacation_edit, name='vacation_edit'),
    path('vacations/<int:pk>/delete/', views.vacation_delete, name='vacation_delete'),
    
    # Tipos de ausencia
    path('absence-types/', views.absence_type_list, name='absence_type_list'),
    path('absence-types/create/', views.absence_type_create, name='absence_type_create'),
    path('absence-types/<int:pk>/edit/', views.absence_type_edit, name='absence_type_edit'),
    path('absence-types/<int:pk>/delete/', views.absence_type_delete, name='absence_type_delete'),
    
    # Cumpleaños
    path('birthdays/', views.birthday_calendar, name='birthday_calendar'),
]
