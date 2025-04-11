from pyexpat.errors import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone

from app_altavista.models.area_comun import AreaComun, ElementoAreaComun
from app_altavista.serializers.area_comun_serializers import (
    AreaComunSerializer,
    AreaComunDetalladoSerializer,
)


class AreaComunViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar las áreas comunes."""

    queryset = AreaComun.objects.all().order_by("nombre")
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["tipo", "requiere_reserva", "esta_activa"]
    search_fields = ["nombre", "descripcion", "ubicacion"]
    ordering_fields = ["nombre", "capacidad", "tipo"]
    ordering = ["nombre"]

    def get_serializer_class(self):
        """Retorna el serializador apropiado según la acción."""
        if self.action == "retrieve":
            return AreaComunDetalladoSerializer
        return AreaComunSerializer

    def get_permissions(self):
        """Define los permisos según la acción."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class AreaComunCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear una nueva área común."""

    model = AreaComun
    template_name = "areas_comunes/crear.html"
    fields = [
        "nombre",
        "tipo",
        "descripcion",
        "capacidad",
        "requiere_reserva",
        "horario_apertura",
        "horario_cierre",
        "ubicacion",
        "imagen",
        "reglas_uso",
        "tarifa",
    ]
    success_url = reverse_lazy("areas-comunes-lista")

    def form_valid(self, form):
        messages.success(self.request, "Área común creada exitosamente.")
        return super().form_valid(form)


class AreaComunUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar un área común existente."""

    model = AreaComun
    template_name = "areas_comunes/editar.html"
    fields = [
        "nombre",
        "tipo",
        "descripcion",
        "capacidad",
        "requiere_reserva",
        "horario_apertura",
        "horario_cierre",
        "ubicacion",
        "imagen",
        "reglas_uso",
        "tarifa",
        "esta_activa",
    ]
    success_url = reverse_lazy("areas-comunes-lista")

    def form_valid(self, form):
        messages.success(self.request, "Área común actualizada exitosamente.")
        return super().form_valid(form)


class AreaComunDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver los detalles de un área común."""

    model = AreaComun
    template_name = "areas_comunes/detalle.html"
    context_object_name = "area_comun"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        area_comun = self.get_object()
        context["elementos"] = area_comun.elementos.all()
        context["reservas_hoy"] = area_comun.get_reservas_del_dia(timezone.now().date())
        context["mantenimientos"] = area_comun.get_proximos_mantenimientos()
        return context


class AreaComunDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un área común."""

    model = AreaComun
    template_name = "areas_comunes/eliminar.html"
    success_url = reverse_lazy("areas-comunes-lista")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Área común eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)


def verificar_disponibilidad(request, pk):
    """Vista para verificar la disponibilidad de un área común."""
    if request.method == "POST":
        area_comun = get_object_or_404(AreaComun, pk=pk)
        fecha = request.POST.get("fecha")
        hora_inicio = request.POST.get("hora_inicio")
        hora_fin = request.POST.get("hora_fin")

        try:
            disponible = area_comun.esta_disponible(fecha, hora_inicio, hora_fin)
            return JsonResponse(
                {
                    "disponible": disponible,
                    "mensaje": (
                        "El área está disponible."
                        if disponible
                        else "El área no está disponible para el horario seleccionado."
                    ),
                }
            )
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)
