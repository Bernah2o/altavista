# app_altavista/serializers/finanzas_serializers.py
from rest_framework import serializers
from ..models.finanzas import (
    IngresoGasto,
    Presupuesto,
    FondoReserva,
    MovimientoFondo
)

class IngresoGastoSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo IngresoGasto."""
    class Meta:
        model = IngresoGasto
        fields = '__all__'

class IngresoGastoDetalladoSerializer(IngresoGastoSerializer):
    """Serializador detallado para el modelo IngresoGasto."""
    class Meta(IngresoGastoSerializer.Meta):
        fields = IngresoGastoSerializer.Meta.fields

class PresupuestoSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Presupuesto."""
    class Meta:
        model = Presupuesto
        fields = '__all__'

class PresupuestoDetalladoSerializer(PresupuestoSerializer):
    """Serializador detallado para el modelo Presupuesto."""
    ingresos_ejecutados = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    gastos_ejecutados = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Presupuesto
        fields = [
            'id',
            'año',
            'mes',
            'ingresos_presupuestados',
            'gastos_presupuestados',
            'descripcion',
            'estado',
            'fecha_creacion',
            'creado_por',
            'ingresos_ejecutados',
            'gastos_ejecutados'
        ]

class FondoReservaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo FondoReserva."""
    class Meta:
        model = FondoReserva
        fields = '__all__'

class MovimientoFondoSerializer(serializers.ModelSerializer):
    """Serializador para el modelo MovimientoFondo."""
    class Meta:
        model = MovimientoFondo
        fields = '__all__'