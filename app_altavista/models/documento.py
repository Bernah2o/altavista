# app_altavista/models/documento.py
from django.db import models
from django.utils import timezone


class Documento(models.Model):
    """
    Modelo que representa documentos importantes de la propiedad horizontal
    como actas, circulares, reglamentos, etc.
    """

    TIPO_CHOICES = [
        ("acta", "Acta"),
        ("circular", "Circular"),
        ("reglamento", "Reglamento"),
        ("contrato", "Contrato"),
        ("financiero", "Documento Financiero"),
        ("legal", "Documento Legal"),
        ("otro", "Otro"),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo")
    fecha_publicacion = models.DateField(
        default=timezone.now, verbose_name="Fecha de publicación"
    )
    archivo = models.FileField(upload_to="documentos/", verbose_name="Archivo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    publico = models.BooleanField(
        default=True,
        verbose_name="Documento público",
        help_text="Si es público, todos los propietarios pueden verlo",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de modificación"
    )
    creado_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_creados",
        verbose_name="Creado por",
    )
    propietarios_vistos = models.ManyToManyField(
        "Propietario",
        through="VisualizacionDocumento",
        related_name="documentos_vistos",
        verbose_name="Propietarios que han visto",
    )

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-fecha_publicacion", "titulo"]
        indexes = [
            models.Index(fields=["tipo"]),
            models.Index(fields=["fecha_publicacion"]),
            models.Index(fields=["publico"]),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"

    @property
    def extension(self):
        """
        Retorna la extensión del archivo.

        Returns:
            str: Extensión del archivo o cadena vacía si no se puede determinar
        """
        import os

        name, extension = os.path.splitext(self.archivo.name)
        return extension.lower()

    @property
    def icono(self):
        """
        Retorna un nombre de icono según el tipo de documento.

        Returns:
            str: Nombre del icono para usar en la interfaz
        """
        extension = self.extension

        if extension in [".pdf"]:
            return "pdf"
        elif extension in [".doc", ".docx"]:
            return "word"
        elif extension in [".xls", ".xlsx"]:
            return "excel"
        elif extension in [".jpg", ".jpeg", ".png", ".gif"]:
            return "image"
        elif extension in [".ppt", ".pptx"]:
            return "powerpoint"
        elif extension in [".zip", ".rar"]:
            return "zip"
        else:
            return "document"

    def get_visualizaciones_count(self):
        """
        Retorna la cantidad de propietarios que han visto el documento.

        Returns:
            int: Número de visualizaciones
        """
        return self.visualizaciones.count()

    def registrar_visualizacion(self, propietario):
        """
        Registra que un propietario ha visto el documento.

        Args:
            propietario: Objeto Propietario

        Returns:
            VisualizacionDocumento: Objeto creado o actualizado
        """
        visualizacion, created = VisualizacionDocumento.objects.get_or_create(
            documento=self, propietario=propietario
        )

        if not created:
            visualizacion.fecha_visualizacion = timezone.now()
            visualizacion.contador += 1
            visualizacion.save()

        return visualizacion


class VisualizacionDocumento(models.Model):
    """
    Modelo que registra las visualizaciones de documentos por parte de los propietarios.
    """

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name="visualizaciones",
        verbose_name="Documento",
    )
    propietario = models.ForeignKey(
        "Propietario",
        on_delete=models.CASCADE,
        related_name="visualizaciones",
        verbose_name="Propietario",
    )
    fecha_visualizacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de visualización"
    )
    contador = models.PositiveIntegerField(
        default=1, verbose_name="Contador de visualizaciones"
    )

    class Meta:
        verbose_name = "Visualización de Documento"
        verbose_name_plural = "Visualizaciones de Documentos"
        unique_together = ["documento", "propietario"]
        ordering = ["-fecha_visualizacion"]

    def __str__(self):
        return f"{self.propietario} visualizó {self.documento}"


class Carpeta(models.Model):
    """
    Modelo para organizar los documentos en carpetas/categorías.
    """

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    carpeta_padre = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcarpetas",
        verbose_name="Carpeta padre",
    )
    publico = models.BooleanField(default=True, verbose_name="Carpeta pública")
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    creado_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carpetas_creadas",
        verbose_name="Creado por",
    )

    class Meta:
        verbose_name = "Carpeta"
        verbose_name_plural = "Carpetas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def ruta_completa(self):
        """
        Retorna la ruta completa de la carpeta.

        Returns:
            str: Ruta completa (ej: "Documentos legales > Contratos")
        """
        if not self.carpeta_padre:
            return self.nombre

        return f"{self.carpeta_padre.ruta_completa} > {self.nombre}"

    def get_documentos(self):
        """
        Retorna todos los documentos en esta carpeta.

        Returns:
            QuerySet: Documentos en la carpeta
        """
        return self.documentos.all()

    def get_todas_subcarpetas(self):
        """
        Retorna todas las subcarpetas recursivamente.

        Returns:
            list: Lista de todas las subcarpetas
        """
        result = list(self.subcarpetas.all())
        for subcarpeta in self.subcarpetas.all():
            result.extend(subcarpeta.get_todas_subcarpetas())
        return result

    def get_todos_documentos(self):
        """
        Retorna todos los documentos de esta carpeta y sus subcarpetas.

        Returns:
            QuerySet: Todos los documentos
        """
        from django.db.models import Q

        # Iniciar con los documentos directos
        query = Q(carpeta=self)

        # Agregar documentos de subcarpetas
        for subcarpeta in self.get_todas_subcarpetas():
            query |= Q(carpeta=subcarpeta)

        return Documento.objects.filter(query)


class DocumentoCarpeta(models.Model):
    """
    Modelo para relacionar documentos con carpetas.
    """

    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name="carpetas_asignadas",
        verbose_name="Documento",
    )
    carpeta = models.ForeignKey(
        Carpeta,
        on_delete=models.CASCADE,
        related_name="documentos",
        verbose_name="Carpeta",
    )
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de asignación"
    )

    class Meta:
        verbose_name = "Documento en Carpeta"
        verbose_name_plural = "Documentos en Carpetas"
        unique_together = ["documento", "carpeta"]

    def __str__(self):
        return f"{self.documento} en {self.carpeta}"
