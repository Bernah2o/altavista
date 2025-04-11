# app_altavista/models/area_comun.py
from django.db import models


class AreaComun(models.Model):
    """
    Modelo que representa las áreas comunes de la propiedad horizontal
    como salones sociales, piscina, gimnasio, etc.
    """

    TIPO_CHOICES = [
        ("recreativa", "Área Recreativa"),
        ("social", "Área Social"),
        ("deportiva", "Área Deportiva"),
        ("servicio", "Área de Servicio"),
        ("otro", "Otro"),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="social",
        verbose_name="Tipo de área",
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    capacidad = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Capacidad"
    )
    requiere_reserva = models.BooleanField(
        default=False, verbose_name="Requiere reserva"
    )
    horario_apertura = models.TimeField(
        null=True, blank=True, verbose_name="Horario de apertura"
    )
    horario_cierre = models.TimeField(
        null=True, blank=True, verbose_name="Horario de cierre"
    )
    esta_activa = models.BooleanField(default=True, verbose_name="Está activa")
    ubicacion = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Ubicación"
    )
    imagen = models.ImageField(
        upload_to="areas_comunes/", blank=True, null=True, verbose_name="Imagen"
    )
    reglas_uso = models.TextField(blank=True, null=True, verbose_name="Reglas de uso")
    tarifa = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Tarifa de uso"
    )

    class Meta:
        verbose_name = "Área Común"
        verbose_name_plural = "Áreas Comunes"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["tipo"]),
            models.Index(fields=["requiere_reserva"]),
            models.Index(fields=["esta_activa"]),
        ]

    def __str__(self):
        return self.nombre

    @property
    def horarios_formateados(self):
        """Retorna los horarios formateados."""
        apertura = (
            self.horario_apertura.strftime("%I:%M %p")
            if self.horario_apertura
            else "N/A"
        )
        cierre = (
            self.horario_cierre.strftime("%I:%M %p") if self.horario_cierre else "N/A"
        )
        return f"{apertura} - {cierre}"

    def esta_disponible(self, fecha, hora_inicio, hora_fin):
        """
        Verifica si el área común está disponible para reserva
        en la fecha y horario especificados.

        Args:
            fecha (date): Fecha para verificar disponibilidad
            hora_inicio (time): Hora de inicio deseada
            hora_fin (time): Hora de fin deseada

        Returns:
            bool: True si está disponible, False si no
        """
        if not self.requiere_reserva or not self.esta_activa:
            return False

        # Verificar horario de operación
        if (self.horario_apertura and hora_inicio < self.horario_apertura) or (
            self.horario_cierre and hora_fin > self.horario_cierre
        ):
            return False

        # Verificar colisiones con otras reservas
        colisiones = (
            self.reservas.filter(fecha_reserva=fecha, estado="confirmada")
            .filter(
                # Alguna parte de la nueva reserva se traslapa con una existente
                models.Q(
                    # Caso 1: hora_inicio está dentro de una reserva existente
                    hora_inicio__lt=hora_fin,
                    hora_fin__gt=hora_inicio,
                )
                | models.Q(
                    # Caso 2: hora_fin está dentro de una reserva existente
                    hora_inicio__lt=hora_fin,
                    hora_fin__gt=hora_inicio,
                )
                | models.Q(
                    # Caso 3: la nueva reserva abarca completamente una existente
                    hora_inicio__lte=models.F("hora_inicio"),
                    hora_fin__gte=models.F("hora_fin"),
                )
            )
            .exists()
        )

        return not colisiones

    def get_reservas_del_dia(self, fecha):
        """
        Retorna todas las reservas confirmadas para una fecha específica.

        Args:
            fecha (date): Fecha para consultar las reservas

        Returns:
            QuerySet: Reservas confirmadas para la fecha
        """
        return self.reservas.filter(fecha_reserva=fecha, estado="confirmada").order_by(
            "hora_inicio"
        )

    def get_proximos_mantenimientos(self):
        """
        Retorna los próximos mantenimientos programados para esta área común.

        Returns:
            QuerySet: Mantenimientos programados
        """
        from datetime import date

        return self.mantenimientos.filter(
            fecha_programada__gte=date.today(), estado__in=["programado", "en_proceso"]
        ).order_by("fecha_programada")


class ElementoAreaComun(models.Model):
    """
    Modelo que representa los elementos o activos que pertenecen a un área común,
    como muebles, equipos, elementos decorativos, etc.
    """

    area_comun = models.ForeignKey(
        AreaComun,
        on_delete=models.CASCADE,
        related_name="elementos",
        verbose_name="Área común",
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre del elemento")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_adquisicion = models.DateField(
        blank=True, null=True, verbose_name="Fecha de adquisición"
    )
    valor = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor"
    )
    estado = models.CharField(max_length=50, default="Bueno", verbose_name="Estado")
    imagen = models.ImageField(
        upload_to="elementos_areas/", blank=True, null=True, verbose_name="Imagen"
    )

    class Meta:
        verbose_name = "Elemento de Área Común"
        verbose_name_plural = "Elementos de Áreas Comunes"
        ordering = ["area_comun", "nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.area_comun}"
