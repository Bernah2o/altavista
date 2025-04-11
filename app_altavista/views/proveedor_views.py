# app_altavista/views/proveedor_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from app_altavista.models.proveedor import Proveedor
from app_altavista.serializers.proveedor_serializers import (
    ProveedorSerializer,
    ProveedorCreateUpdateSerializer,
    ProveedorDetalladoSerializer
)

class ProveedorViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar proveedores.

    Permite crear, consultar, actualizar y eliminar los proveedores
    registrados en la propiedad horizontal.
    """

    queryset = Proveedor.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['tipo', 'estado']
    search_fields = ['nombre', 'nit', 'email', 'contacto_nombre']
    ordering_fields = ['nombre', 'fecha_registro', 'ultima_actualizacion']
    ordering = ['nombre']

    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action in ['create', 'update', 'partial_update']:
            return ProveedorCreateUpdateSerializer
        elif self.action == 'retrieve':
            return ProveedorDetalladoSerializer
        return ProveedorSerializer

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """Activa un proveedor."""
        proveedor = self.get_object()
        if proveedor.estado == 'activo':
            return Response(
                {'error': 'El proveedor ya está activo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proveedor.estado = 'activo'
        proveedor.save()
        serializer = self.get_serializer(proveedor)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """Desactiva un proveedor."""
        proveedor = self.get_object()
        if proveedor.estado == 'inactivo':
            return Response(
                {'error': 'El proveedor ya está inactivo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proveedor.estado = 'inactivo'
        proveedor.save()
        serializer = self.get_serializer(proveedor)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def bloquear(self, request, pk=None):
        """Bloquea un proveedor."""
        proveedor = self.get_object()
        if proveedor.estado == 'bloqueado':
            return Response(
                {'error': 'El proveedor ya está bloqueado.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proveedor.estado = 'bloqueado'
        proveedor.save()
        serializer = self.get_serializer(proveedor)
        return Response(serializer.data)