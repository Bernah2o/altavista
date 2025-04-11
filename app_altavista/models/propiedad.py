# app_altavista/models/propiedad.py
from django.db import models


class PropiedadHorizontal(models.Model):
    """
    Modelo que representa los datos generales de la propiedad horizontal.
    Contiene información administrativa y legal de todo el conjunto residencial.
    """

    nombre = models.CharField(max_length=200, verbose_name="Nombre de la propiedad")
    nit = models.CharField(max_length=20, unique=True, verbose_name="NIT")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    telefono = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Teléfono"
    )
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    fecha_constitucion = models.DateField(verbose_name="Fecha de constitución")
    representante_legal = models.CharField(
        max_length=100, verbose_name="Representante legal"
    )
    cuenta_bancaria = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Cuenta bancaria"
    )
    banco = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Banco"
    )
    total_viviendas = models.PositiveIntegerField(
        default=160, verbose_name="Total de viviendas"
    )

    class Meta:
        verbose_name = "Propiedad Horizontal"
        verbose_name_plural = "Propiedades Horizontales"

    def __str__(self):
        return self.nombre


class ConfiguracionGeneral(models.Model):
    """
    Modelo para almacenar configuraciones generales del sistema.
    """

    TIPO_CHOICES = [
        ("texto", "Texto"),
        ("numero", "Número"),
        ("fecha", "Fecha"),
        ("booleano", "Booleano"),
        ("json", "JSON"),
    ]

    propiedad = models.OneToOneField(
        PropiedadHorizontal,
        on_delete=models.CASCADE,
        related_name="configuracion",
        null=True,
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la configuración")
    clave = models.SlugField(max_length=50, unique=True, verbose_name="Clave")
    valor = models.TextField(verbose_name="Valor")
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default="texto",
        verbose_name="Tipo de dato",
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Configuración General"
        verbose_name_plural = "Configuraciones Generales"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre}: {self.valor[:30]}"

    @property
    def valor_tipado(self):
        """
        Devuelve el valor convertido al tipo de dato correspondiente.

        Returns:
            El valor convertido según el tipo especificado.
        """
        import json
        from datetime import datetime

        if self.tipo == "texto":
            return self.valor
        elif self.tipo == "numero":
            try:
                if "." in self.valor:
                    return float(self.valor)
                return int(self.valor)
            except (ValueError, TypeError):
                return 0
        elif self.tipo == "fecha":
            try:
                return datetime.strptime(self.valor, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return None
        elif self.tipo == "booleano":
            return self.valor.lower() in ("true", "yes", "si", "1", "t", "y", "s")
        elif self.tipo == "json":
            try:
                return json.loads(self.valor)
            except (ValueError, TypeError):
                return {}
        return self.valor
