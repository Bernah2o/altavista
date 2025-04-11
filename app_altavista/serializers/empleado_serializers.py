# app_altavista/serializers/empleado_serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from datetime import datetime
from ..models.empleado import Empleado, RegistroAsistencia


class EmpleadoSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Empleado."""

    class Meta:
        model = Empleado
        fields = "__all__"


class EmpleadoCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear un nuevo empleado."""

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = Empleado
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "telefono",
            "tipo_documento",
            "numero_documento",
            "cargo",
            "fecha_contratacion",
            "salario",
        ]

    def create(self, validated_data):
        """Crear un nuevo empleado con su usuario asociado."""
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name")
        last_name = validated_data.pop("last_name")

        # Crear usuario
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Crear empleado
        empleado = Empleado.objects.create(user=user, **validated_data)
        return empleado


class EmpleadoDetalladoSerializer(EmpleadoSerializer):
    """Serializador detallado para el modelo Empleado."""

    nombre_completo = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    cargo_display = serializers.CharField(source="get_cargo_display", read_only=True)
    tipo_documento_display = serializers.CharField(
        source="get_tipo_documento_display", read_only=True
    )

    class Meta(EmpleadoSerializer.Meta):
        fields = [
            "id",
            "user",
            "telefono",
            "tipo_documento",
            "numero_documento",
            "cargo",
            "fecha_contratacion",
            "salario",
            "activo",
            "nombre_completo",
            "email",
            "cargo_display",
            "tipo_documento_display",
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class RegistroAsistenciaSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo RegistroAsistencia."""

    class Meta:
        model = RegistroAsistencia
        fields = '__all__'


class RegistroAsistenciaDetalladoSerializer(RegistroAsistenciaSerializer):
    """Serializador detallado para el modelo RegistroAsistencia."""
    
    empleado_nombre = serializers.CharField(source='empleado.nombre_completo', read_only=True)
    empleado_cargo = serializers.CharField(source='empleado.get_cargo_display', read_only=True)
    tiempo_trabajado = serializers.SerializerMethodField()

    class Meta(RegistroAsistenciaSerializer.Meta):
        fields = ['id', 'empleado', 'fecha', 'hora_entrada', 'hora_salida',
                 'observaciones', 'empleado_nombre', 'empleado_cargo',
                 'tiempo_trabajado']

    def get_tiempo_trabajado(self, obj):
        """Calcula el tiempo trabajado en horas y minutos."""
        if obj.hora_entrada and obj.hora_salida:
            entrada = datetime.combine(obj.fecha, obj.hora_entrada)
            salida = datetime.combine(obj.fecha, obj.hora_salida)
            diferencia = salida - entrada
            horas = diferencia.seconds // 3600
            minutos = (diferencia.seconds % 3600) // 60
            return f"{horas}h {minutos}m"
        return None
