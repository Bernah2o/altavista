# app_altavista/views/propietario_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q

from ..models.propietario import Propietario
from ..models.vivienda import PropietarioVivienda
from ..serializers.propietario_serializers import (
    PropietarioSerializer,
    PropietarioDetalladoSerializer,
    PropietarioCreateSerializer
)


class PropietarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar propietarios.
    
    Permite crear, consultar, actualizar y eliminar los propietarios
    registrados en la propiedad horizontal.
    """
    queryset = Propietario.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_documento', 'estado', 'fecha_registro']
    search_fields = ['nombre', 'apellido', 'numero_documento', 'email', 'telefono']
    ordering_fields = ['nombre', 'apellido', 'fecha_registro']
    ordering = ['apellido', 'nombre']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action in ['create', 'update', 'partial_update']:
            return PropietarioCreateSerializer
        elif self.action == 'retrieve':
            return PropietarioDetalladoSerializer
        return PropietarioSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def viviendas(self, request, pk=None):
        """
        Retorna las viviendas asociadas al propietario.
        """
        propietario = self.get_object()
        viviendas = propietario.viviendas.all()
        from ..serializers.vivienda_serializers import ViviendaListSerializer
        serializer = ViviendaListSerializer(viviendas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historial_viviendas(self, request, pk=None):
        """
        Retorna el historial completo de viviendas del propietario.
        """
        propietario = self.get_object()
        historial = PropietarioVivienda.objects.filter(propietario=propietario)
        serializer = PropietarioViviendaSerializer(historial, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        Activa un propietario inactivo.
        """
        propietario = self.get_object()
        if propietario.estado == 'activo':
            return Response(
                {"error": "El propietario ya está activo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        propietario.estado = 'activo'
        propietario.save()
        serializer = self.get_serializer(propietario)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def inactivar(self, request, pk=None):
        """
        Inactiva un propietario activo.
        """
        propietario = self.get_object()
        if propietario.estado == 'inactivo':
            return Response(
                {"error": "El propietario ya está inactivo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si tiene viviendas activas
        viviendas_activas = PropietarioVivienda.objects.filter(
            propietario=propietario,
            fecha_fin__isnull=True
        ).exists()
        
        if viviendas_activas:
            return Response(
                {"error": "No se puede inactivar el propietario mientras tenga viviendas asociadas."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        propietario.estado = 'inactivo'
        propietario.save()
        serializer = self.get_serializer(propietario)
        return Response(serializer.data)