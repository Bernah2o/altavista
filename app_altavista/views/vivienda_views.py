# app_altavista/views/vivienda_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q

from app_altavista.serializers.propietario_serializers import PropietarioSerializer
from app_altavista.serializers.vivienda_serializers import ViviendaDetalladaSerializer, ViviendaSerializer

from ..models.vivienda import Vivienda, PropietarioVivienda
from ..models.propietario import Propietario


class ViviendaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar viviendas.
    
    Permite crear, consultar, actualizar y eliminar las viviendas
    registradas en la propiedad horizontal.
    """
    queryset = Vivienda.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['manzana', 'numero', 'tipo', 'estado']
    search_fields = ['manzana', 'numero', 'descripcion']
    ordering_fields = ['manzana', 'numero', 'area', 'fecha_registro']
    ordering = ['manzana', 'numero']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == 'retrieve':
            return ViviendaDetalladaSerializer
        return ViviendaSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def propietarios(self, request, pk=None):
        """
        Retorna los propietarios asociados a la vivienda.
        """
        vivienda = self.get_object()
        propietarios = vivienda.get_propietarios_activos()
        from ..serializers.propietario_serializers import PropietarioListSerializer
        serializer = PropietarioListSerializer(propietarios, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def asignar_propietario(self, request, pk=None):
        """
        Asigna un propietario a la vivienda.
        """
        vivienda = self.get_object()
        serializer = PropietarioViviendaCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            propietario_id = serializer.validated_data['propietario']
            try:
                propietario = Propietario.objects.get(id=propietario_id)
                PropietarioVivienda.objects.create(
                    vivienda=vivienda,
                    propietario=propietario,
                    fecha_inicio=serializer.validated_data.get('fecha_inicio'),
                    tipo_propietario=serializer.validated_data.get('tipo_propietario', 'principal')
                )
                return Response(
                    {"mensaje": "Propietario asignado exitosamente."},
                    status=status.HTTP_201_CREATED
                )
            except Propietario.DoesNotExist:
                return Response(
                    {"error": "El propietario especificado no existe."},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def remover_propietario(self, request, pk=None):
        """
        Remueve un propietario de la vivienda.
        """
        vivienda = self.get_object()
        propietario_id = request.data.get('propietario')
        
        try:
            relacion = PropietarioVivienda.objects.get(
                vivienda=vivienda,
                propietario_id=propietario_id,
                fecha_fin__isnull=True
            )
            relacion.finalizar()
            return Response({"mensaje": "Propietario removido exitosamente."})
        except PropietarioVivienda.DoesNotExist:
            return Response(
                {"error": "No existe una relación activa entre el propietario y la vivienda."},
                status=status.HTTP_404_NOT_FOUND
            )


class PropietarioViviendaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar las relaciones entre propietarios y viviendas.
    
    Permite crear, consultar y gestionar los registros históricos de propietarios
    asociados a las viviendas.
    """
    queryset = PropietarioVivienda.objects.all()
    serializer_class = PropietarioSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vivienda', 'propietario', 'tipo_propietario', 'activo']
    ordering_fields = ['fecha_inicio', 'fecha_fin']
    ordering = ['-fecha_inicio']

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
