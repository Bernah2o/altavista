from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app_altavista.views.administracion_views import CuotaAdministracionViewSet
from app_altavista.views.area_comun_views import AreaComunViewSet
from app_altavista.views.finanzas_views import IngresoGastoViewSet
from app_altavista.views.incidencia_views import IncidenciaViewSet
from app_altavista.views.propiedad_views import PropiedadHorizontalViewSet
from app_altavista.views.proveedor_views import ProveedorViewSet
from app_altavista.views.vivienda_views import ViviendaViewSet
from app_altavista.views.propietario_views import PropietarioViewSet
from app_altavista.views.empleado_views import EmpleadoViewSet
from app_altavista.views.documento_views import DocumentoViewSet
from app_altavista.views.reserva_views import ReservaViewSet
from app_altavista.views.mantenimiento_views import MantenimientoViewSet


router = DefaultRouter()
router.register(r"viviendas", ViviendaViewSet, basename="vivienda")
router.register(r"propietarios", PropietarioViewSet, basename="propietario")
router.register(r"areas-comunes", AreaComunViewSet, basename="areas-comunes")
router.register(r"empleados", EmpleadoViewSet, basename="empleado"),
router.register(r"documentos", DocumentoViewSet, basename="documento")
router.register(r"finanzas", IngresoGastoViewSet, basename="finanza")
router.register(r"incidencias", IncidenciaViewSet, basename="incidencia")
router.register(r"mantenimientos", MantenimientoViewSet, basename="mantenimiento")
router.register(r"propiedades", PropiedadHorizontalViewSet, basename="propiedad")
router.register(r"reservas", ReservaViewSet, basename="reserva")
router.register(
    r"administracion", CuotaAdministracionViewSet, basename="administracion"
)
router.register(r"proveedores", ProveedorViewSet, basename="proveedor")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
