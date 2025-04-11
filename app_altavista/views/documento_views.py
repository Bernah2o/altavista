# app_altavista/views/documento_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone

from ..models.documento import Documento, VisualizacionDocumento, Carpeta, DocumentoCarpeta
from ..serializers.documento_serializers import (
    DocumentoSerializer,
    DocumentoDetalladoSerializer,
    VisualizacionDocumentoSerializer,
    CarpetaSerializer,
    CarpetaDetalladaSerializer,
    DocumentoCarpetaSerializer
)


class DocumentoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar documentos.
    
    Permite crear, consultar, actualizar y eliminar los documentos
    almacenados en la propiedad horizontal.
    """
    queryset = Documento.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'estado', 'fecha_documento']
    search_fields = ['titulo', 'descripcion', 'numero_referencia']
    ordering_fields = ['titulo', 'fecha_documento', 'fecha_registro']
    ordering = ['-fecha_registro']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == 'retrieve':
            return DocumentoDetalladoSerializer
        return DocumentoSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def registrar_visualizacion(self, request, pk=None):
        """
        Registra una visualización del documento.
        """
        documento = self.get_object()
        usuario = request.user
        
        # Crear registro de visualización
        visualizacion = VisualizacionDocumento.objects.create(
            documento=documento,
            usuario=usuario,
            fecha_visualizacion=timezone.now()
        )
        
        serializer = VisualizacionDocumentoSerializer(visualizacion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def visualizaciones(self, request, pk=None):
        """
        Retorna el historial de visualizaciones del documento.
        """
        documento = self.get_object()
        visualizaciones = VisualizacionDocumento.objects.filter(
            documento=documento
        ).order_by('-fecha_visualizacion')
        
        serializer = VisualizacionDocumentoSerializer(visualizaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def carpetas(self, request, pk=None):
        """
        Retorna las carpetas que contienen este documento.
        """
        documento = self.get_object()
        carpetas = documento.carpetas.all()
        serializer = CarpetaSerializer(carpetas, many=True)
        return Response(serializer.data)


class CarpetaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar carpetas de documentos.
    
    Permite crear, consultar y gestionar la estructura de carpetas
    para organizar los documentos.
    """
    queryset = Carpeta.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'estado']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion']
    ordering = ['nombre']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == 'retrieve':
            return CarpetaDetalladaSerializer
        return CarpetaSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def documentos(self, request, pk=None):
        """
        Retorna los documentos contenidos en la carpeta.
        """
        carpeta = self.get_object()
        documentos = carpeta.documentos.all()
        serializer = DocumentoSerializer(documentos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def agregar_documento(self, request, pk=None):
        """
        Agrega un documento a la carpeta.
        """
        carpeta = self.get_object()
        documento_id = request.data.get('documento')
        
        try:
            documento = Documento.objects.get(id=documento_id)
            DocumentoCarpeta.objects.get_or_create(
                carpeta=carpeta,
                documento=documento
            )
            return Response({"mensaje": "Documento agregado exitosamente."})
        except Documento.DoesNotExist:
            return Response(
                {"error": "El documento especificado no existe."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remover_documento(self, request, pk=None):
        """
        Remueve un documento de la carpeta.
        """
        carpeta = self.get_object()
        documento_id = request.data.get('documento')
        
        try:
            relacion = DocumentoCarpeta.objects.get(
                carpeta=carpeta,
                documento_id=documento_id
            )
            relacion.delete()
            return Response({"mensaje": "Documento removido exitosamente."})
        except DocumentoCarpeta.DoesNotExist:
            return Response(
                {"error": "El documento no está en esta carpeta."},
                status=status.HTTP_404_NOT_FOUND
            )