# app_altavista/models/incidencia.py
from django.db import models
from django.utils import timezone

from app_altavista.models.mantenimiento import Mantenimiento




class Incidencia(models.Model):
    """
    Modelo que representa incidencias, reportes o solicitudes
    realizadas por los propietarios.
    """

    TIPO_CHOICES = [
        ("mantenimiento", "Mantenimiento"),
        ("seguridad", "Seguridad"),
        ("convivencia", "Convivencia"),
        ("solicitud", "Solicitud"),
        ("queja", "Queja o Reclamo"),
        ("otro", "Otro"),
    ]

    PRIORIDAD_CHOICES = [
        ("baja", "Baja"),
        ("media", "Media"),
        ("alta", "Alta"),
        ("urgente", "Urgente"),
    ]

    ESTADO_CHOICES = [
        ("reportada", "Reportada"),
        ("en_proceso", "En Proceso"),
        ("resuelta", "Resuelta"),
        ("cancelada", "Cancelada"),
    ]

    propietario = models.ForeignKey(
        "Propietario",
        on_delete=models.CASCADE,
        related_name="incidencias",
        verbose_name="Propietario",
    )
    vivienda = models.ForeignKey(
        "Vivienda",
        on_delete=models.CASCADE,
        related_name="incidencias",
        verbose_name="Vivienda",
    )
    fecha_reporte = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de reporte"
    )
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    ubicacion = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Ubicación específica"
    )
    prioridad = models.CharField(
        max_length=20,
        choices=PRIORIDAD_CHOICES,
        default="media",
        verbose_name="Prioridad",
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADO_CHOICES,
        default="reportada",
        verbose_name="Estado",
    )
    fecha_ultima_actualizacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de última actualización"
    )
    fecha_cierre = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de cierre"
    )
    imagen = models.ImageField(
        upload_to="incidencias/", blank=True, null=True, verbose_name="Imagen"
    )
    requiere_mantenimiento = models.BooleanField(
        default=False, verbose_name="Requiere mantenimiento"
    )
    visible_para_propietario = models.BooleanField(
        default=True, verbose_name="Visible para el propietario"
    )

    class Meta:
        verbose_name = "Incidencia"
        verbose_name_plural = "Incidencias"
        ordering = ["-fecha_reporte"]
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["prioridad"]),
            models.Index(fields=["tipo"]),
            models.Index(fields=["fecha_reporte"]),
            models.Index(fields=["propietario"]),
            models.Index(fields=["vivienda"]),
        ]

    def __str__(self):
        return f"#{self.id} - {self.titulo} ({self.get_prioridad_display()})"

    def save(self, *args, **kwargs):
        # Si el estado cambia a resuelto o cancelado, registrar fecha de cierre
        if self.estado in ["resuelta", "cancelada"] and not self.fecha_cierre:
            self.fecha_cierre = timezone.now()

        # Si se reabre la incidencia, limpiar fecha de cierre
        if self.estado not in ["resuelta", "cancelada"] and self.fecha_cierre:
            self.fecha_cierre = None

        super().save(*args, **kwargs)

    @property
    def tiempo_abierta(self):
        """
        Calcula el tiempo que la incidencia ha estado abierta.

        Returns:
            timedelta: Tiempo transcurrido desde el reporte hasta el cierre o ahora
        """
        if self.fecha_cierre:
            return self.fecha_cierre - self.fecha_reporte
        return timezone.now() - self.fecha_reporte

    @property
    def tiempo_abierta_dias(self):
        """
        Calcula los días que la incidencia ha estado abierta.

        Returns:
            int: Días transcurridos
        """
        return self.tiempo_abierta.days

    @property
    def esta_vencida(self):
        """
        Verifica si la incidencia ha superado el tiempo recomendado de resolución.

        Returns:
            bool: True si está vencida, False si no
        """
        if self.estado in ["resuelta", "cancelada"]:
            return False

        # Definir límites de tiempo según prioridad (en días)
        limites = {"baja": 14, "media": 7, "alta": 3, "urgente": 1}

        return self.tiempo_abierta_dias > limites.get(self.prioridad, 7)

    def get_ultimo_seguimiento(self):
        """
        Retorna el último seguimiento registrado para la incidencia.

        Returns:
            SeguimientoIncidencia: Último seguimiento o None
        """
        return self.seguimientos.order_by("-fecha_actualizacion").first()

    def crear_seguimiento(self, empleado, comentario, nuevo_estado=None):
        """
        Crea un nuevo seguimiento para la incidencia.

        Args:
            empleado: Objeto Empleado que registra el seguimiento
            comentario (str): Comentario del seguimiento
            nuevo_estado (str, optional): Nuevo estado de la incidencia

        Returns:
            SeguimientoIncidencia: Nuevo seguimiento creado
        """
        if nuevo_estado and nuevo_estado in dict(self.ESTADO_CHOICES).keys():
            self.estado = nuevo_estado
            self.save()

        return SeguimientoIncidencia.objects.create(
            incidencia=self,
            empleado=empleado,
            comentario=comentario,
            estado_actual=self.estado,
        )

    def asignar_a_mantenimiento(self):
        """
        Crea un registro de mantenimiento basado en esta incidencia.

        Returns:
            Mantenimiento: Objeto de mantenimiento creado o None si ya existe
        """

        # Verificar si ya existe un mantenimiento para esta incidencia
        if hasattr(self, "mantenimiento"):
            return None

        # Crear registro de mantenimiento
        mantenimiento = Mantenimiento.objects.create(
            vivienda=self.vivienda,
            incidencia=self,
            descripcion=f"Mantenimiento por incidencia: {self.titulo}",
            estado="programado",
            fecha_programada=timezone.now().date(),
        )

        # Actualizar la incidencia
        self.requiere_mantenimiento = True
        self.save()

        return mantenimiento


class SeguimientoIncidencia(models.Model):
    """
    Modelo que representa el seguimiento o actualización de una incidencia.
    """

    incidencia = models.ForeignKey(
        Incidencia,
        on_delete=models.CASCADE,
        related_name="seguimientos",
        verbose_name="Incidencia",
    )
    empleado = models.ForeignKey(
        "Empleado",
        on_delete=models.CASCADE,
        related_name="seguimientos",
        verbose_name="Empleado",
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de actualización"
    )
    comentario = models.TextField(verbose_name="Comentario")
    estado_actual = models.CharField(max_length=30, verbose_name="Estado actual")
    archivo_adjunto = models.FileField(
        upload_to="seguimientos/", blank=True, null=True, verbose_name="Archivo adjunto"
    )
    visible_para_propietario = models.BooleanField(
        default=True, verbose_name="Visible para el propietario"
    )

    class Meta:
        verbose_name = "Seguimiento de Incidencia"
        verbose_name_plural = "Seguimientos de Incidencias"
        ordering = ["-fecha_actualizacion"]
        indexes = [
            models.Index(fields=["incidencia"]),
            models.Index(fields=["empleado"]),
            models.Index(fields=["fecha_actualizacion"]),
        ]

    def __str__(self):
        return f"Seguimiento de {self.incidencia} - {self.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}"

    @property
    def es_cambio_estado(self):
        """
        Verifica si este seguimiento representa un cambio de estado.

        Returns:
            bool: True si hubo cambio de estado, False si no
        """
        seguimiento_anterior = (
            SeguimientoIncidencia.objects.filter(
                incidencia=self.incidencia,
                fecha_actualizacion__lt=self.fecha_actualizacion,
            )
            .order_by("-fecha_actualizacion")
            .first()
        )

        if not seguimiento_anterior:
            # Si no hay seguimiento anterior, verificar si es diferente al estado inicial
            return self.estado_actual != "reportada"

        return self.estado_actual != seguimiento_anterior.estado_actual

    def notificar_propietario(self):
        """
        Envía una notificación al propietario sobre este seguimiento.

        Este método debería implementarse con la lógica real de notificaciones
        según el sistema de comunicación que se utilice (email, SMS, etc.).

        Returns:
            bool: True si se envió la notificación, False si no
        """
        if not self.visible_para_propietario:
            return False

        # Implementar lógica de notificación
        # Por ejemplo:
        # send_email(
        #     to=self.incidencia.propietario.email,
        #     subject=f"Actualización de su incidencia #{self.incidencia.id}",
        #     message=f"Su incidencia ha sido actualizada. Estado actual: {self.estado_actual}.\n\n{self.comentario}"
        # )

        return True


class CategoriaIncidencia(models.Model):
    """
    Modelo para categorizar y etiquetar incidencias para facilitar su
    clasificación y búsqueda.
    """

    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    color = models.CharField(
        max_length=7,
        default="#3498db",
        verbose_name="Color (HEX)",
        help_text="Código de color en formato hexadecimal (ej: #3498db)",
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Categoría de Incidencia"
        verbose_name_plural = "Categorías de Incidencias"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class IncidenciaCategoria(models.Model):
    """
    Modelo para relacionar incidencias con categorías (relación muchos a muchos).
    """

    incidencia = models.ForeignKey(
        Incidencia,
        on_delete=models.CASCADE,
        related_name="categorias_asignadas",
        verbose_name="Incidencia",
    )
    categoria = models.ForeignKey(
        CategoriaIncidencia,
        on_delete=models.CASCADE,
        related_name="incidencias_asignadas",
        verbose_name="Categoría",
    )
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de asignación"
    )
    asignado_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categorias_asignadas",
        verbose_name="Asignado por",
    )

    class Meta:
        verbose_name = "Asignación de Categoría"
        verbose_name_plural = "Asignaciones de Categorías"
        unique_together = ["incidencia", "categoria"]

    def __str__(self):
        return f"{self.incidencia} - {self.categoria}"
