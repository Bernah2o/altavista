# app_altavista/models/administracion.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User


class Comunicado(models.Model):
    """
    Modelo que representa los comunicados oficiales de la administración.
    """
    TIPO_CHOICES = [
        ('general', 'General'),
        ('importante', 'Importante'),
        ('urgente', 'Urgente'),
        ('informativo', 'Informativo')
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    contenido = models.TextField(verbose_name="Contenido")
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='general',
        verbose_name="Tipo"
    )
    fecha_publicacion = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de publicación"
    )
    fecha_expiracion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de expiración"
    )
    autor = models.ForeignKey(
        'Empleado',
        on_delete=models.SET_NULL,
        null=True,
        related_name='comunicados_creados',
        verbose_name="Autor"
    )
    adjuntos = models.FileField(
        upload_to='comunicados/',
        null=True,
        blank=True,
        verbose_name="Archivos adjuntos"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Comunicado"
        verbose_name_plural = "Comunicados"
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"

    @property
    def esta_vigente(self):
        """Verifica si el comunicado está vigente."""
        now = timezone.now()
        if self.fecha_expiracion:
            return self.activo and now <= self.fecha_expiracion
        return self.activo


class Reunion(models.Model):
    """
    Modelo que representa las reuniones programadas por la administración.
    """
    TIPO_CHOICES = [
        ('ordinaria', 'Ordinaria'),
        ('extraordinaria', 'Extraordinaria'),
        ('informativa', 'Informativa'),
        ('comite', 'Comité')
    ]

    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('en_curso', 'En curso'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
        ('reprogramada', 'Reprogramada')
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de reunión"
    )
    fecha_hora = models.DateTimeField(verbose_name="Fecha y hora")
    duracion_estimada = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Duración estimada"
    )
    lugar = models.CharField(max_length=200, verbose_name="Lugar")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='programada',
        verbose_name="Estado"
    )
    organizador = models.ForeignKey(
        'Empleado',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reuniones_organizadas',
        verbose_name="Organizador"
    )
    asistentes = models.ManyToManyField(
        'Propietario',
        related_name='reuniones',
        blank=True,
        verbose_name="Asistentes"
    )
    acta = models.FileField(
        upload_to='actas_reunion/',
        null=True,
        blank=True,
        verbose_name="Acta de reunión"
    )
    documentos = models.FileField(
        upload_to='documentos_reunion/',
        null=True,
        blank=True,
        verbose_name="Documentos relacionados"
    )

    class Meta:
        verbose_name = "Reunión"
        verbose_name_plural = "Reuniones"
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.titulo} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

    @property
    def esta_proxima(self):
        """Verifica si la reunión está próxima (menos de 24 horas)."""
        return (
            self.estado == 'programada' and
            (self.fecha_hora - timezone.now()).total_seconds() <= 86400
        )


class Administracion(models.Model):
    """
    Modelo que representa la administración del conjunto residencial.
    """
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )
    administrador = models.ForeignKey(
        'Empleado',
        on_delete=models.SET_NULL,
        null=True,
        related_name='administraciones',
        verbose_name="Administrador"
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo electrónico"
    )
    horario_atencion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Horario de atención"
    )
    direccion = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Dirección"
    )
    fecha_inicio = models.DateField(
        verbose_name="Fecha de inicio de gestión"
    )
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de fin de gestión"
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="Administración activa"
    )

    class Meta:
        verbose_name = "Administración"
        verbose_name_plural = "Administraciones"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.nombre} ({self.administrador})"

    @property
    def esta_vigente(self):
        """Verifica si la administración está vigente."""
        today = timezone.now().date()
        if self.fecha_fin:
            return self.activa and today <= self.fecha_fin
        return self.activa


class CuotaAdministracion(models.Model):
    """
    Modelo que representa las cuotas mensuales de administración
    establecidas para cada periodo.
    """

    año = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
        verbose_name="Año",
    )
    mes = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)], verbose_name="Mes"
    )
    valor_base = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Valor base"
    )
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")
    recargo_mora = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0, verbose_name="Recargo por mora (%)"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_creacion = models.DateField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    creado_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cuotas_creadas",
        verbose_name="Creado por",
    )

    class Meta:
        verbose_name = "Cuota de Administración"
        verbose_name_plural = "Cuotas de Administración"
        ordering = ["-año", "-mes"]
        unique_together = ["año", "mes"]
        indexes = [
            models.Index(fields=["año", "mes"]),
            models.Index(fields=["fecha_vencimiento"]),
        ]

    def __str__(self):
        return f"Cuota {self.get_nombre_mes()} {self.año} - ${self.valor_base:,}"

    @staticmethod
    def get_nombre_mes(mes):
        """
        Retorna el nombre del mes según su número.

        Args:
            mes (int): Número del mes (1-12).

        Returns:
            str: Nombre del mes
        """
        meses = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]

        mes = max(1, min(mes, 12))  # Asegurar que esté entre 1 y 12
        return meses[mes - 1]

    @property
    def nombre_periodo(self):
        """Retorna el nombre del periodo (mes y año)."""
        return f"{self.get_nombre_mes(self.mes)} {self.año}"

    @property
    def esta_vencida(self):
        """Verifica si la fecha de vencimiento ya pasó."""
        return self.fecha_vencimiento < timezone.now().date()

    def calcular_valor_vivienda(self, vivienda):
        """
        Calcula el valor de la cuota para una vivienda específica.

        Args:
            vivienda: Objeto Vivienda

        Returns:
            Decimal: Valor de la cuota para la vivienda
        """
        return self.valor_base * vivienda.coeficiente_propiedad

    def calcular_valor_con_mora(self, vivienda):
        """
        Calcula el valor de la cuota con recargo de mora si aplica.

        Args:
            vivienda: Objeto Vivienda

        Returns:
            Decimal: Valor de la cuota con mora si aplica
        """
        valor_base = self.calcular_valor_vivienda(vivienda)

        if self.esta_vencida:
            recargo = valor_base * (self.recargo_mora / 100)
            return valor_base + recargo

        return valor_base

    @classmethod
    def generar_cuota_siguiente_mes(cls):
        """
        Genera automáticamente la cuota para el mes siguiente basándose
        en la cuota del mes actual.

        Returns:
            CuotaAdministracion: Nueva instancia de cuota generada o None si ya existe
        """
        import datetime

        # Obtener fecha para el mes siguiente
        hoy = datetime.date.today()
        if hoy.month == 12:
            siguiente_mes = 1
            siguiente_año = hoy.year + 1
        else:
            siguiente_mes = hoy.month + 1
            siguiente_año = hoy.year

        # Verificar si ya existe
        if cls.objects.filter(año=siguiente_año, mes=siguiente_mes).exists():
            return None

        # Obtener cuota actual
        try:
            cuota_actual = cls.objects.get(año=hoy.year, mes=hoy.month)

            # Generar fecha de vencimiento (mismo día del mes siguiente)
            dia_vencimiento = min(cuota_actual.fecha_vencimiento.day, 28)
            fecha_vencimiento = datetime.date(
                siguiente_año, siguiente_mes, dia_vencimiento
            )

            # Crear nueva cuota
            nueva_cuota = cls.objects.create(
                año=siguiente_año,
                mes=siguiente_mes,
                valor_base=cuota_actual.valor_base,
                fecha_vencimiento=fecha_vencimiento,
                recargo_mora=cuota_actual.recargo_mora,
                descripcion=f"Cuota generada automáticamente basada en {cuota_actual}",
            )

            return nueva_cuota

        except cls.DoesNotExist:
            return None


class PagoAdministracion(models.Model):
    """
    Modelo que representa los pagos de cuotas de administración
    realizados por los propietarios.
    """

    ESTADO_CHOICES = [
        ("registrado", "Registrado"),
        ("confirmado", "Confirmado"),
        ("rechazado", "Rechazado"),
    ]

    FORMA_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia Bancaria"),
        ("tarjeta", "Tarjeta de Crédito/Débito"),
        ("cheque", "Cheque"),
        ("otro", "Otro"),
    ]

    vivienda = models.ForeignKey(
        "Vivienda",
        on_delete=models.CASCADE,
        related_name="pagos",
        verbose_name="Vivienda",
    )
    cuota = models.ForeignKey(
        CuotaAdministracion,
        on_delete=models.CASCADE,
        related_name="pagos",
        verbose_name="Cuota",
    )
    fecha_pago = models.DateField(verbose_name="Fecha de pago")
    monto_pagado = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Monto pagado"
    )
    forma_pago = models.CharField(
        max_length=30, choices=FORMA_PAGO_CHOICES, verbose_name="Forma de pago"
    )
    numero_referencia = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Número de referencia"
    )
    comprobante = models.FileField(
        upload_to="comprobantes_pago/",
        blank=True,
        null=True,
        verbose_name="Comprobante",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="registrado",
        verbose_name="Estado",
    )
    registrado_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos_registrados",
        verbose_name="Registrado por",
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de registro"
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    class Meta:
        verbose_name = "Pago de Administración"
        verbose_name_plural = "Pagos de Administración"
        ordering = ["-fecha_pago", "-fecha_registro"]
        unique_together = ["vivienda", "cuota"]
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["fecha_pago"]),
            models.Index(fields=["vivienda", "estado"]),
        ]

    def __str__(self):
        return f"Pago {self.vivienda} - {self.cuota}"

    def clean(self):
        """
        Validaciones personalizadas para el pago.

        Raises:
            ValidationError: Si no cumple con las validaciones
        """
        from django.core.exceptions import ValidationError

        # Validar que el monto pagado sea mayor a cero
        if self.monto_pagado <= 0:
            raise ValidationError(
                {"monto_pagado": "El monto pagado debe ser mayor a cero"}
            )

        # Validar que no exista un pago confirmado para la misma vivienda y cuota
        if (
            not self.pk
            and PagoAdministracion.objects.filter(
                vivienda=self.vivienda, cuota=self.cuota, estado="confirmado"
            ).exists()
        ):
            raise ValidationError(
                "Ya existe un pago confirmado para esta vivienda y periodo"
            )

    def save(self, *args, **kwargs):
        # Si es un pago nuevo, verificar el valor correcto
        if not self.pk and not self.monto_pagado:
            self.monto_pagado = self.cuota.calcular_valor_vivienda(self.vivienda)

        # Si el pago se confirma, registrar transacción financiera
        if self.estado == "confirmado" and (
            not hasattr(self, "_initial_values")
            or self._initial_values.get("estado") != "confirmado"
        ):
            self._registrar_ingreso()

        # Si el pago pasa de confirmado a rechazado, anular transacción financiera
        if (
            hasattr(self, "_initial_values")
            and self._initial_values.get("estado") == "confirmado"
            and self.estado == "rechazado"
        ):
            self._anular_ingreso()

        # Guardar valores iniciales
        if hasattr(self, "id"):
            try:
                self._initial_values = {
                    "estado": PagoAdministracion.objects.get(id=self.id).estado,
                }
            except PagoAdministracion.DoesNotExist:
                self._initial_values = {}
        else:
            self._initial_values = {}

        super().save(*args, **kwargs)

    def _registrar_ingreso(self):
        """Registra el ingreso en el sistema financiero."""
        from .finanzas import IngresoGasto

        IngresoGasto.objects.create(
            fecha=self.fecha_pago,
            tipo="ingreso",
            categoria="cuota_administracion",
            descripcion=f"Pago de cuota de administración - {self.vivienda} - {self.cuota}",
            monto=self.monto_pagado,
            pago=self,
            estado="registrado",
        )

    def _anular_ingreso(self):
        """Anula el ingreso en el sistema financiero."""
        from .finanzas import IngresoGasto

        ingresos = IngresoGasto.objects.filter(pago=self, tipo="ingreso")
        for ingreso in ingresos:
            ingreso.estado = "anulado"
            ingreso.save()

    @property
    def diferencia_monto(self):
        """
        Calcula la diferencia entre el monto pagado y el valor de la cuota.

        Returns:
            Decimal: Diferencia (positiva si pagó más, negativa si pagó menos)
        """
        valor_cuota = self.cuota.calcular_valor_vivienda(self.vivienda)
        return self.monto_pagado - valor_cuota
