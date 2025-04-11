# app_altavista/views/mantenimiento_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import date, timedelta

from ..models.mantenimiento import (
    Mantenimiento,
    ActividadMantenimiento,
    MaterialMantenimiento,
    ProgramacionMantenimiento
)
from ..serializers.mantenimiento_serializers import (
    MantenimientoSerializer,
    MantenimientoDetalladoSerializer,
    ActividadMantenimientoSerializer,
    MaterialMantenimientoSerializer,
    ProgramacionMantenimientoSerializer
)


class MantenimientoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar mantenimientos.
    
    Permite crear, consultar y gestionar los mantenimientos preventivos
    y correctivos de la propiedad horizontal.
    """
    queryset = Mantenimiento.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'estado', 'prioridad', 'area_comun']
    search_fields = ['descripcion', 'observaciones']
    ordering_fields = ['fecha_programada', 'fecha_inicio', 'fecha_fin']
    ordering = ['-fecha_programada']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == 'retrieve':
            return MantenimientoDetalladoSerializer
        return MantenimientoSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def actividades(self, request, pk=None):
        """
        Retorna las actividades asociadas al mantenimiento.
        """
        mantenimiento = self.get_object()
        actividades = ActividadMantenimiento.objects.filter(mantenimiento=mantenimiento)
        serializer = ActividadMantenimientoSerializer(actividades, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def materiales(self, request, pk=None):
        """
        Retorna los materiales utilizados en el mantenimiento.
        """
        mantenimiento = self.get_object()
        materiales = MaterialMantenimiento.objects.filter(mantenimiento=mantenimiento)
        serializer = MaterialMantenimientoSerializer(materiales, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """
        Inicia un mantenimiento programado.
        """
        mantenimiento = self.get_object()
        
        if mantenimiento.estado != 'programado':
            return Response(
                {"error": "Solo se pueden iniciar mantenimientos programados."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        mantenimiento.estado = 'en_proceso'
        mantenimiento.fecha_inicio = timezone.now()
        mantenimiento.save()
        
        serializer = MantenimientoDetalladoSerializer(mantenimiento)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """
        Finaliza un mantenimiento en proceso.
        """
        mantenimiento = self.get_object()
        
        if mantenimiento.estado != 'en_proceso':
            return Response(
                {"error": "Solo se pueden finalizar mantenimientos en proceso."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        observaciones = request.data.get('observaciones')
        mantenimiento.estado = 'completado'
        mantenimiento.fecha_fin = timezone.now()
        if observaciones:
            mantenimiento.observaciones = (mantenimiento.observaciones or '') + f"\n[FINALIZACIÓN] {observaciones}"
        mantenimiento.save()
        
        serializer = MantenimientoDetalladoSerializer(mantenimiento)
        return Response(serializer.data)


class ActividadMantenimientoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar actividades de mantenimiento.
    
    Permite crear, consultar y gestionar las actividades específicas
    realizadas en cada mantenimiento.
    """
    queryset = ActividadMantenimiento.objects.all()
    serializer_class = ActividadMantenimientoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['mantenimiento', 'estado']
    ordering_fields = ['fecha', 'duracion']
    ordering = ['-fecha']
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class MaterialMantenimientoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar materiales de mantenimiento.
    
    Permite registrar y consultar los materiales utilizados
    en cada mantenimiento.
    """
    queryset = MaterialMantenimiento.objects.all()
    serializer_class = MaterialMantenimientoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['mantenimiento']
    search_fields = ['nombre', 'descripcion']
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class ProgramacionMantenimientoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar la programación de mantenimientos.
    
    Permite crear y gestionar la programación de mantenimientos
    preventivos periódicos.
    """
    queryset = ProgramacionMantenimiento.objects.all()
    serializer_class = ProgramacionMantenimientoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['area_comun', 'estado', 'periodicidad']
    search_fields = ['descripcion']
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def generar_mantenimiento(self, request, pk=None):
        """
        Genera un nuevo mantenimiento a partir de la programación.
        """
        programacion = self.get_object()
        
        try:
            mantenimiento = programacion.generar_mantenimiento()
            serializer = MantenimientoSerializer(mantenimiento)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )