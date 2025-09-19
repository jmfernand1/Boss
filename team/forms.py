from django import forms
from django.contrib.auth.models import User
from datetime import date
from .models import Employee, Absence, Vacation, AbsenceType


class EmployeeForm(forms.ModelForm):
    """Formulario para crear/editar empleados"""
    
    # Campos del usuario
    first_name = forms.CharField(
        max_length=30,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        max_length=150,
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'birth_date', 'hire_date', 'position', 
            'department', 'phone', 'mobile', 'emergency_contact', 
            'emergency_phone', 'notes', 'is_active'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        
        if instance and instance.user:
            self.fields['first_name'].initial = instance.user.first_name
            self.fields['last_name'].initial = instance.user.last_name
            self.fields['email'].initial = instance.user.email
            self.fields['username'].initial = instance.user.username
    
    def clean_username(self):
        username = self.cleaned_data['username']
        instance = getattr(self, 'instance', None)
        
        # Verificar que el username no esté en uso por otro usuario
        user_query = User.objects.filter(username=username)
        if instance and instance.user:
            user_query = user_query.exclude(pk=instance.user.pk)
        
        if user_query.exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        
        return username
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        instance = getattr(self, 'instance', None)
        
        # Verificar que el employee_id no esté en uso
        employee_query = Employee.objects.filter(employee_id=employee_id)
        if instance:
            employee_query = employee_query.exclude(pk=instance.pk)
        
        if employee_query.exists():
            raise forms.ValidationError('Este ID de empleado ya está en uso.')
        
        return employee_id
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        
        # Crear o actualizar el usuario
        if employee.user:
            user = employee.user
        else:
            user = User()
        
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        
        if commit:
            user.save()
            employee.user = user
            employee.save()
        
        return employee


class AbsenceForm(forms.ModelForm):
    """Formulario para crear/editar ausencias"""
    
    class Meta:
        model = Absence
        fields = ['employee', 'absence_type', 'start_date', 'end_date', 'reason', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'absence_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True).select_related('user')
        self.fields['employee'].empty_label = "Seleccionar empleado..."
        self.fields['absence_type'].empty_label = "Seleccionar tipo..."
        
        # Establecer fecha de hoy como default para start_date
        if not self.instance.pk:
            self.fields['start_date'].initial = date.today()
            self.fields['end_date'].initial = date.today()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee = cleaned_data.get('employee')
        absence_type = cleaned_data.get('absence_type')
        
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        # Validación especial para vacaciones
        if all([employee, absence_type, start_date, end_date]):
            from .signals import validate_vacation_availability
            from .models import AbsenceType
            
            try:
                vacation_type = AbsenceType.objects.get(code='VAC')
                if absence_type == vacation_type:
                    # Obtener ID de la ausencia actual si estamos editando
                    exclude_id = self.instance.pk if self.instance.pk else None
                    
                    is_valid, message, remaining_days = validate_vacation_availability(
                        employee, start_date, end_date, exclude_id
                    )
                    
                    if not is_valid:
                        raise forms.ValidationError(message)
                    
            except AbsenceType.DoesNotExist:
                pass
        
        return cleaned_data


class VacationForm(forms.ModelForm):
    """Formulario para crear/editar control de vacaciones"""
    
    class Meta:
        model = Vacation
        fields = ['employee', 'year', 'days_entitled', 'days_taken', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2020', 'max': '2100'}),
            'days_entitled': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'days_taken': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True).select_related('user')
        self.fields['employee'].empty_label = "Seleccionar empleado..."
        
        # Establecer año actual como default
        if not self.instance.pk:
            self.fields['year'].initial = date.today().year
    
    def clean_days_taken(self):
        days_taken = self.cleaned_data.get('days_taken', 0)
        days_entitled = self.cleaned_data.get('days_entitled', 0)
        
        if days_taken > days_entitled:
            raise forms.ValidationError('Los días tomados no pueden ser mayores a los días correspondientes.')
        
        return days_taken
    
    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        year = cleaned_data.get('year')
        
        if employee and year:
            # Verificar que no exista otro registro para el mismo empleado y año
            vacation_query = Vacation.objects.filter(employee=employee, year=year)
            if self.instance.pk:
                vacation_query = vacation_query.exclude(pk=self.instance.pk)
            
            if vacation_query.exists():
                raise forms.ValidationError(f'Ya existe un registro de vacaciones para {employee.full_name} en el año {year}.')
        
        return cleaned_data


class AbsenceTypeForm(forms.ModelForm):
    """Formulario para crear/editar tipos de ausencia"""
    
    class Meta:
        model = AbsenceType
        fields = ['name', 'code', 'requires_approval', 'paid', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '10'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data['code'].upper()
        instance = getattr(self, 'instance', None)
        
        # Verificar que el código no esté en uso
        type_query = AbsenceType.objects.filter(code=code)
        if instance:
            type_query = type_query.exclude(pk=instance.pk)
        
        if type_query.exists():
            raise forms.ValidationError('Este código ya está en uso.')
        
        return code


class QuickAbsenceForm(forms.Form):
    """Formulario rápido para registrar ausencias desde el dashboard"""
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Empleado'
    )
    absence_type = forms.ModelChoiceField(
        queryset=AbsenceType.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo'
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Fecha Inicio',
        initial=date.today
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Fecha Fin',
        initial=date.today
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label='Motivo',
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(is_active=True).select_related('user')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee = cleaned_data.get('employee')
        absence_type = cleaned_data.get('absence_type')
        
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        # Validación especial para vacaciones
        if all([employee, absence_type, start_date, end_date]):
            from .signals import validate_vacation_availability
            from .models import AbsenceType
            
            try:
                vacation_type = AbsenceType.objects.get(code='VAC')
                if absence_type == vacation_type:
                    is_valid, message, remaining_days = validate_vacation_availability(
                        employee, start_date, end_date
                    )
                    
                    if not is_valid:
                        raise forms.ValidationError(message)
                    
            except AbsenceType.DoesNotExist:
                pass
        
        return cleaned_data
    
    def save(self):
        """Crear la ausencia basada en los datos del formulario"""
        absence = Absence(
            employee=self.cleaned_data['employee'],
            absence_type=self.cleaned_data['absence_type'],
            start_date=self.cleaned_data['start_date'],
            end_date=self.cleaned_data['end_date'],
            reason=self.cleaned_data['reason']
        )
        absence.save()
        return absence
