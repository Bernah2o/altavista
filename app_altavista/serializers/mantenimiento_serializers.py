# app_altavista/serializers/mantenimiento_serializers.py
from rest_framework import serializers
from ..models.mantenimiento import (
    Mantenimiento,
    ActividadMantenimiento,
    MaterialMantenimiento,
    ProgramacionMantenimiento,
)


class MaterialMantenimientoSerializer(serializers.ModelSerializer):
    """Serializador para el modelo MaterialMantenimiento."""

    class Meta:
        model = MaterialMantenimiento
        fields = "__all__"


class ActividadMantenimientoSerializer(serializers.ModelSerializer):
    """Serializador para el modelo ActividadMantenimiento."""

    class Meta:
        model = ActividadMantenimiento
        fields = "__all__"


class MantenimientoSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Mantenimiento."""

    class Meta:
        model = Mantenimiento
        fields = "__all__"


class MantenimientoDetalladoSerializer(MantenimientoSerializer):
    """Serializador detallado para el modelo Mantenimiento."""

    actividades = ActividadMantenimientoSerializer(many=True, read_only=True)
    materiales = MaterialMantenimientoSerializer(many=True, read_only=True)

    class Meta(MantenimientoSerializer.Meta):
        fields = [
            "id",
            "titulo",
            "descripcion",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "tipo",
            "prioridad",
            "area_comun",
            "vivienda",
            "empleado",
            "observaciones",
            "actividades",
            "materiales",
        ]


class ProgramacionMantenimientoSerializer(serializers.ModelSerializer):
    """Serializador para el modelo ProgramacionMantenimiento."""

    class Meta:
        model = ProgramacionMantenimiento
        fields = "__all__"
