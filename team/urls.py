from django.urls import path
from . import views

app_name = 'team'

urlpatterns = [
    path('', views.team_dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('absences/', views.absence_list, name='absence_list'),
    path('vacations/', views.vacation_summary, name='vacation_summary'),
    path('birthdays/', views.birthday_calendar, name='birthday_calendar'),
]
