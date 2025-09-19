from django.db import models
from django.contrib.auth.models import User
from team.models import Employee
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, timedelta


class Quarter(models.Model):
    """Modelo para representar los periodos de trabajo (Q)"""
    year = models.IntegerField(validators=[MinValueValidator(2020), MaxValueValidator(2100)], verbose_name='Año')
    quarter = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4)], verbose_name='Trimestre')
    start_date = models.DateField(verbose_name='Fecha de Inicio')
    end_date = models.DateField(verbose_name='Fecha de Fin')
    is_active = models.BooleanField(default=False, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Periodo (Q)'
        verbose_name_plural = 'Periodos (Q)'
        unique_together = ['year', 'quarter']
        ordering = ['-year', '-quarter']

    def __str__(self):
        return f"Q{self.quarter} {self.year}"

    def save(self, *args, **kwargs):
        # Auto calcular fechas basadas en el trimestre
        if not self.start_date:
            quarter_starts = {
                1: date(self.year, 1, 1),
                2: date(self.year, 4, 1),
                3: date(self.year, 7, 1),
                4: date(self.year, 10, 1)
            }
            self.start_date = quarter_starts[self.quarter]
        
        if not self.end_date:
            quarter_ends = {
                1: date(self.year, 3, 31),
                2: date(self.year, 6, 30),
                3: date(self.year, 9, 30),
                4: date(self.year, 12, 31)
            }
            self.end_date = quarter_ends[self.quarter]
        
        # Solo un Q puede estar activo
        if self.is_active:
            Quarter.objects.exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)


class InitiativeType(models.Model):
    """Tipos de iniciativas o temas"""
    CATEGORY_CHOICES = [
        ('OPERATIONAL', 'Operativo'),
        ('PROJECT', 'Proyecto'),
        ('INITIATIVE', 'Iniciativa'),
        ('IMPROVEMENT', 'Mejora'),
        ('SUPPORT', 'Soporte'),
    ]
    
    name = models.CharField(max_length=50, verbose_name='Tipo')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Categoría')
    description = models.TextField(blank=True, verbose_name='Descripción')
    color = models.CharField(max_length=7, default='#3498db', verbose_name='Color (HEX)')
    
    class Meta:
        verbose_name = 'Tipo de Iniciativa'
        verbose_name_plural = 'Tipos de Iniciativa'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class Initiative(models.Model):
    """Modelo principal para iniciativas y temas"""
    STATUS_CHOICES = [
        ('BACKLOG', 'Backlog'),
        ('PLANNED', 'Planeado'),
        ('IN_PROGRESS', 'En Progreso'),
        ('BLOCKED', 'Bloqueado'),
        ('COMPLETED', 'Completado'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descripción')
    initiative_type = models.ForeignKey(InitiativeType, on_delete=models.PROTECT, verbose_name='Tipo')
    owner = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='owned_initiatives', verbose_name='Responsable')
    collaborators = models.ManyToManyField(Employee, blank=True, related_name='collaborated_initiatives', verbose_name='Colaboradores')
    quarter = models.ForeignKey(Quarter, on_delete=models.PROTECT, verbose_name='Periodo (Q)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BACKLOG', verbose_name='Estado')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name='Prioridad')
    start_date = models.DateField(null=True, blank=True, verbose_name='Fecha de Inicio')
    target_date = models.DateField(null=True, blank=True, verbose_name='Fecha Objetivo')
    completion_date = models.DateField(null=True, blank=True, verbose_name='Fecha de Completado')
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='Progreso (%)')
    is_operational = models.BooleanField(default=False, verbose_name='Es Operativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Iniciativa'
        verbose_name_plural = 'Iniciativas'
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.owner.full_name}"


class OperationalTask(models.Model):
    """Tareas operativas recurrentes"""
    FREQUENCY_CHOICES = [
        ('DAILY', 'Diario'),
        ('WEEKLY', 'Semanal'),
        ('BIWEEKLY', 'Quincenal'),
        ('MONTHLY', 'Mensual'),
        ('QUARTERLY', 'Trimestral'),
        ('YEARLY', 'Anual'),
        ('ON_DEMAND', 'Bajo Demanda'),
    ]
    
    initiative = models.OneToOneField(Initiative, on_delete=models.CASCADE, related_name='operational_details', verbose_name='Iniciativa')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name='Frecuencia')
    day_of_week = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(6)], verbose_name='Día de la Semana', help_text='0=Lunes, 6=Domingo')
    day_of_month = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(31)], verbose_name='Día del Mes')
    time_of_day = models.TimeField(null=True, blank=True, verbose_name='Hora del Día')
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='Duración (horas)')
    last_execution = models.DateTimeField(null=True, blank=True, verbose_name='Última Ejecución')
    next_execution = models.DateTimeField(null=True, blank=True, verbose_name='Próxima Ejecución')
    
    class Meta:
        verbose_name = 'Tarea Operativa'
        verbose_name_plural = 'Tareas Operativas'

    def __str__(self):
        return f"{self.initiative.title} - {self.get_frequency_display()}"

    def calculate_next_execution(self):
        """Calcula la próxima ejecución basada en la frecuencia"""
        from datetime import datetime, time
        
        if not self.last_execution:
            base_date = datetime.now()
        else:
            base_date = self.last_execution
        
        if self.frequency == 'DAILY':
            next_date = base_date + timedelta(days=1)
        elif self.frequency == 'WEEKLY':
            next_date = base_date + timedelta(weeks=1)
        elif self.frequency == 'BIWEEKLY':
            next_date = base_date + timedelta(weeks=2)
        elif self.frequency == 'MONTHLY':
            next_date = base_date + timedelta(days=30)  # Aproximado
        elif self.frequency == 'QUARTERLY':
            next_date = base_date + timedelta(days=90)  # Aproximado
        elif self.frequency == 'YEARLY':
            next_date = base_date + timedelta(days=365)
        else:  # ON_DEMAND
            return None
        
        if self.time_of_day:
            next_date = datetime.combine(next_date.date(), self.time_of_day)
        
        return next_date


class Sprint(models.Model):
    """Sprints para seguimiento ágil"""
    name = models.CharField(max_length=100, verbose_name='Nombre')
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, related_name='sprints', verbose_name='Periodo (Q)')
    sprint_number = models.IntegerField(verbose_name='Número de Sprint')
    start_date = models.DateField(verbose_name='Fecha de Inicio')
    end_date = models.DateField(verbose_name='Fecha de Fin')
    goal = models.TextField(blank=True, verbose_name='Objetivo del Sprint')
    is_active = models.BooleanField(default=False, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Sprint'
        verbose_name_plural = 'Sprints'
        unique_together = ['quarter', 'sprint_number']
        ordering = ['quarter', 'sprint_number']

    def __str__(self):
        return f"{self.name} - {self.quarter}"


class InitiativeUpdate(models.Model):
    """Actualizaciones y novedades de las iniciativas"""
    UPDATE_TYPE_CHOICES = [
        ('PROGRESS', 'Actualización de Progreso'),
        ('BLOCKER', 'Bloqueo'),
        ('RISK', 'Riesgo'),
        ('ACHIEVEMENT', 'Logro'),
        ('COMMENT', 'Comentario'),
    ]
    
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='updates', verbose_name='Iniciativa')
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPE_CHOICES, verbose_name='Tipo')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descripción')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Creado por')
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False, verbose_name='Resuelto')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Resolución')
    
    class Meta:
        verbose_name = 'Actualización de Iniciativa'
        verbose_name_plural = 'Actualizaciones de Iniciativas'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_update_type_display()} - {self.initiative.title}"


class InitiativeMetric(models.Model):
    """Métricas para seguimiento de iniciativas"""
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='metrics', verbose_name='Iniciativa')
    metric_name = models.CharField(max_length=100, verbose_name='Nombre de la Métrica')
    target_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Objetivo')
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor Actual')
    unit = models.CharField(max_length=20, blank=True, verbose_name='Unidad')
    measured_at = models.DateField(default=date.today, verbose_name='Fecha de Medición')
    
    class Meta:
        verbose_name = 'Métrica de Iniciativa'
        verbose_name_plural = 'Métricas de Iniciativas'
        ordering = ['initiative', 'metric_name']

    def __str__(self):
        return f"{self.metric_name} - {self.initiative.title}"

    @property
    def achievement_percentage(self):
        if self.target_value == 0:
            return 0
        return round((self.current_value / self.target_value) * 100, 2)