from django.contrib import admin

from app_altavista.models.administracion import CuotaAdministracion
from app_altavista.models.area_comun import AreaComun
from app_altavista.models.empleado import Empleado
from app_altavista.models.finanzas import IngresoGasto
from app_altavista.models.incidencia import Incidencia
from app_altavista.models.mantenimiento import Mantenimiento
from app_altavista.models.propietario import Propietario
from app_altavista.models.vivienda import Vivienda


@admin.register(Vivienda)
class ViviendaAdmin(admin.ModelAdmin):
    list_display = ['manzana', 'numero', 'area_m2', 'habitada', 'tiene_ampliacion']
    list_filter = ['manzana', 'habitada', 'tiene_ampliacion']
    search_fields = ['manzana', 'numero']
    ordering = ['manzana', 'numero']

@admin.register(Propietario)
class PropietarioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'documento_identidad', 'telefono', 'email']
    list_filter = ['fecha_registro']
    search_fields = ['nombre', 'apellido', 'documento_identidad']
    ordering = ['apellido', 'nombre']

@admin.register(AreaComun)
class AreaComunAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'capacidad', 'requiere_reserva', 'esta_activa']
    list_filter = ['tipo', 'requiere_reserva', 'esta_activa']
    search_fields = ['nombre', 'ubicacion']
    ordering = ['nombre']

@admin.register(IngresoGasto)
class IngresoGastoAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'tipo', 'categoria', 'monto', 'estado']
    list_filter = ['tipo', 'categoria', 'estado', 'fecha']
    search_fields = ['descripcion', 'numero_factura']
    ordering = ['-fecha', '-fecha_registro']

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'cargo', 'activo', 'fecha_contratacion']
    list_filter = ['cargo', 'activo']
    search_fields = ['nombre', 'apellido', 'documento_identidad']
    ordering = ['apellido', 'nombre']

@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'propietario', 'vivienda', 'tipo', 'prioridad', 'estado']
    list_filter = ['tipo', 'prioridad', 'estado']
    search_fields = ['titulo', 'descripcion']
    ordering = ['-fecha_reporte']

@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'prioridad', 'fecha_programada', 'estado']
    list_filter = ['tipo', 'prioridad', 'estado']
    search_fields = ['titulo', 'descripcion']
    ordering = ['-fecha_programada']

@admin.register(CuotaAdministracion)
class CuotaAdministracionAdmin(admin.ModelAdmin):
    list_display = ['año', 'mes', 'valor_base', 'fecha_vencimiento']
    list_filter = ['año', 'mes']
    search_fields = ['descripcion']
    ordering = ['-año', '-mes']
