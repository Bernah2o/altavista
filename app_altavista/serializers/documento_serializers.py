# app_altavista/serializers/documento_serializers.py
from rest_framework import serializers
from ..models.documento import (
    Documento,
    VisualizacionDocumento,
    Carpeta,
    DocumentoCarpeta,
)


class DocumentoSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Documento."""

    class Meta:
        model = Documento
        fields = "__all__"


class VisualizacionDocumentoSerializer(serializers.ModelSerializer):
    """Serializador para el modelo VisualizacionDocumento."""

    class Meta:
        model = VisualizacionDocumento
        fields = "__all__"


class CarpetaSerializer(serializers.ModelSerializer):
    """Serializador básico para el modelo Carpeta."""

    class Meta:
        model = Carpeta
        fields = "__all__"


class DocumentoCarpetaSerializer(serializers.ModelSerializer):
    """Serializador para el modelo DocumentoCarpeta."""

    class Meta:
        model = DocumentoCarpeta
        fields = "__all__"


class DocumentoDetalladoSerializer(DocumentoSerializer):
    """Serializador detallado para el modelo Documento."""

    visualizaciones = VisualizacionDocumentoSerializer(many=True, read_only=True)
    carpetas = CarpetaSerializer(many=True, read_only=True)

    class Meta(DocumentoSerializer.Meta):
        fields = [
            "id",
            "titulo",
            "descripcion",
            "archivo",
            "fecha_creacion",
            "fecha_modificacion",
            "creado_por",
            "modificado_por",
            "visualizaciones",
            "carpetas",
        ]


class CarpetaDetalladaSerializer(CarpetaSerializer):
    """Serializador detallado para el modelo Carpeta."""

    documentos = DocumentoSerializer(many=True, read_only=True)

    class Meta(CarpetaSerializer.Meta):
        fields = [
            "id",
            "nombre",
            "descripcion",
            "creado_por",
            "modificado_por",
            "fecha_creacion",
            "fecha_modificacion",
            "documentos",
        ]
