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
    initiative_type = models.ForeignKey(InitiativeType, on_delete=models.DO_NOTHING, verbose_name='Tipo')
    owner = models.ForeignKey(Employee, on_delete=models.DO_NOTHING, related_name='owned_initiatives', verbose_name='Responsable')
    collaborators = models.ManyToManyField(Employee, blank=True, related_name='collaborated_initiatives', verbose_name='Colaboradores')
    quarter = models.ForeignKey(Quarter, on_delete=models.DO_NOTHING, verbose_name='Periodo (Q)')
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


class UserStory(models.Model):
    """Historias de usuario asociadas a iniciativas (épicas)"""
    STATUS_CHOICES = [
        ('BACKLOG', 'Backlog'),
        ('READY', 'Listo para Sprint'),
        ('IN_PROGRESS', 'En Progreso'),
        ('IN_REVIEW', 'En Revisión'),
        ('TESTING', 'Pruebas'),
        ('DONE', 'Terminado'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    ]
    
    STORY_POINTS_CHOICES = [
        (1, '1 - Muy Pequeña'),
        (2, '2 - Pequeña'),
        (3, '3 - Mediana'),
        (5, '5 - Grande'),
        (8, '8 - Muy Grande'),
        (13, '13 - Extra Grande'),
        (21, '21 - XXL'),
    ]
    
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='user_stories', verbose_name='Iniciativa (Épica)')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descripción')
    acceptance_criteria = models.TextField(blank=True, verbose_name='Criterios de Aceptación')
    story_points = models.IntegerField(choices=STORY_POINTS_CHOICES, null=True, blank=True, verbose_name='Story Points')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name='Prioridad')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BACKLOG', verbose_name='Estado')
    assignee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_stories', verbose_name='Asignado a')
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_stories', verbose_name='Sprint')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Iniciado el')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completado el')
    
    class Meta:
        verbose_name = 'Historia de Usuario'
        verbose_name_plural = 'Historias de Usuario'
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"US-{self.pk}: {self.title}"
    
    @property
    def progress_percentage(self):
        """Calcula el porcentaje de progreso basado en las tareas"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0 if self.status != 'DONE' else 100
        
        completed_tasks = self.tasks.filter(status='DONE').count()
        return round((completed_tasks / total_tasks) * 100, 2)
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        
        # Actualizar fechas según estado
        if self.status == 'IN_PROGRESS' and not self.started_at:
            self.started_at = timezone.now()
        elif self.status == 'DONE' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status not in ['DONE'] and self.completed_at:
            self.completed_at = None
        
        super().save(*args, **kwargs)
        
        # Actualizar progreso de la iniciativa padre
        self.update_initiative_progress()
    
    def update_initiative_progress(self):
        """Actualiza el progreso de la iniciativa basado en las historias de usuario"""
        if self.initiative:
            stories = self.initiative.user_stories.all()
            if stories.exists():
                total_progress = sum(story.progress_percentage for story in stories)
                avg_progress = round(total_progress / stories.count(), 2)
                self.initiative.progress = min(100, avg_progress)
                self.initiative.save(update_fields=['progress'])


class Task(models.Model):
    """Tareas específicas dentro de las historias de usuario"""
    STATUS_CHOICES = [
        ('TODO', 'Por Hacer'),
        ('IN_PROGRESS', 'En Progreso'),
        ('IN_REVIEW', 'En Revisión'),
        ('DONE', 'Terminado'),
        ('BLOCKED', 'Bloqueado'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('DEVELOPMENT', 'Desarrollo'),
        ('TESTING', 'Pruebas'),
        ('DESIGN', 'Diseño'),
        ('RESEARCH', 'Investigación'),
        ('DOCUMENTATION', 'Documentación'),
        ('REVIEW', 'Revisión'),
        ('DEPLOYMENT', 'Despliegue'),
        ('OTHER', 'Otro'),
    ]
    
    user_story = models.ForeignKey(UserStory, on_delete=models.CASCADE, related_name='tasks', verbose_name='Historia de Usuario')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descripción')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='DEVELOPMENT', verbose_name='Tipo de Tarea')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO', verbose_name='Estado')
    assignee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name='Asignado a')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Horas Estimadas')
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Horas Reales')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Iniciado el')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completado el')
    blocked_reason = models.TextField(blank=True, verbose_name='Razón del Bloqueo')
    
    class Meta:
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
        ordering = ['status', '-created_at']
    
    def __str__(self):
        return f"T-{self.pk}: {self.title}"
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        
        # Actualizar fechas según estado
        if self.status == 'IN_PROGRESS' and not self.started_at:
            self.started_at = timezone.now()
        elif self.status == 'DONE' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status not in ['DONE'] and self.completed_at:
            self.completed_at = None
        
        super().save(*args, **kwargs)
        
        # Actualizar progreso de la historia de usuario padre
        if self.user_story:
            self.user_story.save()  # Esto activará update_initiative_progress