from django.contrib import admin
from .models import (
    Quarter, InitiativeType, Initiative, OperationalTask, 
    Sprint, InitiativeUpdate, InitiativeMetric, UserStory, Task
)


@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'start_date', 'end_date', 'is_active']
    list_filter = ['year', 'is_active']
    ordering = ['-year', '-quarter']


@admin.register(InitiativeType)
class InitiativeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'color']
    list_filter = ['category']
    search_fields = ['name', 'description']


@admin.register(Initiative)
class InitiativeAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'initiative_type', 'quarter', 'status', 'priority', 'progress']
    list_filter = ['status', 'priority', 'initiative_type', 'quarter', 'is_operational']
    search_fields = ['title', 'description', 'owner__user__first_name', 'owner__user__last_name']
    date_hierarchy = 'created_at'
    ordering = ['-priority', '-created_at']
    filter_horizontal = ['collaborators']
    
    fieldsets = (
        ('Información General', {
            'fields': ('title', 'description', 'initiative_type', 'is_operational')
        }),
        ('Asignación', {
            'fields': ('owner', 'collaborators', 'quarter')
        }),
        ('Estado y Prioridad', {
            'fields': ('status', 'priority', 'progress')
        }),
        ('Fechas', {
            'fields': ('start_date', 'target_date', 'completion_date')
        }),
    )


@admin.register(OperationalTask)
class OperationalTaskAdmin(admin.ModelAdmin):
    list_display = ['initiative', 'frequency', 'last_execution', 'next_execution']
    list_filter = ['frequency']
    search_fields = ['initiative__title']
    
    fieldsets = (
        ('Iniciativa', {
            'fields': ('initiative',)
        }),
        ('Frecuencia', {
            'fields': ('frequency', 'day_of_week', 'day_of_month', 'time_of_day', 'duration_hours')
        }),
        ('Ejecución', {
            'fields': ('last_execution', 'next_execution')
        }),
    )


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ['name', 'quarter', 'sprint_number', 'start_date', 'end_date', 'is_active']
    list_filter = ['quarter', 'is_active']
    search_fields = ['name', 'goal']
    date_hierarchy = 'start_date'
    ordering = ['quarter', 'sprint_number']


@admin.register(InitiativeUpdate)
class InitiativeUpdateAdmin(admin.ModelAdmin):
    list_display = ['initiative', 'update_type', 'title', 'created_by', 'created_at', 'is_resolved']
    list_filter = ['update_type', 'is_resolved', 'created_at']
    search_fields = ['title', 'description', 'initiative__title']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('initiative', 'update_type', 'title', 'description')
        }),
        ('Estado', {
            'fields': ('is_resolved', 'resolved_at')
        }),
        ('Metadatos', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_by']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InitiativeMetric)
class InitiativeMetricAdmin(admin.ModelAdmin):
    list_display = ['initiative', 'metric_name', 'current_value', 'target_value', 'achievement_percentage', 'measured_at']
    list_filter = ['measured_at', 'initiative__quarter']
    search_fields = ['metric_name', 'initiative__title']
    date_hierarchy = 'measured_at'
    ordering = ['initiative', 'metric_name']


@admin.register(UserStory)
class UserStoryAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'initiative', 'status', 'priority', 'story_points', 'assignee', 'sprint', 'progress_percentage']
    list_filter = ['status', 'priority', 'story_points', 'initiative__quarter', 'sprint']
    search_fields = ['title', 'description', 'initiative__title', 'assignee__user__first_name', 'assignee__user__last_name']
    date_hierarchy = 'created_at'
    ordering = ['-priority', '-created_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('initiative', 'title', 'description', 'acceptance_criteria')
        }),
        ('Planificación', {
            'fields': ('story_points', 'priority', 'status', 'assignee', 'sprint')
        }),
        ('Fechas', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['started_at', 'completed_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user_story', 'task_type', 'status', 'assignee', 'estimated_hours', 'actual_hours']
    list_filter = ['task_type', 'status', 'user_story__initiative__quarter']
    search_fields = ['title', 'description', 'user_story__title', 'assignee__user__first_name', 'assignee__user__last_name']
    date_hierarchy = 'created_at'
    ordering = ['status', '-created_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('user_story', 'title', 'description', 'task_type')
        }),
        ('Asignación y Estado', {
            'fields': ('status', 'assignee', 'blocked_reason')
        }),
        ('Tiempo', {
            'fields': ('estimated_hours', 'actual_hours')
        }),
        ('Fechas', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['started_at', 'completed_at']