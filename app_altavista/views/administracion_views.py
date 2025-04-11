# app_altavista/views/administracion_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from datetime import date, timedelta

from app_altavista.serializers.administracion_serializers import CuotaAdministracionDetalladaSerializer, CuotaAdministracionSerializer, PagoAdministracionCreateSerializer, PagoAdministracionDetalladoSerializer, PagoAdministracionSerializer, ReportePagosSerializer

from ..models.administracion import CuotaAdministracion, PagoAdministracion
from ..models.vivienda import Vivienda
from ..models.propietario import Propietario
from ..models.empleado import Empleado


class CuotaAdministracionViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar cuotas de administración.

    Permite crear, consultar, actualizar y eliminar las cuotas mensuales
    establecidas para la administración de la propiedad horizontal.
    """

    queryset = CuotaAdministracion.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["año", "mes", "fecha_vencimiento"]
    search_fields = ["descripcion"]
    ordering_fields = ["año", "mes", "fecha_vencimiento", "valor_base"]
    ordering = ["-año", "-mes"]

    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == "retrieve":
            return CuotaAdministracionDetalladaSerializer
        return CuotaAdministracionSerializer

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def periodo_actual(self, request):
        """
        Retorna la cuota del período actual (mes en curso).
        """
        hoy = date.today()
        try:
            cuota = CuotaAdministracion.objects.get(año=hoy.year, mes=hoy.month)
            serializer = CuotaAdministracionDetalladaSerializer(cuota)
            return Response(serializer.data)
        except CuotaAdministracion.DoesNotExist:
            return Response(
                {"error": f"No existe cuota para el período {hoy.month}/{hoy.year}"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["post"])
    def generar_siguiente(self, request):
        """
        Genera la cuota para el período siguiente.
        """
        nueva_cuota = CuotaAdministracion.generar_cuota_siguiente_mes()

        if nueva_cuota:
            serializer = CuotaAdministracionSerializer(nueva_cuota)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {
                    "error": "No se pudo generar la cuota para el siguiente período. Puede que ya exista o no haya cuota actual."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["get"])
    def estado_pagos(self, request, pk=None):
        """
        Retorna el estado de pagos para esta cuota.
        """
        cuota = self.get_object()

        # Contar pagos por estado
        total_viviendas = Vivienda.objects.count()
        pagos_realizados = PagoAdministracion.objects.filter(cuota=cuota).count()
        pagos_pendientes = total_viviendas - pagos_realizados

        # Agrupar por estado
        estados = (
            PagoAdministracion.objects.filter(cuota=cuota)
            .values("estado")
            .annotate(total=Count("estado"))
        )

        # Crear diccionario de estados
        estados_dict = {"registrado": 0, "confirmado": 0, "rechazado": 0}

        for estado in estados:
            estados_dict[estado["estado"]] = estado["total"]

        # Calcular monto esperado y recaudado
        monto_esperado = cuota.valor_base * total_viviendas

        monto_recaudado = (
            PagoAdministracion.objects.filter(
                cuota=cuota, estado="confirmado"
            ).aggregate(total=Sum("monto_pagado"))["total"]
            or 0
        )

        return Response(
            {
                "total_viviendas": total_viviendas,
                "pagos_realizados": pagos_realizados,
                "pagos_pendientes": pagos_pendientes,
                "porcentaje_recaudacion": (
                    round((pagos_realizados / total_viviendas) * 100, 2)
                    if total_viviendas > 0
                    else 0
                ),
                "monto_esperado": monto_esperado,
                "monto_recaudado": monto_recaudado,
                "porcentaje_monto": (
                    round((monto_recaudado / monto_esperado) * 100, 2)
                    if monto_esperado > 0
                    else 0
                ),
                "detalle_estados": estados_dict,
            }
        )

    @action(detail=True, methods=["get"])
    def viviendas_pendientes(self, request, pk=None):
        """
        Retorna las viviendas que no han pagado esta cuota.
        """
        cuota = self.get_object()

        # Obtener viviendas que ya pagaron
        viviendas_pagadas = PagoAdministracion.objects.filter(cuota=cuota).values_list(
            "vivienda_id", flat=True
        )

        # Filtrar viviendas que no han pagado
        viviendas_pendientes = Vivienda.objects.exclude(id__in=viviendas_pagadas)

        from ..serializers.vivienda_serializers import ViviendaListSerializer

        serializer = ViviendaListSerializer(viviendas_pendientes, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def generar_recordatorios(self, request, pk=None):
        """
        Genera recordatorios para las viviendas con pagos pendientes.

        Esta función simula el envío de notificaciones. En un entorno real,
        se debería implementar la lógica de envío de correos, SMS, etc.
        """
        cuota = self.get_object()

        # Verificar que la cuota tenga pagos pendientes
        viviendas_pagadas = PagoAdministracion.objects.filter(cuota=cuota).values_list(
            "vivienda_id", flat=True
        )

        viviendas_pendientes = Vivienda.objects.exclude(id__in=viviendas_pagadas)

        if not viviendas_pendientes.exists():
            return Response(
                {"error": "No hay viviendas con pagos pendientes para esta cuota."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generar recordatorios (simulado)
        recordatorios_enviados = 0
        for vivienda in viviendas_pendientes:
            propietarios = vivienda.get_propietarios_activos()
            for propietario in propietarios:
                if propietario.email:
                    # Simular envío de recordatorio
                    recordatorios_enviados += 1
                    # En un entorno real, aquí se enviaría el correo

        return Response(
            {
                "mensaje": f"Se han enviado {recordatorios_enviados} recordatorios de pago.",
                "viviendas_pendientes": viviendas_pendientes.count(),
                "recordatorios_enviados": recordatorios_enviados,
            }
        )


class PagoAdministracionViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar pagos de administración.

    Permite registrar, consultar y gestionar los pagos realizados por los propietarios
    para las cuotas de administración.
    """

    queryset = PagoAdministracion.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["vivienda", "cuota", "estado", "forma_pago"]
    search_fields = ["numero_referencia", "observaciones"]
    ordering_fields = ["fecha_pago", "monto_pagado", "fecha_registro"]
    ordering = ["-fecha_registro"]

    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if (
            self.action == "create"
            or self.action == "update"
            or self.action == "partial_update"
        ):
            return PagoAdministracionCreateSerializer
        elif self.action == "retrieve":
            return PagoAdministracionDetalladoSerializer
        return PagoAdministracionSerializer

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ["list", "retrieve", "mis_pagos"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Asigna automáticamente el empleado que registra el pago."""
        # Verificar si el usuario es un empleado
        try:
            empleado = self.request.user.empleado
            serializer.save(registrado_por=empleado)
        except (Empleado.DoesNotExist, AttributeError):
            serializer.save()

    @action(detail=False, methods=["get"])
    def mis_pagos(self, request):
        """
        Retorna los pagos asociados al propietario autenticado.
        """
        try:
            propietario = request.user.propietario
        except (Propietario.DoesNotExist, AttributeError):
            return Response(
                {"error": "Usuario no asociado a un propietario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener viviendas del propietario
        viviendas = propietario.viviendas.all()

        # Obtener pagos de esas viviendas
        pagos = PagoAdministracion.objects.filter(vivienda__in=viviendas)

        # Aplicar filtros adicionales si existen
        año = request.query_params.get("año")
        mes = request.query_params.get("mes")
        estado = request.query_params.get("estado")

        if año:
            pagos = pagos.filter(cuota__año=año)
        if mes:
            pagos = pagos.filter(cuota__mes=mes)
        if estado:
            pagos = pagos.filter(estado=estado)

        # Ordenar y paginar
        pagos = pagos.order_by("-fecha_registro")

        # Serializar
        page = self.paginate_queryset(pagos)
        if page is not None:
            serializer = PagoAdministracionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PagoAdministracionSerializer(pagos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        """
        Confirma un pago registrado.
        """
        pago = self.get_object()

        # Verificar que el pago esté en estado registrado
        if pago.estado != "registrado":
            return Response(
                {"error": "Solo se pueden confirmar pagos en estado 'registrado'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Actualizar estado y guardar
        pago.estado = "confirmado"

        # Verificar si hay un empleado asociado al usuario
        try:
            empleado = request.user.empleado
            pago.registrado_por = empleado
        except (Empleado.DoesNotExist, AttributeError):
            pass

        pago.save()

        serializer = PagoAdministracionDetalladoSerializer(pago)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        """
        Rechaza un pago registrado.
        """
        pago = self.get_object()

        # Verificar que el pago esté en estado registrado
        if pago.estado != "registrado":
            return Response(
                {"error": "Solo se pueden rechazar pagos en estado 'registrado'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Actualizar estado y guardar
        pago.estado = "rechazado"

        # Agregar motivo si se proporciona
        motivo = request.data.get("motivo")
        if motivo:
            pago.observaciones = (pago.observaciones or "") + f"\n[RECHAZADO] {motivo}"

        # Verificar si hay un empleado asociado al usuario
        try:
            empleado = request.user.empleado
            pago.registrado_por = empleado
        except (Empleado.DoesNotExist, AttributeError):
            pass

        pago.save()

        serializer = PagoAdministracionDetalladoSerializer(pago)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """
        Retorna estadísticas para el dashboard de pagos.
        """
        # Obtener pagos del mes actual
        hoy = date.today()
        mes_actual = hoy.month
        año_actual = hoy.year

        # Obtener cuota del mes actual
        try:
            cuota_actual = CuotaAdministracion.objects.get(
                año=año_actual, mes=mes_actual
            )
        except CuotaAdministracion.DoesNotExist:
            cuota_actual = None

        # Estadísticas generales
        total_viviendas = Vivienda.objects.count()

        # Si hay cuota actual, calcular estadísticas de pagos
        if cuota_actual:
            pagos_mes = PagoAdministracion.objects.filter(cuota=cuota_actual)
            pagos_realizados = pagos_mes.count()
            pagos_pendientes = total_viviendas - pagos_realizados

            # Monto recaudado
            monto_recaudado = (
                pagos_mes.filter(estado="confirmado").aggregate(
                    total=Sum("monto_pagado")
                )["total"]
                or 0
            )

            # Monto esperado
            monto_esperado = cuota_actual.valor_base * total_viviendas

            # Porcentaje de recaudación
            porcentaje_recaudacion = (
                round((pagos_realizados / total_viviendas) * 100, 2)
                if total_viviendas > 0
                else 0
            )
            porcentaje_monto = (
                round((monto_recaudado / monto_esperado) * 100, 2)
                if monto_esperado > 0
                else 0
            )
        else:
            pagos_realizados = 0
            pagos_pendientes = total_viviendas
            monto_recaudado = 0
            monto_esperado = 0
            porcentaje_recaudacion = 0
            porcentaje_monto = 0

        # Estadísticas históricas (últimos 6 meses)
        estadisticas_historicas = []

        for i in range(5, -1, -1):
            # Calcular fecha para mes anterior
            fecha_mes = date.today().replace(day=1) - timedelta(days=1)
            for _ in range(i):
                fecha_mes = fecha_mes.replace(day=1) - timedelta(days=1)

            mes = fecha_mes.month
            año = fecha_mes.year

            # Buscar cuota para ese mes
            try:
                cuota = CuotaAdministracion.objects.get(año=año, mes=mes)
                total_pagos = PagoAdministracion.objects.filter(cuota=cuota).count()
                monto = (
                    PagoAdministracion.objects.filter(
                        cuota=cuota, estado="confirmado"
                    ).aggregate(total=Sum("monto_pagado"))["total"]
                    or 0
                )

                # Calcular porcentaje
                porcentaje = (
                    round((total_pagos / total_viviendas) * 100, 2)
                    if total_viviendas > 0
                    else 0
                )

                estadisticas_historicas.append(
                    {
                        "mes": mes,
                        "año": año,
                        "nombre_mes": cuota.get_nombre_mes(mes),
                        "total_pagos": total_pagos,
                        "monto": monto,
                        "porcentaje": porcentaje,
                    }
                )
            except CuotaAdministracion.DoesNotExist:
                # Si no hay cuota para ese mes, agregar datos vacíos
                estadisticas_historicas.append(
                    {
                        "mes": mes,
                        "año": año,
                        "nombre_mes": CuotaAdministracion.get_nombre_mes(mes),
                        "total_pagos": 0,
                        "monto": 0,
                        "porcentaje": 0,
                    }
                )

        # Últimos pagos registrados
        ultimos_pagos = PagoAdministracion.objects.all().order_by("-fecha_registro")[:5]
        serializer_pagos = PagoAdministracionSerializer(ultimos_pagos, many=True)

        return Response(
            {
                "mes_actual": {
                    "mes": mes_actual,
                    "año": año_actual,
                    "nombre_mes": (
                        CuotaAdministracion.get_nombre_mes(mes_actual)
                        if cuota_actual
                        else ""
                    ),
                    "cuota_base": cuota_actual.valor_base if cuota_actual else 0,
                    "pagos_realizados": pagos_realizados,
                    "pagos_pendientes": pagos_pendientes,
                    "monto_recaudado": monto_recaudado,
                    "monto_esperado": monto_esperado,
                    "porcentaje_recaudacion": porcentaje_recaudacion,
                    "porcentaje_monto": porcentaje_monto,
                },
                "historico": estadisticas_historicas,
                "ultimos_pagos": serializer_pagos.data,
            }
        )

    @action(detail=False, methods=["get"])
    def reporte(self, request):
        """
        Genera un reporte de pagos según parámetros de filtrado.
        """
        # Obtener parámetros de filtrado
        año = request.query_params.get("año")
        mes = request.query_params.get("mes")

        # Filtros iniciales
        filters = {}
        if año:
            filters["cuota__año"] = año
        if mes:
            filters["cuota__mes"] = mes

        # Realizar consulta
        pagos = PagoAdministracion.objects.filter(**filters).order_by(
            "vivienda__manzana", "vivienda__numero"
        )

        # Aplicar más filtros si es necesario
        estado = request.query_params.get("estado")
        forma_pago = request.query_params.get("forma_pago")

        if estado:
            pagos = pagos.filter(estado=estado)
        if forma_pago:
            pagos = pagos.filter(forma_pago=forma_pago)

        # Serializar datos
        serializer = ReportePagosSerializer(pagos, many=True)

        # Calcular totales
        total_pagos = pagos.count()
        monto_total = pagos.aggregate(total=Sum("monto_pagado"))["total"] or 0

        # Agrupación por estado
        estados = pagos.values("estado").annotate(
            total=Count("estado"), monto=Sum("monto_pagado")
        )

        estados_dict = {}
        for estado in estados:
            estados_dict[estado["estado"]] = {
                "total": estado["total"],
                "monto": estado["monto"],
            }

        # Agrupación por forma de pago
        formas_pago = pagos.values("forma_pago").annotate(
            total=Count("forma_pago"), monto=Sum("monto_pagado")
        )

        formas_dict = {}
        for forma in formas_pago:
            formas_dict[forma["forma_pago"]] = {
                "total": forma["total"],
                "monto": forma["monto"],
            }

        return Response(
            {
                "filtros": {
                    "año": año,
                    "mes": mes,
                    "estado": estado,
                    "forma_pago": forma_pago,
                },
                "resumen": {
                    "total_pagos": total_pagos,
                    "monto_total": monto_total,
                    "por_estado": estados_dict,
                    "por_forma_pago": formas_dict,
                },
                "pagos": serializer.data,
            }
        )
