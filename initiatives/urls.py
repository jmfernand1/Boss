from django.urls import path
from . import views

app_name = 'initiatives'

urlpatterns = [
    path('', views.initiatives_dashboard, name='dashboard'),
    path('list/', views.initiative_list, name='initiative_list'),
    path('detail/<int:pk>/', views.initiative_detail, name='initiative_detail'),
    path('operational/', views.operational_tasks, name='operational_tasks'),
    path('sprint/', views.sprint_board, name='sprint_board'),
    path('quarter/', views.quarter_summary, name='quarter_summary'),
    path('quarter/<int:pk>/', views.quarter_summary, name='quarter_summary_detail'),
]
