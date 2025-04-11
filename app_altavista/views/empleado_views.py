# app_altavista/views/empleado_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta

from app_altavista.models.empleado import Empleado, RegistroAsistencia
from app_altavista.serializers.empleado_serializers import (
    EmpleadoCreateSerializer,
    EmpleadoDetalladoSerializer,
    EmpleadoSerializer,
    RegistroAsistenciaSerializer,
)


class EmpleadoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar empleados.

    Permite crear, consultar, actualizar y eliminar los empleados
    registrados en la propiedad horizontal.
    """

    queryset = Empleado.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["cargo", "tipo_contrato", "estado"]
    search_fields = ["nombre", "apellido", "numero_documento", "email", "telefono"]
    ordering_fields = ["nombre", "apellido", "fecha_ingreso"]
    ordering = ["apellido", "nombre"]

    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action in ["create", "update", "partial_update"]:
            return EmpleadoCreateSerializer
        elif self.action == "retrieve":
            return EmpleadoDetalladoSerializer
        return EmpleadoSerializer

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["get"])
    def asistencias(self, request, pk=None):
        """
        Retorna el registro de asistencias del empleado.
        """
        empleado = self.get_object()
        # Obtener parámetros de filtrado
        fecha_inicio = request.query_params.get("fecha_inicio")
        fecha_fin = request.query_params.get("fecha_fin")

        # Aplicar filtros
        asistencias = RegistroAsistencia.objects.filter(empleado=empleado)
        if fecha_inicio:
            asistencias = asistencias.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            asistencias = asistencias.filter(fecha__lte=fecha_fin)

        asistencias = asistencias.order_by("-fecha")
        serializer = RegistroAsistenciaSerializer(asistencias, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def registrar_asistencia(self, request, pk=None):
        """
        Registra una nueva asistencia para el empleado.
        """
        empleado = self.get_object()

        # Verificar si ya existe registro para hoy
        hoy = date.today()
        if RegistroAsistencia.objects.filter(empleado=empleado, fecha=hoy).exists():
            return Response(
                {"error": "Ya existe un registro de asistencia para el día de hoy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Crear nuevo registro
        registro = RegistroAsistencia.objects.create(
            empleado=empleado,
            fecha=hoy,
            hora_entrada=timezone.now().time(),
            estado="presente",
        )

        serializer = RegistroAsistenciaSerializer(registro)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def registrar_salida(self, request, pk=None):
        """
        Registra la hora de salida del empleado.
        """
        empleado = self.get_object()

        try:
            registro = RegistroAsistencia.objects.get(
                empleado=empleado, fecha=date.today(), hora_salida__isnull=True
            )
            registro.hora_salida = timezone.now().time()
            registro.save()

            serializer = RegistroAsistenciaSerializer(registro)
            return Response(serializer.data)
        except RegistroAsistencia.DoesNotExist:
            return Response(
                {"error": "No existe un registro de entrada para el día de hoy."},
                status=status.HTTP_404_NOT_FOUND,
            )


class RegistroAsistenciaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar registros de asistencia.

    Permite crear, consultar y gestionar los registros de asistencia
    de los empleados.
    """

    queryset = RegistroAsistencia.objects.all()
    serializer_class = RegistroAsistenciaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["empleado", "fecha", "estado"]
    ordering_fields = ["fecha", "hora_entrada", "hora_salida"]
    ordering = ["-fecha", "-hora_entrada"]

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def reporte_mensual(self, request):
        """
        Genera un reporte mensual de asistencias.
        """
        # Obtener mes y año del reporte
        mes = int(request.query_params.get("mes", date.today().month))
        año = int(request.query_params.get("año", date.today().year))

        # Filtrar registros del mes
        registros = RegistroAsistencia.objects.filter(fecha__year=año, fecha__month=mes)

        # Agrupar por empleado
        resumen = registros.values("empleado").annotate(
            total_asistencias=Count("id"),
            presentes=Count("id", filter=Q(estado="presente")),
            ausentes=Count("id", filter=Q(estado="ausente")),
            tardanzas=Count("id", filter=Q(estado="tardanza")),
        )

        # Agregar información del empleado
        for item in resumen:
            empleado = Empleado.objects.get(id=item["empleado"])
            item["nombre_empleado"] = f"{empleado.nombre} {empleado.apellido}"
            item["cargo"] = empleado.cargo

        return Response({"periodo": {"mes": mes, "año": año}, "registros": resumen})
