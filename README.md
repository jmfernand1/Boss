# BOSS - Sistema de Gestión de Equipo e Iniciativas

BOSS (Business Operations Support System) es una aplicación web desarrollada en Django que permite a los líderes y jefes de equipo gestionar aspectos administrativos del personal y hacer seguimiento de iniciativas y proyectos usando metodologías ágiles.

## 🚀 Características Principales

### 📋 Módulo Administrativo (Team)
- **Gestión de Empleados**: Información completa del personal
- **Control de Ausencias**: Registro y seguimiento de ausencias
- **Gestión de Vacaciones**: Control de días disponibles y tomados
- **Calendario de Cumpleaños**: Vista mensual de cumpleaños
- **Dashboard del Equipo**: Resumen general del estado del equipo

### 🎯 Módulo de Iniciativas
- **Gestión por Quarters (Q)**: Organización por periodos trimestrales
- **Tipos de Iniciativas**: Proyectos, mejoras, operativos, soporte
- **Tareas Operativas**: Control de tareas recurrentes con frecuencias definidas
- **Seguimiento Ágil**: Sprints, tablero Kanban, métricas
- **Actualizaciones**: Registro de progreso, bloqueos, riesgos y logros
- **Dashboard de Iniciativas**: Vista general del Q activo

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.0.1
- **Frontend**: Bootstrap 5.3, Font Awesome
- **Base de Datos**: SQLite (desarrollo)
- **Autenticación**: Sistema de autenticación de Django

## 📦 Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd boss
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar migraciones**
```bash
python manage.py migrate
```

5. **Crear datos iniciales (opcional)**
```bash
python create_initial_data.py
```

6. **Iniciar el servidor**
```bash
python manage.py runserver
```

7. **Acceder a la aplicación**
```
http://localhost:8000
```

## 👤 Usuarios de Prueba

Si ejecutaste el script de datos iniciales, puedes acceder con:

- **Administrador**: 
  - Usuario: `admin`
  - Contraseña: `admin123`

- **Empleados de ejemplo**:
  - Usuarios: `jperez`, `mgarcia`, `clopez`, `amartinez`
  - Contraseña: `password123`

## 📱 Módulos y Funcionalidades

### Team (Equipo)
- `/team/` - Dashboard del equipo
- `/team/employees/` - Lista de empleados
- `/team/absences/` - Gestión de ausencias
- `/team/vacations/` - Control de vacaciones
- `/team/birthdays/` - Calendario de cumpleaños

### Initiatives (Iniciativas)
- `/initiatives/` - Dashboard de iniciativas
- `/initiatives/list/` - Lista de todas las iniciativas
- `/initiatives/operational/` - Tareas operativas
- `/initiatives/sprint/` - Tablero del sprint actual
- `/initiatives/quarter/` - Resumen del Q activo

### Administración
- `/admin/` - Panel de administración de Django

## 🔧 Configuración Adicional

### Zona Horaria
El sistema está configurado para la zona horaria de México (`America/Mexico_City`). Para cambiarla, modifica en `settings.py`:
```python
TIME_ZONE = 'America/Mexico_City'
```

### Idioma
El sistema está en español. Para cambiar el idioma, modifica en `settings.py`:
```python
LANGUAGE_CODE = 'es-mx'
```

## 📊 Modelos de Datos

### Team
- **Employee**: Información del empleado
- **AbsenceType**: Tipos de ausencias (vacaciones, enfermedad, etc.)
- **Absence**: Registro de ausencias
- **Vacation**: Control anual de vacaciones

### Initiatives
- **Quarter**: Periodos trimestrales
- **InitiativeType**: Categorización de iniciativas
- **Initiative**: Iniciativas y proyectos
- **OperationalTask**: Detalles de tareas recurrentes
- **Sprint**: Sprints ágiles
- **InitiativeUpdate**: Actualizaciones y novedades
- **InitiativeMetric**: Métricas de seguimiento

## 🚧 Próximas Mejoras

- [ ] Notificaciones por correo
- [ ] Exportación de reportes (PDF/Excel)
- [ ] API REST para integraciones
- [ ] Gráficas y estadísticas avanzadas
- [ ] Integración con calendario externo
- [ ] Sistema de permisos más granular

## 📝 Licencia

Este proyecto es privado y de uso interno empresarial.

## 👥 Soporte

Para soporte o preguntas sobre el sistema, contactar al equipo de TI.