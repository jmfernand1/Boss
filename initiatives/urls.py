from django.urls import path
from . import views

app_name = 'initiatives'

urlpatterns = [
    # Dashboard y vistas principales
    path('', views.initiatives_dashboard, name='dashboard'),
    path('list/', views.initiative_list, name='initiative_list'),
    path('detail/<int:pk>/', views.initiative_detail, name='initiative_detail'),
    path('operational/', views.operational_tasks, name='operational_tasks'),
    path('sprint/', views.sprint_board, name='sprint_board'),
    path('quarter/', views.quarter_summary, name='quarter_summary'),
    path('quarter/<int:pk>/', views.quarter_summary, name='quarter_summary_detail'),
    
    # CRUD Initiatives
    path('create/', views.initiative_create, name='initiative_create'),
    path('edit/<int:pk>/', views.initiative_edit, name='initiative_edit'),
    path('delete/<int:pk>/', views.initiative_delete, name='initiative_delete'),
    path('quick-create/', views.quick_initiative_create, name='quick_initiative_create'),
    
    # CRUD Quarters
    path('quarters/', views.quarter_list, name='quarter_list'),
    path('quarters/create/', views.quarter_create, name='quarter_create'),
    path('quarters/edit/<int:pk>/', views.quarter_edit, name='quarter_edit'),
    path('quarters/delete/<int:pk>/', views.quarter_delete, name='quarter_delete'),
    
    # CRUD Initiative Types
    path('types/', views.initiative_type_list, name='initiative_type_list'),
    path('types/create/', views.initiative_type_create, name='initiative_type_create'),
    path('types/edit/<int:pk>/', views.initiative_type_edit, name='initiative_type_edit'),
    path('types/delete/<int:pk>/', views.initiative_type_delete, name='initiative_type_delete'),
    
    # CRUD Sprints
    path('sprints/', views.sprint_list, name='sprint_list'),
    path('sprints/create/', views.sprint_create, name='sprint_create'),
    path('sprints/edit/<int:pk>/', views.sprint_edit, name='sprint_edit'),
    path('sprints/delete/<int:pk>/', views.sprint_delete, name='sprint_delete'),
    
    # CRUD Initiative Updates
    path('<int:initiative_pk>/updates/create/', views.initiative_update_create, name='initiative_update_create'),
    path('updates/edit/<int:pk>/', views.initiative_update_edit, name='initiative_update_edit'),
    path('updates/delete/<int:pk>/', views.initiative_update_delete, name='initiative_update_delete'),
    
    # CRUD Initiative Metrics
    path('<int:initiative_pk>/metrics/create/', views.initiative_metric_create, name='initiative_metric_create'),
    path('metrics/edit/<int:pk>/', views.initiative_metric_edit, name='initiative_metric_edit'),
    path('metrics/delete/<int:pk>/', views.initiative_metric_delete, name='initiative_metric_delete'),
    
    # CRUD Operational Tasks
    path('operational/create/', views.operational_task_create, name='operational_task_create'),
    path('operational/edit/<int:pk>/', views.operational_task_edit, name='operational_task_edit'),
    path('operational/delete/<int:pk>/', views.operational_task_delete, name='operational_task_delete'),
    path('operational/mark-executed/<int:pk>/', views.operational_task_mark_executed, name='operational_task_mark_executed'),
    
    # CRUD User Stories
    path('<int:initiative_pk>/stories/create/', views.user_story_create, name='user_story_create'),
    path('stories/<int:pk>/', views.user_story_detail, name='user_story_detail'),
    path('stories/edit/<int:pk>/', views.user_story_edit, name='user_story_edit'),
    path('stories/delete/<int:pk>/', views.user_story_delete, name='user_story_delete'),
    path('stories/quick-create/', views.quick_user_story_create, name='quick_user_story_create'),
    
    # CRUD Tasks
    path('stories/<int:story_pk>/tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/edit/<int:pk>/', views.task_edit, name='task_edit'),
    path('tasks/delete/<int:pk>/', views.task_delete, name='task_delete'),
    path('tasks/quick-create/', views.quick_task_create, name='quick_task_create'),
    
    # Vistas auxiliares AJAX
    path('change-status/<int:pk>/', views.initiative_change_status, name='initiative_change_status'),
    path('stories/change-status/<int:pk>/', views.user_story_change_status, name='user_story_change_status'),
    path('tasks/change-status/<int:pk>/', views.task_change_status, name='task_change_status'),
]
