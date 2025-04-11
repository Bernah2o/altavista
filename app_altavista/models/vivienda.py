# app_altavista/models/vivienda.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import OuterRef, Exists
from datetime import date

from app_altavista.models.administracion import CuotaAdministracion, PagoAdministracion


class Vivienda(models.Model):
    """
    Modelo que representa cada casa en la propiedad horizontal.
    Todas son casas de dos plantas.
    """

    MANZANA_CHOICES = [
        ("A", "Manzana A"),
        ("B", "Manzana B"),
        ("C", "Manzana C"),
        ("D", "Manzana D"),
    ]

    manzana = models.CharField(
        max_length=1, choices=MANZANA_CHOICES, verbose_name="Manzana"
    )
    numero = models.CharField(max_length=10, verbose_name="Número")
    area_m2 = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Área total (m²)"
    )
    area_construida_m2 = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Área construida (m²)",
        help_text="Área total construida incluyendo ambas plantas",
    )
    coeficiente_propiedad = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Coeficiente de propiedad",
    )
    habitada = models.BooleanField(default=True, verbose_name="Habitada")
    tiene_ampliacion = models.BooleanField(
        default=False, verbose_name="Tiene ampliación"
    )
    fecha_entrega = models.DateField(
        null=True, blank=True, verbose_name="Fecha de entrega"
    )
    propietarios = models.ManyToManyField(
        "Propietario",
        through="PropietarioVivienda",
        related_name="viviendas",
        verbose_name="Propietarios",
    )

    class Meta:
        verbose_name = "Vivienda"
        verbose_name_plural = "Viviendas"
        ordering = ["manzana", "numero"]
        unique_together = ["manzana", "numero"]
        indexes = [
            models.Index(fields=["manzana", "numero"]),
        ]

    def __str__(self):
        return f"Casa {self.manzana}-{self.numero}"

    @property
    def identificacion_completa(self):
        """Retorna la identificación completa de la casa."""
        return f"Manzana {self.manzana} - Casa {self.numero}"

    def get_propietarios_activos(self):
        """Retorna los propietarios actuales de la casa."""
        return self.propietarios.filter(propietariovivienda__es_propietario=True)

    def get_incidencias_activas(self):
        """Retorna las incidencias activas asociadas a la casa."""
        return self.incidencias.filter(estado__in=["reportada", "en_proceso"])

    def get_pagos_pendientes(self):
        """Retorna los pagos pendientes de la casa."""

        cuotas = CuotaAdministracion.objects.filter(fecha_vencimiento__lte=date.today())

        pagos_realizados = PagoAdministracion.objects.filter(
            vivienda=self, cuota=OuterRef("pk")
        )

        return cuotas.filter(~Exists(pagos_realizados))

    def calcular_valor_cuota(self, cuota):
        """
        Calcula el valor de la cuota de administración para esta vivienda.

        Args:
            cuota: Objeto CuotaAdministracion

        Returns:
            Decimal: Valor de la cuota para esta vivienda
        """
        return cuota.valor_base * self.coeficiente_propiedad


class PropietarioVivienda(models.Model):
    """
    Modelo que representa la relación entre un propietario y una casa,
    manteniendo un historial completo de ocupación y propiedad.
    """

    propietario = models.ForeignKey(
        "Propietario",
        on_delete=models.CASCADE,
        verbose_name="Propietario",
        related_name="relaciones_vivienda",
    )
    vivienda = models.ForeignKey(
        "Vivienda",
        on_delete=models.CASCADE,
        verbose_name="Vivienda",
        related_name="relaciones_propietario",
    )
    fecha_inicio = models.DateField(verbose_name="Fecha de inicio")
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de finalización"
    )
    es_propietario = models.BooleanField(
        default=True,
        verbose_name="Es propietario",
        help_text="Si es False, se considera arrendatario",
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones",
        help_text="Notas adicionales sobre la ocupación o propiedad"
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    modificado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última modificación"
    )

    class Meta:
        verbose_name = "Relación Propietario-Vivienda"
        verbose_name_plural = "Relaciones Propietarios-Viviendas"
        unique_together = ["propietario", "vivienda"]
        indexes = [
            models.Index(fields=["propietario", "vivienda"]),
            models.Index(fields=["es_propietario"]),
        ]

    def __str__(self):
        relacion = "Propietario" if self.es_propietario else "Arrendatario"
        return f"{self.propietario} - {self.vivienda} ({relacion})"
