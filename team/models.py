from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date


class Employee(models.Model):
    """Modelo para la información básica de los empleados del equipo"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True, verbose_name='ID de Empleado')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    mobile = models.CharField(max_length=20, blank=True, verbose_name='Móvil')
    birth_date = models.DateField(verbose_name='Fecha de Nacimiento')
    hire_date = models.DateField(verbose_name='Fecha de Ingreso')
    position = models.CharField(max_length=100, verbose_name='Cargo')
    department = models.CharField(max_length=100, verbose_name='Departamento')
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name='Contacto de Emergencia')
    emergency_phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono de Emergencia')
    notes = models.TextField(blank=True, verbose_name='Notas')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    @property
    def years_of_service(self):
        today = date.today()
        return today.year - self.hire_date.year - ((today.month, today.day) < (self.hire_date.month, self.hire_date.day))


class AbsenceType(models.Model):
    """Tipos de ausencias"""
    name = models.CharField(max_length=50, verbose_name='Tipo de Ausencia')
    code = models.CharField(max_length=10, unique=True, verbose_name='Código')
    requires_approval = models.BooleanField(default=False, verbose_name='Requiere Aprobación')
    paid = models.BooleanField(default=True, verbose_name='Con Goce de Sueldo')
    color = models.CharField(max_length=7, default='#3498db', verbose_name='Color (HEX)')
    
    class Meta:
        verbose_name = 'Tipo de Ausencia'
        verbose_name_plural = 'Tipos de Ausencia'
        ordering = ['name']

    def __str__(self):
        return self.name


class Absence(models.Model):
    """Modelo para registrar ausencias"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='absences', verbose_name='Empleado')
    absence_type = models.ForeignKey(AbsenceType, on_delete=models.PROTECT, verbose_name='Tipo de Ausencia')
    start_date = models.DateField(verbose_name='Fecha de Inicio')
    end_date = models.DateField(verbose_name='Fecha de Fin')
    reason = models.TextField(blank=True, verbose_name='Motivo')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ausencia'
        verbose_name_plural = 'Ausencias'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.absence_type.name} ({self.start_date} - {self.end_date})"

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date < self.start_date:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')


class Vacation(models.Model):
    """Modelo para el control de vacaciones"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='vacations', verbose_name='Empleado')
    year = models.IntegerField(validators=[MinValueValidator(2020), MaxValueValidator(2100)], verbose_name='Año')
    days_entitled = models.IntegerField(default=0, verbose_name='Días Correspondientes')
    days_taken = models.IntegerField(default=0, verbose_name='Días Tomados')
    days_pending = models.IntegerField(default=0, verbose_name='Días Pendientes')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Control de Vacaciones'
        verbose_name_plural = 'Control de Vacaciones'
        unique_together = ['employee', 'year']
        ordering = ['-year', 'employee']

    def __str__(self):
        return f"{self.employee.full_name} - {self.year} ({self.days_pending} días pendientes)"

    def save(self, *args, **kwargs):
        self.days_pending = self.days_entitled - self.days_taken
        super().save(*args, **kwargs)


class Birthday(models.Model):
    """Vista para cumpleaños (calculado desde Employee)"""
    class Meta:
        managed = False
        verbose_name = 'Cumpleaños'
        verbose_name_plural = 'Cumpleaños'

    @classmethod
    def get_upcoming_birthdays(cls, days=30):
        """Obtiene los cumpleaños en los próximos días"""
        from datetime import datetime, timedelta
        today = date.today()
        end_date = today + timedelta(days=days)
        
        employees = Employee.objects.filter(is_active=True)
        upcoming = []
        
        for emp in employees:
            # Calcular próximo cumpleaños
            this_year_birthday = date(today.year, emp.birth_date.month, emp.birth_date.day)
            if this_year_birthday < today:
                next_birthday = date(today.year + 1, emp.birth_date.month, emp.birth_date.day)
            else:
                next_birthday = this_year_birthday
                
            # Verificar si está en el rango
            if today <= next_birthday <= end_date:
                upcoming.append({
                    'employee': emp,
                    'birthday': next_birthday,
                    'age': next_birthday.year - emp.birth_date.year
                })
        
        return sorted(upcoming, key=lambda x: x['birthday'])