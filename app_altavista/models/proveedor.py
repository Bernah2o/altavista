# app_altavista/models/proveedor.py
from django.db import models

class Proveedor(models.Model):
    """Modelo que representa a los proveedores de servicios y productos
    para la propiedad horizontal.
    """

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('bloqueado', 'Bloqueado')
    ]

    TIPO_CHOICES = [
        ('servicios', 'Servicios'),
        ('productos', 'Productos'),
        ('ambos', 'Ambos')
    ]

    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre o Razón Social"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='servicios',
        verbose_name="Tipo de Proveedor"
    )
    nit = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="NIT o Documento"
    )
    direccion = models.CharField(
        max_length=255,
        verbose_name="Dirección"
    )
    telefono = models.CharField(
        max_length=20,
        verbose_name="Teléfono"
    )
    email = models.EmailField(
        verbose_name="Correo Electrónico"
    )
    contacto_nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Contacto",
        help_text="Nombre de la persona de contacto"
    )
    contacto_telefono = models.CharField(
        max_length=20,
        verbose_name="Teléfono del Contacto"
    )
    servicios_productos = models.TextField(
        verbose_name="Servicios/Productos",
        help_text="Descripción de los servicios o productos que ofrece"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activo',
        verbose_name="Estado"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['tipo']),
            models.Index(fields=['nit'])
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    def clean(self):
        """Validaciones personalizadas para el proveedor."""
        from django.core.exceptions import ValidationError

        # Validar formato del NIT
        if not self.nit.replace('-', '').isdigit():
            raise ValidationError({
                'nit': 'El NIT debe contener solo números y guiones.'
            })

    @property
    def esta_activo(self):
        """Indica si el proveedor está activo."""
        return self.estado == 'activo'