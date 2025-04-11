# app_altavista/views/propiedad_views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from ..models.propiedad import PropiedadHorizontal, ConfiguracionGeneral
from ..serializers.propiedad_serializers import (
    PropiedadHorizontalSerializer,
    PropiedadHorizontalDetalladoSerializer,
    ConfiguracionGeneralSerializer
)

class PropiedadHorizontalViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar la información de la propiedad horizontal.
    
    Permite consultar y modificar los datos generales del conjunto residencial.
    """
    queryset = PropiedadHorizontal.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'nit', 'direccion', 'representante_legal']
    ordering_fields = ['nombre', 'fecha_constitucion']
    ordering = ['nombre']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == 'retrieve':
            return PropiedadHorizontalDetalladoSerializer
        return PropiedadHorizontalSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

class ConfiguracionGeneralViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar las configuraciones generales del sistema.
    
    Permite crear, consultar, actualizar y eliminar configuraciones.
    """
    queryset = ConfiguracionGeneral.objects.all()
    serializer_class = ConfiguracionGeneralSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo']
    search_fields = ['nombre', 'clave', 'descripcion']
    ordering_fields = ['nombre', 'clave']
    ordering = ['nombre']
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def por_clave(self, request):
        """Obtiene una configuración por su clave."""
        clave = request.query_params.get('clave', None)
        if not clave:
            return Response(
                {"error": "Debe especificar una clave"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            config = ConfiguracionGeneral.objects.get(clave=clave)
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        except ConfiguracionGeneral.DoesNotExist:
            return Response(
                {"error": "Configuración no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )