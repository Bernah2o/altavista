# app_altavista/models/ocupante.py
from django.db import models
from django.core.validators import MinValueValidator


class Vehiculo(models.Model):
    """Modelo que representa los vehículos asociados a una vivienda."""

    TIPO_CHOICES = [
        ('CARRO', 'Carro'),
        ('MOTO', 'Motocicleta'),
        ('BICICLETA', 'Bicicleta'),
        ('OTRO', 'Otro'),
    ]

    propietario = models.ForeignKey(
        'Propietario',
        on_delete=models.CASCADE,
        related_name='vehiculos',
        verbose_name='Propietario'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de vehículo'
    )
    marca = models.CharField(max_length=50, verbose_name='Marca')
    modelo = models.CharField(max_length=50, verbose_name='Modelo')
    placa = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Placa',
        null=True,
        blank=True
    )
    color = models.CharField(max_length=30, verbose_name='Color')
    fecha_registro = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de registro'
    )

    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        ordering = ['propietario', 'tipo', 'placa']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.marca} {self.modelo} ({self.placa or 'Sin placa'})"


class Mascota(models.Model):
    """Modelo que representa las mascotas asociadas a una vivienda."""

    TIPO_CHOICES = [
        ('PERRO', 'Perro'),
        ('GATO', 'Gato'),
        ('AVE', 'Ave'),
        ('OTRO', 'Otro'),
    ]

    propietario = models.ForeignKey(
        'Propietario',
        on_delete=models.CASCADE,
        related_name='mascotas',
        verbose_name='Propietario'
    )
    nombre = models.CharField(max_length=50, verbose_name='Nombre')
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de mascota'
    )
    raza = models.CharField(
        max_length=50,
        verbose_name='Raza',
        blank=True,
        null=True
    )
    fecha_registro = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de registro'
    )

    class Meta:
        verbose_name = 'Mascota'
        verbose_name_plural = 'Mascotas'
        ordering = ['propietario', 'tipo', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_display()} ({self.raza or 'Sin raza específica'})"


class MiembroFamiliar(models.Model):
    """Modelo que representa los miembros familiares que habitan en una vivienda."""

    PARENTESCO_CHOICES = [
        ('CONYUGE', 'Cónyuge'),
        ('HIJO', 'Hijo/a'),
        ('PADRE', 'Padre'),
        ('MADRE', 'Madre'),
        ('OTRO', 'Otro'),
    ]

    propietario = models.ForeignKey(
        'Propietario',
        on_delete=models.CASCADE,
        related_name='miembros_familiares',
        verbose_name='Propietario'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellido = models.CharField(max_length=100, verbose_name='Apellido')
    parentesco = models.CharField(
        max_length=20,
        choices=PARENTESCO_CHOICES,
        verbose_name='Parentesco'
    )
    fecha_nacimiento = models.DateField(verbose_name='Fecha de nacimiento')
    documento_identidad = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Documento de identidad'
    )

    class Meta:
        verbose_name = 'Miembro Familiar'
        verbose_name_plural = 'Miembros Familiares'
        ordering = ['propietario', 'apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.get_parentesco_display()}"


class PersonalServicio(models.Model):
    """Modelo que representa al personal de servicio que trabaja en una vivienda."""

    TIPO_SERVICIO_CHOICES = [
        ('DOMESTICO', 'Servicio Doméstico'),
        ('CONDUCTOR', 'Conductor'),
        ('JARDINERO', 'Jardinero'),
        ('OTRO', 'Otro'),
    ]

    propietario = models.ForeignKey(
        'Propietario',
        on_delete=models.CASCADE,
        related_name='personal_servicio',
        verbose_name='Propietario'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellido = models.CharField(max_length=100, verbose_name='Apellido')
    documento_identidad = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Documento de identidad'
    )
    tipo_servicio = models.CharField(
        max_length=20,
        choices=TIPO_SERVICIO_CHOICES,
        verbose_name='Tipo de servicio'
    )
    telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
        blank=True,
        null=True
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Personal de Servicio'
        verbose_name_plural = 'Personal de Servicio'
        ordering = ['propietario', 'apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.get_tipo_servicio_display()}"