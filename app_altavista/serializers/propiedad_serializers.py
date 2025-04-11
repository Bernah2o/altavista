# app_altavista/serializers/propiedad_serializers.py
from rest_framework import serializers
from ..models.propiedad import PropiedadHorizontal, ConfiguracionGeneral

class PropiedadHorizontalSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo PropiedadHorizontal."""
    class Meta:
        model = PropiedadHorizontal
        fields = '__all__'

class PropiedadHorizontalDetalladoSerializer(PropiedadHorizontalSerializer):
    """Serializador detallado para el modelo PropiedadHorizontal."""
    configuracion = serializers.SerializerMethodField()

    class Meta(PropiedadHorizontalSerializer.Meta):
        fields = PropiedadHorizontalSerializer.Meta.fields + ('configuracion')

    def get_configuracion(self, obj):
        """Obtener la configuración asociada a la propiedad."""
        try:
            config = obj.configuracion
            return {
                'id': config.id,
                'nombre': config.nombre,
                'clave': config.clave,
                'valor': config.valor_tipado,
                'tipo': config.tipo,
                'descripcion': config.descripcion
            }
        except ConfiguracionGeneral.DoesNotExist:
            return None

class ConfiguracionGeneralSerializer(serializers.ModelSerializer):
    """Serializador para el modelo ConfiguracionGeneral."""
    valor_tipado = serializers.SerializerMethodField()

    class Meta:
        model = ConfiguracionGeneral
        fields = '__all__'

    def get_valor_tipado(self, obj):
        """Obtener el valor convertido al tipo correspondiente."""
        return obj.valor_tipado