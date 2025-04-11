# app_altavista/serializers/area_comun_serializers.py
from rest_framework import serializers
from ..models.area_comun import AreaComun, ElementoAreaComun

class ElementoAreaComunSerializer(serializers.ModelSerializer):
    """Serializador para el modelo ElementoAreaComun."""
    class Meta:
        model = ElementoAreaComun
        fields = '__all__'

class AreaComunSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo AreaComun."""
    horarios_formateados = serializers.CharField(read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = AreaComun
        fields = '__all__'

class AreaComunDetalladoSerializer(AreaComunSerializer):
    """Serializador detallado para el modelo AreaComun."""
    elementos = ElementoAreaComunSerializer(many=True, read_only=True)
    reservas_hoy = serializers.SerializerMethodField()
    proximos_mantenimientos = serializers.SerializerMethodField()

    class Meta(AreaComunSerializer.Meta):
        fields = ['id', 'nombre', 'tipo', 'capacidad', 'estado', 'descripcion', 'horario_inicio', 'horario_fin', 'horarios_formateados', 'tipo_display', 'elementos', 'reservas_hoy', 'proximos_mantenimientos']

    def get_reservas_hoy(self, obj):
        """Obtener las reservas del día actual."""
        from datetime import date
        reservas = obj.get_reservas_del_dia(date.today())
        return [{
            'id': r.id,
            'hora_inicio': r.hora_inicio.strftime('%I:%M %p'),
            'hora_fin': r.hora_fin.strftime('%I:%M %p'),
            'propietario': f"{r.propietario.nombre} {r.propietario.apellido}"
        } for r in reservas]

    def get_proximos_mantenimientos(self, obj):
        """Obtener los próximos mantenimientos programados."""
        mantenimientos = obj.get_proximos_mantenimientos()
        return [{
            'id': m.id,
            'fecha_programada': m.fecha_programada,
            'descripcion': m.descripcion,
            'estado': m.get_estado_display()
        } for m in mantenimientos]

class ElementoAreaComunDetalladoSerializer(ElementoAreaComunSerializer):
    """Serializador detallado para el modelo ElementoAreaComun."""
    area_comun = AreaComunSerializer(read_only=True)

    class Meta(ElementoAreaComunSerializer.Meta):
        fields = ElementoAreaComunSerializer.Meta.fields