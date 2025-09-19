#!/usr/bin/env python
"""Script para crear datos iniciales de ejemplo"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boss_core.settings')
django.setup()

from django.contrib.auth.models import User
from team.models import Employee, AbsenceType, Absence, Vacation
from initiatives.models import Quarter, InitiativeType, Initiative, Sprint

def create_initial_data():
    print("Creando datos iniciales...")
    
    # Crear superusuario
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@boss.com',
            password='admin123',
            first_name='Admin',
            last_name='Sistema'
        )
        print("✓ Superusuario creado: admin / admin123")
    else:
        admin = User.objects.get(username='admin')
        print("✓ Superusuario ya existe")
    
    # Crear tipos de ausencia
    absence_types = [
        {'name': 'Vacaciones', 'code': 'VAC', 'requires_approval': True, 'paid': True, 'color': '#3498db'},
        {'name': 'Enfermedad', 'code': 'ENF', 'requires_approval': False, 'paid': True, 'color': '#e74c3c'},
        {'name': 'Permiso Personal', 'code': 'PER', 'requires_approval': True, 'paid': True, 'color': '#f39c12'},
        {'name': 'Capacitación', 'code': 'CAP', 'requires_approval': True, 'paid': True, 'color': '#27ae60'},
        {'name': 'Home Office', 'code': 'HO', 'requires_approval': False, 'paid': True, 'color': '#9b59b6'},
    ]
    
    for at in absence_types:
        AbsenceType.objects.get_or_create(code=at['code'], defaults=at)
    print("✓ Tipos de ausencia creados")
    
    # Crear algunos empleados de ejemplo
    employees_data = [
        {
            'username': 'jperez',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan.perez@empresa.com',
            'employee_id': 'EMP001',
            'position': 'Desarrollador Senior',
            'department': 'Tecnología',
            'birth_date': date(1990, 3, 15),
            'hire_date': date(2020, 1, 15)
        },
        {
            'username': 'mgarcia',
            'first_name': 'María',
            'last_name': 'García',
            'email': 'maria.garcia@empresa.com',
            'employee_id': 'EMP002',
            'position': 'Scrum Master',
            'department': 'Tecnología',
            'birth_date': date(1988, 7, 22),
            'hire_date': date(2019, 6, 1)
        },
        {
            'username': 'clopez',
            'first_name': 'Carlos',
            'last_name': 'López',
            'email': 'carlos.lopez@empresa.com',
            'employee_id': 'EMP003',
            'position': 'Product Owner',
            'department': 'Producto',
            'birth_date': date(1985, 11, 10),
            'hire_date': date(2021, 3, 1)
        },
        {
            'username': 'amartinez',
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'email': 'ana.martinez@empresa.com',
            'employee_id': 'EMP004',
            'position': 'UX Designer',
            'department': 'Diseño',
            'birth_date': date(1992, 9, 5),
            'hire_date': date(2022, 2, 15)
        }
    ]
    
    created_employees = []
    for emp_data in employees_data:
        user_data = {k: emp_data[k] for k in ['username', 'first_name', 'last_name', 'email']}
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={**user_data, 'password': 'pbkdf2_sha256$720000$salt$hash'}  # Contraseña no utilizable
        )
        
        if created:
            user.set_password('password123')
            user.save()
        
        employee_data = {k: emp_data[k] for k in ['employee_id', 'position', 'department', 'birth_date', 'hire_date']}
        employee, _ = Employee.objects.get_or_create(
            user=user,
            defaults=employee_data
        )
        created_employees.append(employee)
    
    print("✓ Empleados de ejemplo creados")
    
    # Crear registros de vacaciones para el año actual
    current_year = date.today().year
    for emp in created_employees:
        Vacation.objects.get_or_create(
            employee=emp,
            year=current_year,
            defaults={
                'days_entitled': 15,
                'days_taken': 5,
                'days_pending': 10
            }
        )
    print("✓ Registros de vacaciones creados")
    
    # Crear Quarter actual
    current_quarter = (date.today().month - 1) // 3 + 1
    quarter, _ = Quarter.objects.get_or_create(
        year=current_year,
        quarter=current_quarter,
        defaults={
            'is_active': True
        }
    )
    print(f"✓ Quarter activo creado: Q{current_quarter} {current_year}")
    
    # Crear tipos de iniciativas
    initiative_types = [
        {'name': 'Nueva Funcionalidad', 'category': 'PROJECT', 'color': '#3498db'},
        {'name': 'Mejora Técnica', 'category': 'IMPROVEMENT', 'color': '#27ae60'},
        {'name': 'Soporte', 'category': 'SUPPORT', 'color': '#e74c3c'},
        {'name': 'Proceso Recurrente', 'category': 'OPERATIONAL', 'color': '#f39c12'},
        {'name': 'Investigación', 'category': 'INITIATIVE', 'color': '#9b59b6'},
    ]
    
    for it in initiative_types:
        InitiativeType.objects.get_or_create(name=it['name'], defaults=it)
    print("✓ Tipos de iniciativas creados")
    
    # Crear Sprint actual
    sprint, _ = Sprint.objects.get_or_create(
        quarter=quarter,
        sprint_number=1,
        defaults={
            'name': f'Sprint {current_quarter}.1',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=14),
            'goal': 'Establecer las bases del sistema de gestión',
            'is_active': True
        }
    )
    print("✓ Sprint activo creado")
    
    # Crear algunas iniciativas de ejemplo
    if created_employees:
        initiatives_data = [
            {
                'title': 'Implementar módulo de reportes',
                'description': 'Crear reportes ejecutivos para el dashboard',
                'initiative_type': InitiativeType.objects.get(name='Nueva Funcionalidad'),
                'owner': created_employees[0],
                'status': 'IN_PROGRESS',
                'priority': 'HIGH',
                'progress': 35
            },
            {
                'title': 'Actualización mensual de métricas',
                'description': 'Proceso recurrente de actualización de KPIs',
                'initiative_type': InitiativeType.objects.get(name='Proceso Recurrente'),
                'owner': created_employees[1],
                'status': 'IN_PROGRESS',
                'priority': 'MEDIUM',
                'progress': 60,
                'is_operational': True
            },
            {
                'title': 'Migración a cloud',
                'description': 'Migrar infraestructura actual a AWS',
                'initiative_type': InitiativeType.objects.get(name='Mejora Técnica'),
                'owner': created_employees[0],
                'status': 'PLANNED',
                'priority': 'HIGH',
                'progress': 0
            }
        ]
        
        for init_data in initiatives_data:
            Initiative.objects.get_or_create(
                title=init_data['title'],
                quarter=quarter,
                defaults=init_data
            )
        print("✓ Iniciativas de ejemplo creadas")
    
    print("\n¡Datos iniciales creados exitosamente!")
    print("\nPuedes acceder al sistema con:")
    print("- Usuario administrador: admin / admin123")
    print("- Usuarios de ejemplo: jperez, mgarcia, clopez, amartinez (contraseña: password123)")

if __name__ == '__main__':
    create_initial_data()
