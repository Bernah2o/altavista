# app_altavista/serializers/reserva_serializers.py
from rest_framework import serializers
from ..models.reserva import Reserva, ConfiguracionReservas
from ..models.area_comun import AreaComun
from ..models.vivienda import Vivienda

class ReservaSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Reserva."""
    class Meta:
        model = Reserva
        fields = '__all__'

class ReservaCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear una nueva reserva."""
    class Meta:
        model = Reserva
        fields = ['area_comun', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'observaciones']

    def validate(self, data):
        """Validación personalizada para la creación de reservas."""
        area_comun = data.get('area_comun')
        fecha_reserva = data.get('fecha_reserva')
        hora_inicio = data.get('hora_inicio')
        hora_fin = data.get('hora_fin')

        # Verificar disponibilidad
        reservas_existentes = Reserva.objects.filter(
            area_comun=area_comun,
            fecha_reserva=fecha_reserva,
            hora_inicio=hora_inicio,
            estado__in=['pendiente', 'confirmada']
        )

        if reservas_existentes.exists():
            raise serializers.ValidationError(
                "Ya existe una reserva para este horario."
            )

        return data

class ReservaDetalladaSerializer(ReservaSerializer):
    """Serializador detallado para el modelo Reserva."""
    area_comun_nombre = serializers.CharField(source='area_comun.nombre', read_only=True)
    vivienda_identificador = serializers.CharField(source='vivienda.identificador', read_only=True)

    class Meta(ReservaSerializer.Meta):
        fields = [
            'id',
            'area_comun',
            'vivienda',
            'fecha_reserva',
            'hora_inicio',
            'hora_fin',
            'estado',
            'observaciones',
            'area_comun_nombre',
            'vivienda_identificador'
        ]

class ConfiguracionReservasSerializer(serializers.ModelSerializer):
    """Serializador para el modelo ConfiguracionReservas."""
    class Meta:
        model = ConfiguracionReservas
        fields = '__all__'