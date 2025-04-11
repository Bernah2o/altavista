# app_altavista/serializers/administracion_serializers.py
from rest_framework import serializers
from django.utils import timezone
from django.db.models import Count, Sum, Max
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models import Count, Sum


from app_altavista.models.administracion import (
    Administracion,
    Comunicado,
    CuotaAdministracion,
    PagoAdministracion,
    Reunion,
)
from app_altavista.models.vivienda import Vivienda


class CuotaAdministracionSerializer(serializers.ModelSerializer):
    """Serializador para el modelo CuotaAdministracion."""

    class Meta:
        model = CuotaAdministracion
        fields = "__all__"


class CuotaAdministracionDetalladaSerializer(CuotaAdministracionSerializer):
    """Serializador detallado para el modelo CuotaAdministracion."""

    mes_display = serializers.CharField(source="get_nombre_mes", read_only=True)
    estado_pagos = serializers.SerializerMethodField()

    class Meta:
        model = CuotaAdministracion
        fields = [
            "id",
            "año",
            "mes",
            "valor_base",
            "fecha_vencimiento",
            "recargo_mora",
            "descripcion",
            "fecha_creacion",
            "creado_por",
            "mes_display",
            "estado_pagos",
        ]

    def get_estado_pagos(self, obj):
        """Calcula el estado de los pagos para la cuota."""
        total_viviendas = Vivienda.objects.count()
        pagos = PagoAdministracion.objects.filter(cuota=obj)
        pagos_realizados = pagos.count()

        return {
            "total_viviendas": total_viviendas,
            "pagos_realizados": pagos_realizados,
            "pagos_pendientes": total_viviendas - pagos_realizados,
            "monto_recaudado": pagos.filter(estado="confirmado").aggregate(
                total=Sum("monto_pagado")
            )["total"]
            or 0,
        }


class ComunicadoSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Comunicado."""

    autor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Comunicado
        fields = "__all__"

    def get_autor_nombre(self, obj):
        if obj.autor:
            return f"{obj.autor.user.first_name} {obj.autor.user.last_name}"
        return None


class ReunionSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Reunion."""

    organizador_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Reunion
        fields = "__all__"

    def get_organizador_nombre(self, obj):
        if obj.organizador:
            return f"{obj.organizador.user.first_name} {obj.organizador.user.last_name}"
        return None


class ReunionDetalladaSerializer(ReunionSerializer):
    """Serializador detallado para el modelo Reunion."""

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    asistentes_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Reunion
        fields = [
            "id",
            "titulo",
            "fecha",
            "hora",
            "lugar",
            "tipo",
            "estado",
            "descripcion",
            "organizador",
            "organizador_nombre",
            "asistentes",
            "estado_display",
            "tipo_display",
            "asistentes_detalle",
        ]

    def get_asistentes_detalle(self, obj):
        return [
            {
                "id": asistente.id,
                "nombre": f"{asistente.user.first_name} {asistente.user.last_name}",
                "tipo": asistente.__class__.__name__,
            }
            for asistente in obj.asistentes.all()
        ]


class AdministracionSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Administracion."""

    class Meta:
        model = Administracion
        fields = "__all__"


class AdministracionDetalladaSerializer(AdministracionSerializer):
    """Serializador detallado para el modelo Administracion."""

    comunicados = ComunicadoSerializer(many=True, read_only=True)
    reuniones = ReunionSerializer(many=True, read_only=True)

    class Meta:
        model = Administracion
        fields = [
            "id",
            "nombre",
            "descripcion",
            "fecha_creacion",
            "comunicados",
            "reuniones"
        ]


class PagoAdministracionCreateSerializer(serializers.ModelSerializer):
    """Serializador para crear pagos de administración."""

    class Meta:
        model = PagoAdministracion
        fields = [
            "vivienda",
            "cuota",
            "monto_pagado",
            "fecha_pago",
            "forma_pago",
            "comprobante",
            "observaciones",
        ]

    def validate(self, data):
        """Validación personalizada para el pago de administración."""
        vivienda = data.get("vivienda")
        cuota = data.get("cuota")
        monto_pagado = data.get("monto_pagado")

        # Verificar que la vivienda existe
        if not Vivienda.objects.filter(id=vivienda.id).exists():
            raise serializers.ValidationError("La vivienda especificada no existe.")

        # Verificar que no exista un pago confirmado para esta vivienda y cuota
        if PagoAdministracion.objects.filter(
            vivienda=vivienda, cuota=cuota, estado="confirmado"
        ).exists():
            raise serializers.ValidationError(
                "Ya existe un pago confirmado para esta cuota."
            )

        # Calcular el valor esperado de la cuota para la vivienda
        valor_esperado = cuota.calcular_valor_con_mora(vivienda)

        # Verificar que el monto pagado sea correcto
        if monto_pagado < valor_esperado:
            raise serializers.ValidationError(
                f"El monto pagado debe ser al menos {valor_esperado}"
            )

        # Establecer el estado inicial como 'registrado'
        data["estado"] = "registrado"

        # Si no se proporciona fecha de pago, usar la fecha actual
        if "fecha_pago" not in data:
            data["fecha_pago"] = timezone.now().date()

        return data


class PagoAdministracionDetalladoSerializer(PagoAdministracionCreateSerializer):
    """Serializador detallado para el modelo PagoAdministracion."""

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    forma_pago_display = serializers.CharField(
        source="get_forma_pago_display", read_only=True
    )
    vivienda_detalle = serializers.SerializerMethodField()
    cuota_detalle = serializers.SerializerMethodField()
    dias_retraso = serializers.SerializerMethodField()
    monto_pendiente = serializers.SerializerMethodField()

    class Meta(PagoAdministracionCreateSerializer.Meta):
        fields = PagoAdministracionCreateSerializer.Meta.fields + [
            "estado",
            "estado_display",
            "forma_pago_display",
            "vivienda_detalle",
            "cuota_detalle",
            "dias_retraso",
            "monto_pendiente",
        ]

    def get_vivienda_detalle(self, obj):
        vivienda = obj.vivienda
        return {
            "id": vivienda.id,
            "identificador": vivienda.identificador,
            "tipo": vivienda.get_tipo_display(),
            "area": vivienda.area,
        }

    def get_cuota_detalle(self, obj):
        cuota = obj.cuota
        return {
            "id": cuota.id,
            "mes": cuota.mes,
            "anio": cuota.anio,
            "mes_display": cuota.get_nombre_mes(),
            "valor_base": cuota.valor_base,
        }

    def get_dias_retraso(self, obj):
        if obj.fecha_pago and obj.cuota:
            fecha_limite = obj.cuota.fecha_limite
            if obj.fecha_pago > fecha_limite:
                return (obj.fecha_pago - fecha_limite).days
        return 0

    def get_monto_pendiente(self, obj):
        if obj.cuota:
            valor_esperado = obj.cuota.calcular_valor_con_mora(obj.vivienda)
            return max(0, valor_esperado - obj.monto_pagado)
        return 0


class PagoAdministracionSerializer(serializers.ModelSerializer):
    """Serializador base para el modelo PagoAdministracion."""

    class Meta:
        model = PagoAdministracion
        fields = [
            "id",
            "vivienda",
            "cuota",
            "monto_pagado",
            "fecha_pago",
            "estado",
            "forma_pago",
            "comprobante",
            "observaciones",
        ]


class ReportePagosSerializer(serializers.Serializer):
    """Serializador para generar reportes de pagos de administración."""

    fecha_inicio = serializers.DateField(required=True)
    fecha_fin = serializers.DateField(required=True)
    total_recaudado = serializers.SerializerMethodField()
    total_pendiente = serializers.SerializerMethodField()
    pagos_por_estado = serializers.SerializerMethodField()
    pagos_por_mes = serializers.SerializerMethodField()
    pagos_por_vivienda = serializers.SerializerMethodField()

    def get_total_recaudado(self, obj):
        return (
            PagoAdministracion.objects.filter(
                fecha_pago__range=[obj["fecha_inicio"], obj["fecha_fin"]],
                estado="confirmado",
            ).aggregate(total=Sum("monto_pagado"))["total"]
            or 0
        )

    def get_total_pendiente(self, obj):
        cuotas_periodo = CuotaAdministracion.objects.filter(
            fecha_limite__range=[obj["fecha_inicio"], obj["fecha_fin"]]
        )
        total_esperado = sum(cuota.calcular_valor_total() for cuota in cuotas_periodo)
        return max(0, total_esperado - self.get_total_recaudado(obj))

    def get_pagos_por_estado(self, obj):
        return (
            PagoAdministracion.objects.filter(
                fecha_pago__range=[obj["fecha_inicio"], obj["fecha_fin"]]
            )
            .values("estado")
            .annotate(cantidad=Count("id"), monto_total=Sum("monto_pagado"))
        )

    def get_pagos_por_mes(self, obj):
        return (
            PagoAdministracion.objects.filter(
                fecha_pago__range=[obj["fecha_inicio"], obj["fecha_fin"]]
            )
            .annotate(mes=ExtractMonth("fecha_pago"), anio=ExtractYear("fecha_pago"))
            .values("mes", "anio")
            .annotate(cantidad=Count("id"), monto_total=Sum("monto_pagado"))
            .order_by("anio", "mes")
        )

    def get_pagos_por_vivienda(self, obj):
        return (
            PagoAdministracion.objects.filter(
                fecha_pago__range=[obj["fecha_inicio"], obj["fecha_fin"]]
            )
            .values("vivienda__identificador", "vivienda__tipo")
            .annotate(
                pagos_realizados=Count("id"),
                monto_total=Sum("monto_pagado"),
                ultimo_pago=Max("fecha_pago"),
            )
            .order_by("vivienda__identificador")
        )

    def validate(self, data):
        if data["fecha_inicio"] > data["fecha_fin"]:
            raise serializers.ValidationError(
                "La fecha de inicio debe ser anterior a la fecha fin"
            )
        return data
