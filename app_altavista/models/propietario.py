# app_altavista/models/propietario.py
from django.db import models
from django.contrib.auth.models import User


class Propietario(models.Model):
    """
    Modelo que representa a los propietarios o residentes de las viviendas
    en la propiedad horizontal.
    """

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    documento_identidad = models.CharField(
        max_length=20, unique=True, verbose_name="Documento de identidad"
    )
    telefono = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Teléfono"
    )
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    fecha_registro = models.DateField(
        auto_now_add=True, verbose_name="Fecha de registro"
    )
    usuario = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario del sistema",
        related_name="propietario",
    )

    class Meta:
        verbose_name = "Propietario"
        verbose_name_plural = "Propietarios"
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=["documento_identidad"]),
            models.Index(fields=["apellido", "nombre"]),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del propietario."""
        return f"{self.nombre} {self.apellido}"

    def get_viviendas(self):
        """Retorna todas las viviendas asociadas al propietario."""
        return self.viviendas.all()

    def get_vehiculos(self):
        """Retorna todos los vehículos asociados al propietario."""
        return self.vehiculos.all()

    def get_incidencias_activas(self):
        """Retorna las incidencias activas reportadas por el propietario."""
        return self.incidencias.filter(estado__in=["reportada", "en_proceso"])

    def tiene_pagos_pendientes(self):
        """Verifica si el propietario tiene pagos pendientes en alguna de sus viviendas."""
        for vivienda in self.get_viviendas():
            if vivienda.get_pagos_pendientes().exists():
                return True
        return False
