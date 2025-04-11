# app_altavista/serializers/incidencia_serializers.py
from rest_framework import serializers
from ..models.incidencia import Incidencia, CategoriaIncidencia
from ..models.vivienda import Vivienda

class CategoriaIncidenciaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo CategoriaIncidencia."""
    class Meta:
        model = CategoriaIncidencia
        fields = ['id', 'nombre', 'descripcion', 'color', 'activa']

class IncidenciaSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Incidencia."""
    class Meta:
        model = Incidencia
        fields = '__all__'

class IncidenciaCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear una nueva incidencia."""
    class Meta:
        model = Incidencia
        fields = ['titulo', 'descripcion', 'tipo', 'prioridad', 'ubicacion', 'vivienda']

    def validate(self, data):
        """Validación personalizada para la creación de incidencias."""
        if data.get('vivienda'):
            vivienda = data['vivienda']
            if not Vivienda.objects.filter(id=vivienda.id, estado='ocupada').exists():
                raise serializers.ValidationError(
                    "La vivienda especificada no está ocupada o no existe."
                )
        return data

class IncidenciaDetalladaSerializer(IncidenciaSerializer):
    """Serializador detallado para el modelo Incidencia."""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    vivienda_identificador = serializers.CharField(source='vivienda.identificador', read_only=True)
    reportado_por = serializers.SerializerMethodField()
    asignado_a = serializers.SerializerMethodField()

    class Meta(IncidenciaSerializer.Meta):
        fields = [
            'id', 'titulo', 'descripcion', 'tipo', 'estado', 'prioridad',
            'ubicacion', 'vivienda', 'reportado_por', 'asignado_a',
            'fecha_reporte', 'fecha_actualizacion', 'estado_display',
            'tipo_display', 'prioridad_display', 'vivienda_identificador'
        ]

    def get_reportado_por(self, obj):
        if obj.reportado_por:
            return {
                'id': obj.reportado_por.id,
                'nombre': f"{obj.reportado_por.user.first_name} {obj.reportado_por.user.last_name}",
                'tipo': obj.reportado_por.__class__.__name__
            }
        return None

    def get_asignado_a(self, obj):
        if obj.asignado_a:
            return {
                'id': obj.asignado_a.id,
                'nombre': f"{obj.asignado_a.user.first_name} {obj.asignado_a.user.last_name}",
                'cargo': obj.asignado_a.get_cargo_display()
            }
        return None