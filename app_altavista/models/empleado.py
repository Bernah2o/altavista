# app_altavista/models/empleado.py
from django.db import models
from django.contrib.auth.models import User


class Empleado(models.Model):
    """
    Modelo que representa a los empleados que trabajan en la propiedad horizontal,
    como personal administrativo, mantenimiento, seguridad, etc.
    """

    CARGO_CHOICES = [
        ("administrador", "Administrador"),
        ("contador", "Contador"),
        ("seguridad", "Seguridad"),
        ("mantenimiento", "Mantenimiento"),
        ("aseo", "Aseo"),
        ("otro", "Otro"),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    documento_identidad = models.CharField(
        max_length=20, unique=True, verbose_name="Documento de identidad"
    )
    cargo = models.CharField(max_length=50, choices=CARGO_CHOICES, verbose_name="Cargo")
    fecha_contratacion = models.DateField(verbose_name="Fecha de contratación")
    fecha_terminacion = models.DateField(
        null=True, blank=True, verbose_name="Fecha de terminación"
    )
    salario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Salario"
    )
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    direccion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Dirección"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empleado",
        verbose_name="Usuario del sistema",
    )
    horario_entrada = models.TimeField(
        null=True, blank=True, verbose_name="Horario de entrada"
    )
    horario_salida = models.TimeField(
        null=True, blank=True, verbose_name="Horario de salida"
    )
    dias_trabajo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Ej: Lunes a Viernes, Fines de semana, etc.",
        verbose_name="Días de trabajo",
    )
    foto = models.ImageField(
        upload_to="empleados/", blank=True, null=True, verbose_name="Foto"
    )

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=["documento_identidad"]),
            models.Index(fields=["cargo"]),
            models.Index(fields=["activo"]),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.get_cargo_display()}"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del empleado."""
        return f"{self.nombre} {self.apellido}"

    @property
    def esta_trabajando(self):
        """
        Verifica si el empleado está trabajando actualmente.

        Returns:
            bool: True si está en horario laboral, False si no
        """
        import datetime

        if not self.activo or not self.horario_entrada or not self.horario_salida:
            return False

        now = datetime.datetime.now().time()
        return self.horario_entrada <= now <= self.horario_salida

    def get_seguimientos_incidencias(self):
        """
        Retorna los seguimientos de incidencias realizados por el empleado.

        Returns:
            QuerySet: Seguimientos ordenados por fecha
        """
        return self.seguimientos.all().order_by("-fecha_actualizacion")

    def get_tareas_pendientes(self):
        """
        Retorna las incidencias asignadas al empleado que están en proceso.

        Returns:
            QuerySet: Incidencias en proceso
        """
        from .incidencia import Incidencia

        return Incidencia.objects.filter(
            seguimientos__empleado=self, estado="en_proceso"
        ).distinct()


class RegistroAsistencia(models.Model):
    """
    Modelo para registrar la asistencia de los empleados.
    """

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name="asistencias",
        verbose_name="Empleado",
    )
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha")
    hora_entrada = models.TimeField(
        null=True, blank=True, verbose_name="Hora de entrada"
    )
    hora_salida = models.TimeField(null=True, blank=True, verbose_name="Hora de salida")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    class Meta:
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"
        ordering = ["-fecha", "-hora_entrada"]
        unique_together = ["empleado", "fecha"]

    def __str__(self):
        return f"{self.empleado} - {self.fecha}"

    @property
    def horas_trabajadas(self):
        """
        Calcula las horas trabajadas en el día.

        Returns:
            float: Horas trabajadas o None si no hay salida registrada
        """
        if not self.hora_entrada or not self.hora_salida:
            return None

        import datetime

        entrada = datetime.datetime.combine(self.fecha, self.hora_entrada)
        salida = datetime.datetime.combine(self.fecha, self.hora_salida)

        # Si la salida es al día siguiente
        if salida < entrada:
            salida = salida + datetime.timedelta(days=1)

        delta = salida - entrada
        return delta.total_seconds() / 3600

    @property
    def entrada_a_tiempo(self):
        """
        Verifica si el empleado llegó a tiempo.

        Returns:
            bool: True si llegó a tiempo, False si no
        """
        if not self.hora_entrada or not self.empleado.horario_entrada:
            return None

        return self.hora_entrada <= self.empleado.horario_entrada
