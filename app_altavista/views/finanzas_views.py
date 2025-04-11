# app_altavista/views/finanzas_views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta

from ..models.finanzas import IngresoGasto, Presupuesto, FondoReserva, MovimientoFondo
from ..serializers.finanzas_serializers import (
    IngresoGastoSerializer,
    IngresoGastoDetalladoSerializer,
    PresupuestoSerializer,
    PresupuestoDetalladoSerializer,
    FondoReservaSerializer,
    MovimientoFondoSerializer
)


class IngresoGastoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar ingresos y gastos.
    
    Permite crear, consultar, actualizar y eliminar los registros de
    ingresos y gastos de la propiedad horizontal.
    """
    queryset = IngresoGasto.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'categoria', 'fecha', 'estado']
    search_fields = ['descripcion', 'numero_comprobante']
    ordering_fields = ['fecha', 'monto', 'fecha_registro']
    ordering = ['-fecha', '-fecha_registro']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == 'retrieve':
            return IngresoGastoDetalladoSerializer
        return IngresoGastoSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def resumen_mensual(self, request):
        """
        Retorna un resumen de ingresos y gastos del mes actual.
        """
        hoy = date.today()
        primer_dia = hoy.replace(day=1)
        ultimo_dia = (primer_dia + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Obtener registros del mes
        registros = IngresoGasto.objects.filter(
            fecha__range=[primer_dia, ultimo_dia],
            estado='confirmado'
        )
        
        # Calcular totales
        ingresos = registros.filter(tipo='ingreso').aggregate(
            total=Sum('monto'),
            cantidad=Count('id')
        )
        
        gastos = registros.filter(tipo='gasto').aggregate(
            total=Sum('monto'),
            cantidad=Count('id')
        )
        
        # Agrupar por categoría
        categorias = registros.values('tipo', 'categoria').annotate(
            total=Sum('monto'),
            cantidad=Count('id')
        ).order_by('tipo', '-total')
        
        return Response({
            'periodo': {
                'mes': hoy.month,
                'año': hoy.year
            },
            'ingresos': {
                'total': ingresos['total'] or 0,
                'cantidad': ingresos['cantidad']
            },
            'gastos': {
                'total': gastos['total'] or 0,
                'cantidad': gastos['cantidad']
            },
            'balance': (ingresos['total'] or 0) - (gastos['total'] or 0),
            'por_categoria': categorias
        })


class PresupuestoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar presupuestos.
    
    Permite crear, consultar y gestionar los presupuestos anuales
    y mensuales de la propiedad horizontal.
    """
    queryset = Presupuesto.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['año', 'mes', 'estado']
    search_fields = ['descripcion']
    ordering_fields = ['año', 'mes', 'monto_proyectado']
    ordering = ['-año', '-mes']
    
    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == 'retrieve':
            return PresupuestoDetalladoSerializer
        return PresupuestoSerializer
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def ejecucion(self, request, pk=None):
        """
        Retorna el estado de ejecución del presupuesto.
        """
        presupuesto = self.get_object()
        
        # Obtener ingresos y gastos del período
        movimientos = IngresoGasto.objects.filter(
            fecha__year=presupuesto.año,
            fecha__month=presupuesto.mes if presupuesto.mes else None,
            estado='confirmado'
        )
        
        # Calcular totales ejecutados
        ingresos = movimientos.filter(tipo='ingreso').aggregate(total=Sum('monto'))['total'] or 0
        gastos = movimientos.filter(tipo='gasto').aggregate(total=Sum('monto'))['total'] or 0
        
        # Calcular porcentajes de ejecución
        porc_ingresos = round((ingresos / presupuesto.monto_proyectado) * 100, 2) if presupuesto.monto_proyectado > 0 else 0
        porc_gastos = round((gastos / presupuesto.monto_proyectado) * 100, 2) if presupuesto.monto_proyectado > 0 else 0
        
        return Response({
            'presupuesto_proyectado': presupuesto.monto_proyectado,
            'ingresos_ejecutados': ingresos,
            'gastos_ejecutados': gastos,
            'balance_ejecutado': ingresos - gastos,
            'porcentaje_ingresos': porc_ingresos,
            'porcentaje_gastos': porc_gastos
        })


class FondoReservaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar fondos de reserva.
    
    Permite crear, consultar y gestionar los fondos de reserva
    de la propiedad horizontal.
    """
    queryset = FondoReserva.objects.all()
    serializer_class = FondoReservaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'estado']
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'saldo_actual', 'fecha_creacion']
    ordering = ['nombre']
    
    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def movimientos(self, request, pk=None):
        """
        Retorna los movimientos del fondo de reserva.
        """
        fondo = self.get_object()
        movimientos = MovimientoFondo.objects.filter(fondo=fondo).order_by('-fecha')
        serializer = MovimientoFondoSerializer(movimientos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def registrar_movimiento(self, request, pk=None):
        """
        Registra un nuevo movimiento en el fondo de reserva.
        """
        fondo = self.get_object()
        serializer = MovimientoFondoSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(fondo=fondo)
            # Actualizar saldo del fondo
            fondo.actualizar_saldo()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)