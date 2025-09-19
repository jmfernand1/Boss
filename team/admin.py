from django.contrib import admin
from .models import Employee, AbsenceType, Absence, Vacation


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'position', 'department', 'hire_date', 'is_active']
    list_filter = ['is_active', 'department', 'hire_date']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id', 'position']
    date_hierarchy = 'hire_date'
    ordering = ['user__first_name', 'user__last_name']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'employee_id', 'is_active')
        }),
        ('Información Personal', {
            'fields': ('birth_date', 'phone', 'mobile')
        }),
        ('Información Laboral', {
            'fields': ('position', 'department', 'hire_date')
        }),
        ('Contacto de Emergencia', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )


@admin.register(AbsenceType)
class AbsenceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'requires_approval', 'paid', 'color']
    list_filter = ['requires_approval', 'paid']
    search_fields = ['name', 'code']


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'absence_type', 'start_date', 'end_date', 'duration_days']
    list_filter = ['absence_type', 'start_date', 'employee']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'reason']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    
    fieldsets = (
        ('Información General', {
            'fields': ('employee', 'absence_type')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date')
        }),
        ('Detalles', {
            'fields': ('reason', 'notes')
        }),
    )


@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'year', 'days_entitled', 'days_taken', 'days_pending']
    list_filter = ['year', 'employee__department']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    ordering = ['-year', 'employee']
    
    fieldsets = (
        ('Información General', {
            'fields': ('employee', 'year')
        }),
        ('Días', {
            'fields': ('days_entitled', 'days_taken'),
            'description': 'Los días pendientes se calculan automáticamente'
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['days_pending']