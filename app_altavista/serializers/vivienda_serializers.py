# app_altavista/serializers/vivienda_serializers.py
from rest_framework import serializers
from ..models.vivienda import Vivienda
from ..models.propietario import Propietario

class ViviendaSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Vivienda."""
    class Meta:
        model = Vivienda
        fields = '__all__'

class ViviendaCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear una nueva vivienda."""
    class Meta:
        model = Vivienda
        fields = ['identificador', 'tipo', 'area', 'estado', 'observaciones']

    def validate_identificador(self, value):
        """Validar que el identificador sea único."""
        if Vivienda.objects.filter(identificador=value).exists():
            raise serializers.ValidationError(
                "Ya existe una vivienda con este identificador."
            )
        return value

class ViviendaDetalladaSerializer(ViviendaSerializer):
    """Serializador detallado para el modelo Vivienda."""
    propietarios = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta(ViviendaSerializer.Meta):
        fields = ['id', 'identificador', 'tipo', 'area', 'estado', 'observaciones', 'propietarios', 'estado_display', 'tipo_display']

    def get_propietarios(self, obj):
        """Obtener lista de propietarios asociados a la vivienda."""
        propietarios = obj.propietario_set.all()
        return [{
            'id': prop.id,
            'nombre': f"{prop.user.first_name} {prop.user.last_name}",
            'email': prop.user.email,
            'telefono': prop.telefono
        } for prop in propietarios]