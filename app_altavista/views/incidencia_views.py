from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from app_altavista.models.incidencia import CategoriaIncidencia, Incidencia
from app_altavista.serializers.incidencia_serializers import (
    CategoriaIncidenciaSerializer,
    IncidenciaSerializer,
)


class CategoriaIncidenciaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar categorías de incidencias.

    Permite crear, consultar y gestionar las categorías utilizadas
    para clasificar las incidencias.
    """

    queryset = CategoriaIncidencia.objects.all()
    serializer_class = CategoriaIncidenciaSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["activa"]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre"]
    ordering = ("nombre",)

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class IncidenciaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar incidencias.

    Permite crear, consultar y gestionar las incidencias reportadas
    en el sistema, incluyendo su seguimiento y resolución.
    """

    queryset = Incidencia.objects.all()
    serializer_class = IncidenciaSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["estado", "prioridad", "categoria", "asignado_a"]
    search_fields = ["titulo", "descripcion"]
    ordering_fields = ["fecha_creacion", "fecha_actualizacion", "prioridad"]
    ordering = ["-fecha_creacion"]

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def cambiar_estado(self, request, pk=None):
        """
        Actualiza el estado de una incidencia.
        """
        incidencia = self.get_object()
        nuevo_estado = request.data.get("estado")

        if nuevo_estado not in dict(Incidencia.ESTADOS).keys():
            return Response(
                {"error": "Estado no válido."}, status=status.HTTP_400_BAD_REQUEST
            )

        incidencia.estado = nuevo_estado
        incidencia.save()

        serializer = self.get_serializer(incidencia)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def asignar(self, request, pk=None):
        """
        Asigna la incidencia a un empleado.
        """
        incidencia = self.get_object()
        empleado_id = request.data.get("empleado")

        if not empleado_id:
            return Response(
                {"error": "Se requiere especificar un empleado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from ..models.empleado import Empleado

            empleado = Empleado.objects.get(id=empleado_id)
            incidencia.asignado_a = empleado
            incidencia.save()

            serializer = self.get_serializer(incidencia)
            return Response(serializer.data)
        except Empleado.DoesNotExist:
            return Response(
                {"error": "El empleado especificado no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )
