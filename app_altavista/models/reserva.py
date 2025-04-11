# app_altavista/models/reserva.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Reserva(models.Model):
    """
    Modelo que representa las reservas de áreas comunes realizadas por los propietarios.
    """

    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("confirmada", "Confirmada"),
        ("cancelada", "Cancelada"),
        ("completada", "Completada"),
        ("no_asistio", "No Asistió"),
    ]

    area = models.ForeignKey(
        "AreaComun",
        on_delete=models.CASCADE,
        related_name="reservas",
        verbose_name="Área común",
    )
    propietario = models.ForeignKey(
        "Propietario",
        on_delete=models.CASCADE,
        related_name="reservas",
        verbose_name="Propietario",
    )
    fecha_reserva = models.DateField(verbose_name="Fecha de reserva")
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    hora_fin = models.TimeField(verbose_name="Hora de fin")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="pendiente",
        verbose_name="Estado",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    numero_invitados = models.PositiveSmallIntegerField(
        default=0, verbose_name="Número de invitados"
    )
    motivo = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Motivo de la reserva"
    )
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de solicitud"
    )
    fecha_confirmacion = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de confirmación"
    )
    confirmada_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas_confirmadas",
        verbose_name="Confirmada por",
    )
    costo = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Costo"
    )
    pagada = models.BooleanField(default=False, verbose_name="Pagada")

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["fecha_reserva", "hora_inicio"]
        unique_together = ["area", "fecha_reserva", "hora_inicio"]
        indexes = [
            models.Index(fields=["fecha_reserva"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["propietario"]),
            models.Index(fields=["area"]),
        ]

    def __str__(self):
        return (
            f"{self.area} - {self.fecha_reserva} ({self.hora_inicio}-{self.hora_fin})"
        )

    def clean(self):
        """
        Validaciones personalizadas para la reserva.

        Raises:
            ValidationError: Si no cumple con las validaciones
        """
        # Validar que la hora de fin sea posterior a la hora de inicio
        if self.hora_inicio and self.hora_fin and self.hora_inicio >= self.hora_fin:
            raise ValidationError(
                {
                    "hora_fin": "La hora de finalización debe ser posterior a la hora de inicio"
                }
            )

        # Validar que la fecha de reserva sea futura (solo para nuevas reservas)
        today = timezone.now().date()
        if not self.pk and self.fecha_reserva and self.fecha_reserva < today:
            raise ValidationError(
                {
                    "fecha_reserva": "La fecha de reserva debe ser posterior a la fecha actual"
                }
            )

        # Validar que el área común permita reservas
        if self.area and not self.area.requiere_reserva:
            raise ValidationError({"area": "Esta área común no permite reservas"})

        # Validar disponibilidad (solo para nuevas reservas o cambios de horario/fecha)
        if (
            not self.pk
            or self._state.adding
            or self._initial_values.get("fecha_reserva") != self.fecha_reserva
            or self._initial_values.get("hora_inicio") != self.hora_inicio
            or self._initial_values.get("hora_fin") != self.hora_fin
        ):

            if not self.area.esta_disponible(
                self.fecha_reserva, self.hora_inicio, self.hora_fin
            ):
                raise ValidationError(
                    "El área no está disponible en el horario seleccionado"
                )

    def save(self, *args, **kwargs):
        # Guardar valores iniciales para validaciones
        if hasattr(self, "id"):
            try:
                self._initial_values = {
                    "fecha_reserva": Reserva.objects.get(id=self.id).fecha_reserva,
                    "hora_inicio": Reserva.objects.get(id=self.id).hora_inicio,
                    "hora_fin": Reserva.objects.get(id=self.id).hora_fin,
                }
            except Reserva.DoesNotExist:
                self._initial_values = {}
        else:
            self._initial_values = {}

        # Actualizar fecha de confirmación si se confirma la reserva
        if self.estado == "confirmada" and not self.fecha_confirmacion:
            self.fecha_confirmacion = timezone.now()

        # Actualizar costo si el área tiene tarifa
        if self.area and self.area.tarifa > 0 and self.costo == 0:
            self.costo = self.area.tarifa

        super().save(*args, **kwargs)

    @property
    def duracion_horas(self):
        """
        Calcula la duración de la reserva en horas.

        Returns:
            float: Duración en horas
        """
        import datetime

        delta = datetime.datetime.combine(
            datetime.date.today(), self.hora_fin
        ) - datetime.datetime.combine(datetime.date.today(), self.hora_inicio)
        return delta.total_seconds() / 3600

    @property
    def esta_activa(self):
        """
        Indica si la reserva está activa (pendiente o confirmada).

        Returns:
            bool: True si está activa, False si no
        """
        return self.estado in ["pendiente", "confirmada"]

    @property
    def es_hoy(self):
        """
        Indica si la reserva es para el día de hoy.

        Returns:
            bool: True si es hoy, False si no
        """
        return self.fecha_reserva == timezone.now().date()

    def cancelar(self, observacion=None):
        """
        Cancela la reserva.

        Args:
            observacion (str, optional): Motivo de la cancelación

        Returns:
            bool: True si se canceló correctamente, False si no
        """
        if self.estado not in ["pendiente", "confirmada"]:
            return False

        self.estado = "cancelada"

        if observacion:
            self.observaciones = (
                self.observaciones or ""
            ) + f"\n[Cancelación] {observacion}"

        self.save()
        return True

    def confirmar(self, empleado, observacion=None):
        """
        Confirma la reserva por parte de un empleado.

        Args:
            empleado: Objeto Empleado que confirma la reserva
            observacion (str, optional): Comentario adicional

        Returns:
            bool: True si se confirmó correctamente, False si no
        """
        if self.estado != "pendiente":
            return False

        self.estado = "confirmada"
        self.confirmada_por = empleado
        self.fecha_confirmacion = timezone.now()

        if observacion:
            self.observaciones = (
                self.observaciones or ""
            ) + f"\n[Confirmación] {observacion}"

        self.save()
        return True

    def marcar_completada(self):
        """
        Marca la reserva como completada después de su uso.

        Returns:
            bool: True si se marcó como completada, False si no
        """
        if self.estado != "confirmada":
            return False

        self.estado = "completada"
        self.save()
        return True

    def marcar_no_asistio(self):
        """
        Marca la reserva como no asistida cuando el propietario no se presentó.

        Returns:
            bool: True si se marcó como no asistida, False si no
        """
        if self.estado != "confirmada":
            return False

        self.estado = "no_asistio"
        self.save()
        return True

    def registrar_pago(self, monto=None):
        """
        Registra el pago de la reserva.

        Args:
            monto (Decimal, optional): Monto pagado. Si es None, usa el costo de la reserva.

        Returns:
            bool: True si se registró el pago, False si no
        """
        if self.pagada:
            return False

        if monto is None:
            monto = self.costo

        # Registrar el pago (podría integrarse con sistema financiero)
        from .finanzas import IngresoGasto

        IngresoGasto.objects.create(
            fecha=timezone.now().date(),
            tipo="ingreso",
            categoria="reserva_area_comun",
            descripcion=f"Pago de reserva: {self.area} - {self.fecha_reserva}",
            monto=monto,
        )

        self.pagada = True
        self.save()
        return True

    @classmethod
    def get_proximas_reservas(cls, dias=7):
        """
        Obtiene las próximas reservas para los siguientes días.

        Args:
            dias (int): Número de días a considerar

        Returns:
            QuerySet: Reservas próximas
        """
        import datetime

        hoy = timezone.now().date()
        fin = hoy + datetime.timedelta(days=dias)

        return cls.objects.filter(
            fecha_reserva__gte=hoy,
            fecha_reserva__lte=fin,
            estado__in=["pendiente", "confirmada"],
        ).order_by("fecha_reserva", "hora_inicio")

    @classmethod
    def get_reservas_vencidas(cls):
        """
        Obtiene las reservas pendientes que ya pasaron su fecha.

        Returns:
            QuerySet: Reservas pendientes vencidas
        """
        hoy = timezone.now().date()
        ahora = timezone.now().time()

        # Reservas de días anteriores
        reservas_antiguas = cls.objects.filter(
            fecha_reserva__lt=hoy, estado="pendiente"
        )

        # Reservas de hoy pero con hora de inicio ya pasada
        reservas_hoy = cls.objects.filter(
            fecha_reserva=hoy, hora_inicio__lt=ahora, estado="pendiente"
        )

        return (reservas_antiguas | reservas_hoy).order_by(
            "fecha_reserva", "hora_inicio"
        )


class ConfiguracionReservas(models.Model):
    """
    Modelo para configurar reglas y parámetros del sistema de reservas.
    """

    dias_anticipacion_min = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Días mínimos de anticipación",
        help_text="Días mínimos de anticipación para realizar una reserva",
    )
    dias_anticipacion_max = models.PositiveSmallIntegerField(
        default=30,
        verbose_name="Días máximos de anticipación",
        help_text="Días máximos de anticipación para realizar una reserva",
    )
    duracion_maxima_horas = models.PositiveSmallIntegerField(
        default=4,
        verbose_name="Duración máxima (horas)",
        help_text="Duración máxima de una reserva en horas",
    )
    reservas_max_semana = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="Máximo de reservas por semana",
        help_text="Máximo número de reservas que puede hacer un propietario por semana",
    )
    requiere_aprobacion = models.BooleanField(
        default=True,
        verbose_name="Requiere aprobación administrativa",
        help_text="Si es True, las reservas deben ser aprobadas por un administrador",
    )
    mensaje_politicas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Mensaje de políticas de reserva",
        help_text="Texto que se mostrará a los propietarios al hacer reservas",
    )
    areas_disponibles = models.ManyToManyField(
        "AreaComun",
        blank=True,
        related_name="configuraciones_reserva",
        verbose_name="Áreas disponibles para reserva",
    )

    class Meta:
        verbose_name = "Configuración de Reservas"
        verbose_name_plural = "Configuraciones de Reservas"

    def __str__(self):
        return "Configuración de Reservas"

    @classmethod
    def get_config(cls):
        """
        Obtiene o crea la configuración de reservas.

        Returns:
            ConfiguracionReservas: Configuración actual
        """
        config, created = cls.objects.get_or_create(pk=1)
        return config

    def validar_reserva(self, propietario, fecha_reserva, duracion_horas):
        """
        Valida si una reserva cumple con las reglas configuradas.

        Args:
            propietario: Objeto Propietario
            fecha_reserva (date): Fecha de la reserva
            duracion_horas (float): Duración en horas

        Returns:
            tuple: (bool, str) - (Es válida, mensaje de error)
        """
        import datetime

        hoy = timezone.now().date()

        # Validar anticipación mínima
        dias_anticipacion = (fecha_reserva - hoy).days
        if dias_anticipacion < self.dias_anticipacion_min:
            return (
                False,
                f"Debes reservar con al menos {self.dias_anticipacion_min} días de anticipación",
            )

        # Validar anticipación máxima
        if dias_anticipacion > self.dias_anticipacion_max:
            return (
                False,
                f"No puedes reservar con más de {self.dias_anticipacion_max} días de anticipación",
            )

        # Validar duración máxima
        if duracion_horas > self.duracion_maxima_horas:
            return (
                False,
                f"La duración máxima permitida es de {self.duracion_maxima_horas} horas",
            )

        # Validar máximo de reservas por semana
        if self.reservas_max_semana > 0:
            # Calcular inicio y fin de la semana de la fecha de reserva
            inicio_semana = fecha_reserva - datetime.timedelta(
                days=fecha_reserva.weekday()
            )
            fin_semana = inicio_semana + datetime.timedelta(days=6)

            # Contar reservas en esa semana
            reservas_semana = Reserva.objects.filter(
                propietario=propietario,
                fecha_reserva__gte=inicio_semana,
                fecha_reserva__lte=fin_semana,
                estado__in=["pendiente", "confirmada"],
            ).count()

            if reservas_semana >= self.reservas_max_semana:
                return (
                    False,
                    f"Has alcanzado el límite de {self.reservas_max_semana} reservas por semana",
                )

        return True, ""
