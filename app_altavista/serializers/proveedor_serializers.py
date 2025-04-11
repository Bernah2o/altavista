# app_altavista/serializers/proveedor_serializers.py
from rest_framework import serializers
from app_altavista.models.proveedor import Proveedor

class ProveedorSerializer(serializers.ModelSerializer):
    """Serializador base para el modelo Proveedor."""
    
    class Meta:
        model = Proveedor
        fields = [
            'id', 'nombre', 'tipo', 'nit', 'estado',
            'direccion', 'telefono', 'email',
            'contacto_nombre', 'contacto_telefono',
            'servicios_productos', 'fecha_registro',
            'ultima_actualizacion'
        ]
        read_only_fields = ['fecha_registro', 'ultima_actualizacion']

class ProveedorCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializador para crear y actualizar proveedores."""

    class Meta:
        model = Proveedor
        fields = [
            'nombre', 'tipo', 'nit', 'direccion',
            'telefono', 'email', 'contacto_nombre',
            'contacto_telefono', 'servicios_productos',
            'estado', 'observaciones'
        ]

    def validate_nit(self, value):
        """Validación personalizada para el NIT."""
        # Eliminar guiones para validar que solo contenga números
        nit_limpio = value.replace('-', '')
        if not nit_limpio.isdigit():
            raise serializers.ValidationError(
                'El NIT debe contener solo números y guiones.'
            )
        return value

class ProveedorDetalladoSerializer(serializers.ModelSerializer):
    """Serializador para mostrar información detallada del proveedor."""
    
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    esta_activo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Proveedor
        fields = [
            'id', 'nombre', 'tipo', 'tipo_display',
            'nit', 'direccion', 'telefono', 'email',
            'contacto_nombre', 'contacto_telefono',
            'servicios_productos', 'estado', 'estado_display',
            'esta_activo', 'fecha_registro', 'ultima_actualizacion',
            'observaciones'
        ]
        read_only_fields = ['fecha_registro', 'ultima_actualizacion']