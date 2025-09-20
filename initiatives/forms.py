from django import forms
from django.contrib.auth.models import User
from datetime import date
from .models import (
    Initiative, Quarter, Sprint, InitiativeUpdate, 
    InitiativeMetric, OperationalTask, InitiativeType
)
from team.models import Employee


class InitiativeForm(forms.ModelForm):
    """Formulario para crear/editar iniciativas"""
    
    class Meta:
        model = Initiative
        fields = [
            'title', 'description', 'initiative_type', 'owner', 'collaborators',
            'quarter', 'status', 'priority', 'start_date', 'target_date',
            'completion_date', 'progress', 'is_operational'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'initiative_type': forms.Select(attrs={'class': 'form-select'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'collaborators': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'quarter': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'progress': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'is_operational': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owner'].queryset = Employee.objects.filter(is_active=True).select_related('user')
        self.fields['collaborators'].queryset = Employee.objects.filter(is_active=True).select_related('user')
        self.fields['quarter'].queryset = Quarter.objects.all().order_by('-year', '-quarter')
        
        self.fields['owner'].empty_label = "Seleccionar responsable..."
        self.fields['initiative_type'].empty_label = "Seleccionar tipo..."
        self.fields['quarter'].empty_label = "Seleccionar periodo..."
        
        # Preseleccionar Q activo si es nuevo
        if not self.instance.pk:
            active_quarter = Quarter.objects.filter(is_active=True).first()
            if active_quarter:
                self.fields['quarter'].initial = active_quarter
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        target_date = cleaned_data.get('target_date')
        completion_date = cleaned_data.get('completion_date')
        status = cleaned_data.get('status')
        
        # Validaciones de fechas
        if start_date and target_date and target_date < start_date:
            raise forms.ValidationError('La fecha objetivo debe ser posterior a la fecha de inicio.')
        
        if completion_date and start_date and completion_date < start_date:
            raise forms.ValidationError('La fecha de completado debe ser posterior a la fecha de inicio.')
        
        # Si está completado, debe tener fecha de completado
        if status == 'COMPLETED' and not completion_date:
            cleaned_data['completion_date'] = date.today()
        
        # Si no está completado, no debería tener fecha de completado
        if status != 'COMPLETED' and completion_date:
            cleaned_data['completion_date'] = None
        
        return cleaned_data


class QuarterForm(forms.ModelForm):
    """Formulario para crear/editar periodos (Q)"""
    
    class Meta:
        model = Quarter
        fields = ['year', 'quarter', 'start_date', 'end_date', 'is_active']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2020', 'max': '2100'}),
            'quarter': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '4'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['year'].initial = date.today().year
    
    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        quarter = cleaned_data.get('quarter')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        # Verificar que no exista otro Q para el mismo año y trimestre
        if year and quarter:
            quarter_query = Quarter.objects.filter(year=year, quarter=quarter)
            if self.instance.pk:
                quarter_query = quarter_query.exclude(pk=self.instance.pk)
            
            if quarter_query.exists():
                raise forms.ValidationError(f'Ya existe un Q{quarter} para el año {year}.')
        
        return cleaned_data


class InitiativeTypeForm(forms.ModelForm):
    """Formulario para crear/editar tipos de iniciativa"""
    
    class Meta:
        model = InitiativeType
        fields = ['name', 'category', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }


class SprintForm(forms.ModelForm):
    """Formulario para crear/editar sprints"""
    
    class Meta:
        model = Sprint
        fields = ['name', 'quarter', 'sprint_number', 'start_date', 'end_date', 'goal', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'quarter': forms.Select(attrs={'class': 'form-select'}),
            'sprint_number': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'goal': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quarter'].queryset = Quarter.objects.all().order_by('-year', '-quarter')
        self.fields['quarter'].empty_label = "Seleccionar periodo..."
        
        # Preseleccionar Q activo si es nuevo
        if not self.instance.pk:
            active_quarter = Quarter.objects.filter(is_active=True).first()
            if active_quarter:
                self.fields['quarter'].initial = active_quarter
    
    def clean(self):
        cleaned_data = super().clean()
        quarter = cleaned_data.get('quarter')
        sprint_number = cleaned_data.get('sprint_number')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        # Verificar que no exista otro sprint con el mismo número en el Q
        if quarter and sprint_number:
            sprint_query = Sprint.objects.filter(quarter=quarter, sprint_number=sprint_number)
            if self.instance.pk:
                sprint_query = sprint_query.exclude(pk=self.instance.pk)
            
            if sprint_query.exists():
                raise forms.ValidationError(f'Ya existe un Sprint {sprint_number} en {quarter}.')
        
        return cleaned_data


class OperationalTaskForm(forms.ModelForm):
    """Formulario para crear/editar tareas operativas"""
    
    class Meta:
        model = OperationalTask
        fields = [
            'initiative', 'frequency', 'day_of_week', 'day_of_month',
            'time_of_day', 'duration_hours', 'last_execution', 'next_execution'
        ]
        widgets = {
            'initiative': forms.Select(attrs={'class': 'form-select'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '6'}),
            'day_of_month': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '31'}),
            'time_of_day': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'last_execution': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'next_execution': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['initiative'].queryset = Initiative.objects.filter(is_operational=True)
        self.fields['initiative'].empty_label = "Seleccionar iniciativa operativa..."


class InitiativeUpdateForm(forms.ModelForm):
    """Formulario para crear actualizaciones de iniciativas"""
    
    def __init__(self, *args, **kwargs):
        # Extraer initiative si se pasa como parámetro
        initiative = kwargs.pop('initiative', None)
        super().__init__(*args, **kwargs)
        
        if initiative:
            # Pre-seleccionar la iniciativa y ocultarla
            self.fields['initiative'].initial = initiative
            self.fields['initiative'].widget = forms.HiddenInput()
        
        # Configurar widgets
        self.fields['title'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Título de la actualización'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe la actualización en detalle...'
        })
    
    class Meta:
        model = InitiativeUpdate
        fields = ['initiative', 'update_type', 'title', 'description', 'is_resolved']
        widgets = {
            'initiative': forms.Select(attrs={'class': 'form-select'}),
            'update_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        initiative = kwargs.pop('initiative', None)
        super().__init__(*args, **kwargs)
        
        if initiative:
            self.fields['initiative'].initial = initiative
            self.fields['initiative'].widget.attrs['readonly'] = True
        
        self.fields['initiative'].queryset = Initiative.objects.all().select_related('owner')
        self.fields['initiative'].empty_label = "Seleccionar iniciativa..."


class InitiativeMetricForm(forms.ModelForm):
    """Formulario para crear/editar métricas de iniciativas"""
    
    def __init__(self, *args, **kwargs):
        # Extraer initiative si se pasa como parámetro
        initiative = kwargs.pop('initiative', None)
        super().__init__(*args, **kwargs)
        
        if initiative:
            # Pre-seleccionar la iniciativa y ocultarla
            self.fields['initiative'].initial = initiative
            self.fields['initiative'].widget = forms.HiddenInput()
        
        # Configurar widgets
        self.fields['metric_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ej: Usuarios Activos, Ventas Mensuales, etc.'
        })
        self.fields['target_value'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '100'
        })
        self.fields['current_value'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '0'
        })
        self.fields['unit'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '%'
        })
        # Establecer fecha actual por defecto
        if not self.instance.pk:
            self.fields['measured_at'].initial = timezone.now().date()
    
    class Meta:
        model = InitiativeMetric
        fields = ['initiative', 'metric_name', 'target_value', 'current_value', 'unit', 'measured_at']
        widgets = {
            'initiative': forms.Select(attrs={'class': 'form-select'}),
            'metric_name': forms.TextInput(attrs={'class': 'form-control'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
        'measured_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    }




class QuickInitiativeForm(forms.Form):
    """Formulario rápido para crear iniciativas desde el dashboard"""
    
    title = forms.CharField(
        max_length=200,
        label='Título',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        label='Descripción',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    initiative_type = forms.ModelChoiceField(
        queryset=InitiativeType.objects.all(),
        label='Tipo',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccionar tipo..."
    )
    owner = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True).select_related('user'),
        label='Responsable',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccionar responsable..."
    )
    priority = forms.ChoiceField(
        choices=Initiative.PRIORITY_CHOICES,
        label='Prioridad',
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='MEDIUM'
    )
    is_operational = forms.BooleanField(
        label='¿Es operativo?',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def save(self):
        """Crear la iniciativa basada en los datos del formulario"""
        active_quarter = Quarter.objects.filter(is_active=True).first()
        
        initiative = Initiative(
            title=self.cleaned_data['title'],
            description=self.cleaned_data['description'] or '',
            initiative_type=self.cleaned_data['initiative_type'],
            owner=self.cleaned_data['owner'],
            quarter=active_quarter,
            priority=self.cleaned_data['priority'],
            is_operational=self.cleaned_data['is_operational']
        )
        
        if active_quarter:
            initiative.save()
            return initiative
        else:
            raise forms.ValidationError('No hay un periodo (Q) activo para crear la iniciativa.')
