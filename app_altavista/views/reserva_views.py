# app_altavista/views/reserva_views.py
from rest_framework import viewsets, permissions, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from app_altavista.models.area_comun import AreaComun
from app_altavista.models.propietario import Propietario
from app_altavista.models.reserva import ConfiguracionReservas, Reserva
from app_altavista.serializers.reserva_serializers import ConfiguracionReservasSerializer, ReservaCreateSerializer, ReservaDetalladaSerializer, ReservaSerializer


class ReservaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar reservas.
    
    Permite crear, consultar y gestionar las reservas de áreas comunes
    realizadas por los propietarios.
    """
    queryset = Reserva.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['area_comun', 'vivienda', 'estado', 'fecha_reserva']
    search_fields = ['observaciones']
    ordering_fields = ['fecha_reserva', 'hora_inicio', 'fecha_registro']
    ordering = ['-fecha_reserva', 'hora_inicio']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action in ['create', 'update', 'partial_update']:
            return ReservaCreateSerializer
        elif self.action == 'retrieve':
            return ReservaDetalladaSerializer
        return ReservaSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve', 'create']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Asigna automáticamente la vivienda del propietario."""
        try:
            propietario = self.request.user.propietario
            vivienda = propietario.get_vivienda_principal()
            if not vivienda:
                raise serializers.ValidationError(
                    "El usuario no tiene una vivienda asignada."
                )
            serializer.save(vivienda=vivienda)
        except (AttributeError, Propietario.DoesNotExist):
            raise serializers.ValidationError(
                "Solo los propietarios pueden realizar reservas."
            )
    
    @action(detail=False, methods=['get'])
    def disponibilidad(self, request):
        """
        Verifica la disponibilidad de un área común en una fecha y hora específica.
        """
        area_comun_id = request.query_params.get('area_comun')
        fecha = request.query_params.get('fecha')
        hora_inicio = request.query_params.get('hora_inicio')
        
        if not all([area_comun_id, fecha, hora_inicio]):
            return Response(
                {"error": "Debe especificar área común, fecha y hora de inicio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            area_comun = AreaComun.objects.get(id=area_comun_id)
            configuracion = ConfiguracionReservas.objects.get(area_comun=area_comun)
            
            # Verificar si hay reservas existentes
            reservas_existentes = Reserva.objects.filter(
                area_comun=area_comun,
                fecha_reserva=fecha,
                hora_inicio=hora_inicio,
                estado__in=['pendiente', 'confirmada']
            ).exists()
            
            if reservas_existentes:
                return Response({"disponible": False, "mensaje": "Ya existe una reserva para este horario."})
            
            return Response({
                "disponible": True,
                "duracion_maxima": configuracion.duracion_maxima,
                "costo": configuracion.costo
            })
        except (AreaComun.DoesNotExist, ConfiguracionReservas.DoesNotExist):
            return Response(
                {"error": "Área común no encontrada o no configurada."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """
        Confirma una reserva pendiente.
        """
        reserva = self.get_object()
        
        if reserva.estado != 'pendiente':
            return Response(
                {"error": "Solo se pueden confirmar reservas pendientes."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reserva.estado = 'confirmada'
        reserva.save()
        
        serializer = ReservaDetalladaSerializer(reserva)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela una reserva pendiente o confirmada.
        """
        reserva = self.get_object()
        
        if reserva.estado not in ['pendiente', 'confirmada']:
            return Response(
                {"error": "Solo se pueden cancelar reservas pendientes o confirmadas."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        motivo = request.data.get('motivo')
        reserva.estado = 'cancelada'
        if motivo:
            reserva.observaciones = (reserva.observaciones or '') + f"\n[CANCELACIÓN] {motivo}"
        reserva.save()
        
        serializer = ReservaDetalladaSerializer(reserva)
        return Response(serializer.data)


class ConfiguracionReservasViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar la configuración de reservas.
    
    Permite definir y consultar las reglas y parámetros para las reservas
    de cada área común.
    """
    queryset = ConfiguracionReservas.objects.all()
    serializer_class = ConfiguracionReservasSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['area_comun']
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]