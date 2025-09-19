from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Absence, Vacation, AbsenceType


@receiver(post_save, sender=Absence)
def update_vacation_on_absence_save(sender, instance, created, **kwargs):
    """
    Actualiza el modelo Vacation cuando se crea o modifica una ausencia de tipo vacaciones
    """
    # Verificar si es una ausencia de tipo vacaciones
    try:
        vacation_type = AbsenceType.objects.get(code='VAC')
        if instance.absence_type == vacation_type:
            update_vacation_days(instance.employee, instance.start_date.year)
    except AbsenceType.DoesNotExist:
        # Si no existe el tipo VAC, no hacer nada
        pass


@receiver(post_delete, sender=Absence)
def update_vacation_on_absence_delete(sender, instance, **kwargs):
    """
    Actualiza el modelo Vacation cuando se elimina una ausencia de tipo vacaciones
    """
    # Verificar si era una ausencia de tipo vacaciones
    try:
        vacation_type = AbsenceType.objects.get(code='VAC')
        if instance.absence_type == vacation_type:
            update_vacation_days(instance.employee, instance.start_date.year)
    except AbsenceType.DoesNotExist:
        pass


def update_vacation_days(employee, year):
    """
    Actualiza los días tomados de vacaciones para un empleado en un año específico
    """
    with transaction.atomic():
        # Obtener o crear el registro de vacaciones para el año
        vacation, created = Vacation.objects.get_or_create(
            employee=employee,
            year=year,
            defaults={
                'days_entitled': 15,  # Días por defecto, se puede ajustar
                'days_taken': 0
            }
        )
        
        # Calcular total de días de vacaciones tomados en el año
        try:
            vacation_type = AbsenceType.objects.get(code='VAC')
            vacation_absences = Absence.objects.filter(
                employee=employee,
                absence_type=vacation_type,
                start_date__year=year
            )
            
            total_vacation_days = sum(abs.duration_days for abs in vacation_absences)
            
            # Actualizar días tomados
            vacation.days_taken = total_vacation_days
            vacation.save()  # Esto automáticamente calculará days_pending
            
        except AbsenceType.DoesNotExist:
            pass


def validate_vacation_availability(employee, start_date, end_date, exclude_absence_id=None):
    """
    Valida si el empleado tiene días de vacaciones disponibles
    Retorna (is_valid, message, available_days)
    """
    try:
        vacation_type = AbsenceType.objects.get(code='VAC')
        year = start_date.year
        
        # Obtener el registro de vacaciones del año
        try:
            vacation = Vacation.objects.get(employee=employee, year=year)
        except Vacation.DoesNotExist:
            # Si no existe, crear uno por defecto
            vacation = Vacation.objects.create(
                employee=employee,
                year=year,
                days_entitled=15,
                days_taken=0
            )
        
        # Calcular días solicitados
        requested_days = (end_date - start_date).days + 1
        
        # Calcular días ya usados (excluyendo la ausencia actual si es edición)
        vacation_absences = Absence.objects.filter(
            employee=employee,
            absence_type=vacation_type,
            start_date__year=year
        )
        
        if exclude_absence_id:
            vacation_absences = vacation_absences.exclude(id=exclude_absence_id)
        
        used_days = sum(abs.duration_days for abs in vacation_absences)
        available_days = vacation.days_entitled - used_days
        
        if requested_days > available_days:
            return (
                False, 
                f"Solo tiene {available_days} días de vacaciones disponibles. Solicitó: {requested_days} días.",
                available_days
            )
        
        return (True, "Días de vacaciones disponibles", available_days - requested_days)
        
    except AbsenceType.DoesNotExist:
        # Si no existe el tipo VAC, permitir la ausencia
        return (True, "Tipo de vacaciones no configurado", 0)
