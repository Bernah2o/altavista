# app_altavista/serializers/propietario_serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from ..models.propietario import Propietario
from ..models.vivienda import Vivienda


class PropietarioSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Propietario."""

    class Meta:
        model = Propietario
        fields = "__all__"


class PropietarioCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear un nuevo propietario."""

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = Propietario
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "telefono",
            "tipo_documento",
            "numero_documento",
            "viviendas",
        ]

    def create(self, validated_data):
        """Crear un nuevo propietario con su usuario asociado."""
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

        # Crear propietario
        propietario = Propietario.objects.create(user=user, **validated_data)
        return propietario


class PropietarioDetalladoSerializer(PropietarioSerializer):
    """Serializador detallado para el modelo Propietario."""

    nombre_completo = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    viviendas_detalle = serializers.SerializerMethodField()
    tipo_documento_display = serializers.CharField(
        source="get_tipo_documento_display", read_only=True
    )

    class Meta(PropietarioSerializer.Meta):
        fields = [
            "id",
            "user",
            "telefono",
            "tipo_documento",
            "numero_documento",
            "viviendas",
            "nombre_completo",
            "email",
            "viviendas_detalle",
            "tipo_documento_display",
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_viviendas_detalle(self, obj):
        return [
            {
                "id": vivienda.id,
                "identificador": vivienda.identificador,
                "tipo": vivienda.get_tipo_display(),
                "area": vivienda.area,
            }
            for vivienda in obj.viviendas.all()
        ]
