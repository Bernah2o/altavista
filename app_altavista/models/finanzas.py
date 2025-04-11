# app_altavista/models/finanzas.py
from django.db import models
from django.utils import timezone


class IngresoGasto(models.Model):
    """
    Modelo que representa los ingresos y gastos financieros
    de la propiedad horizontal.
    """

    TIPO_CHOICES = [
        ("ingreso", "Ingreso"),
        ("gasto", "Gasto"),
    ]

    ESTADO_CHOICES = [
        ("registrado", "Registrado"),
        ("verificado", "Verificado"),
        ("anulado", "Anulado"),
    ]

    CATEGORIA_INGRESO_CHOICES = [
        ("cuota_administracion", "Cuota de Administración"),
        ("multa", "Multa"),
        ("reserva_area_comun", "Reserva de Área Común"),
        ("parqueadero", "Parqueadero Visitantes"),
        ("alquiler", "Alquiler de Espacio"),
        ("otro_ingreso", "Otro Ingreso"),
    ]

    CATEGORIA_GASTO_CHOICES = [
        ("nomina", "Nómina"),
        ("servicios_publicos", "Servicios Públicos"),
        ("mantenimiento", "Mantenimiento"),
        ("seguridad", "Seguridad"),
        ("aseo", "Aseo"),
        ("administracion", "Administración"),
        ("impuestos", "Impuestos"),
        ("seguros", "Seguros"),
        ("legal", "Legal"),
        ("otro_gasto", "Otro Gasto"),
    ]

    fecha = models.DateField(verbose_name="Fecha")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    categoria = models.CharField(max_length=50, verbose_name="Categoría")
    descripcion = models.TextField(verbose_name="Descripción")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    proveedor = models.ForeignKey(
        "Proveedor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacciones",
        verbose_name="Proveedor",
    )
    pago = models.ForeignKey(
        "PagoAdministracion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacciones",
        verbose_name="Pago Asociado",
    )
    comprobante = models.FileField(
        upload_to="comprobantes_financieros/",
        null=True,
        blank=True,
        verbose_name="Comprobante",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="registrado",
        verbose_name="Estado",
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de registro"
    )
    registrado_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacciones_registradas",
        verbose_name="Registrado por",
    )
    metodo_pago = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Método de pago"
    )
    numero_factura = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Número de factura"
    )

    class Meta:
        verbose_name = "Ingreso/Gasto"
        verbose_name_plural = "Ingresos/Gastos"
        ordering = ["-fecha", "-fecha_registro"]
        indexes = [
            models.Index(fields=["tipo"]),
            models.Index(fields=["categoria"]),
            models.Index(fields=["fecha"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.categoria} - ${self.monto:,}"

    def save(self, *args, **kwargs):
        # Validar que el monto sea positivo
        if self.monto <= 0:
            raise ValueError("El monto debe ser positivo")

        # Si es un gasto, guardar el monto como negativo en la base de datos
        if self.tipo == "gasto" and self.monto > 0:
            self.monto = -self.monto

        super().save(*args, **kwargs)

    @property
    def get_categorias_disponibles(self):
        """
        Retorna las categorías disponibles según el tipo de transacción.

        Returns:
            list: Lista de tuplas (valor, etiqueta) de categorías
        """
        if self.tipo == "ingreso":
            return self.CATEGORIA_INGRESO_CHOICES
        return self.CATEGORIA_GASTO_CHOICES

    def anular(self, motivo=None):
        """
        Anula la transacción.

        Args:
            motivo (str, optional): Motivo de la anulación

        Returns:
            bool: True si se anuló correctamente, False si no
        """
        if self.estado == "anulado":
            return False

        self.estado = "anulado"

        if motivo:
            self.descripcion = f"{self.descripcion}\n[ANULADO] {motivo}"

        self.save()
        return True

    @classmethod
    def get_balance_periodo(cls, año, mes=None):
        """
        Calcula el balance para un período específico.

        Args:
            año (int): Año del período
            mes (int, optional): Mes del período (1-12). Si es None, considera todo el año.

        Returns:
            dict: Diccionario con totales de ingresos, gastos y balance
        """
        from django.db.models import Sum

        # Filtrar por año y mes si se proporciona
        filters = {"fecha__year": año, "estado__in": ["registrado", "verificado"]}
        if mes:
            filters["fecha__month"] = mes

        # Obtener totales
        ingresos = (
            cls.objects.filter(tipo="ingreso", **filters).aggregate(total=Sum("monto"))[
                "total"
            ]
            or 0
        )

        gastos = (
            cls.objects.filter(tipo="gasto", **filters).aggregate(total=Sum("monto"))[
                "total"
            ]
            or 0
        )

        balance = ingresos + gastos  # Los gastos ya son negativos

        return {
            "ingresos": ingresos,
            "gastos": abs(gastos),  # Valor absoluto para presentación
            "balance": balance,
        }

    @classmethod
    def get_gastos_por_categoria(cls, año, mes=None):
        """
        Obtiene el desglose de gastos por categoría para un período.

        Args:
            año (int): Año del período
            mes (int, optional): Mes del período (1-12). Si es None, considera todo el año.

        Returns:
            dict: Diccionario con categorías y montos
        """
        from django.db.models import Sum

        # Filtrar por año y mes si se proporciona
        filters = {
            "fecha__year": año,
            "tipo": "gasto",
            "estado__in": ["registrado", "verificado"],
        }
        if mes:
            filters["fecha__month"] = mes

        # Agrupar por categoría
        resultado = (
            cls.objects.filter(**filters)
            .values("categoria")
            .annotate(total=Sum("monto"))
            .order_by("categoria")
        )

        # Convertir a diccionario para facilitar su uso
        gastos_por_categoria = {}
        for item in resultado:
            # Convertir a valor absoluto y redondear
            total_abs = abs(round(item["total"], 2))
            gastos_por_categoria[item["categoria"]] = total_abs

        return gastos_por_categoria


class Presupuesto(models.Model):
    """
    Modelo para gestionar presupuestos anuales y mensuales.
    """

    año = models.PositiveIntegerField(verbose_name="Año")
    mes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Mes (1-12)",
        help_text="Si es nulo, se considera un presupuesto anual",
    )
    categoria = models.CharField(max_length=50, verbose_name="Categoría")
    tipo = models.CharField(
        max_length=10, choices=IngresoGasto.TIPO_CHOICES, verbose_name="Tipo"
    )
    monto_presupuestado = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Monto presupuestado"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    creado_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="presupuestos_creados",
        verbose_name="Creado por",
    )

    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ["-año", "-mes", "tipo", "categoria"]
        unique_together = ["año", "mes", "categoria", "tipo"]

    def __str__(self):
        periodo = f"{self.año}" if not self.mes else f"{self.mes}/{self.año}"
        return f"Presupuesto {self.get_tipo_display()} - {self.categoria} ({periodo}): ${self.monto_presupuestado:,}"

    @property
    def gasto_real(self):
        """
        Calcula el gasto/ingreso real para este presupuesto.

        Returns:
            Decimal: Monto real ejecutado
        """
        # Configurar filtros según el período
        filters = {
            "categoria": self.categoria,
            "tipo": self.tipo,
            "fecha__year": self.año,
            "estado__in": ["registrado", "verificado"],
        }

        if self.mes:
            filters["fecha__month"] = self.mes

        # Calcular total
        from django.db.models import Sum

        total = (
            IngresoGasto.objects.filter(**filters).aggregate(total=Sum("monto"))[
                "total"
            ]
            or 0
        )

        # Si es gasto, convertir a valor absoluto
        if self.tipo == "gasto":
            total = abs(total)

        return total

    @property
    def porcentaje_ejecucion(self):
        """
        Calcula el porcentaje de ejecución del presupuesto.

        Returns:
            float: Porcentaje de ejecución
        """
        if self.monto_presupuestado == 0:
            return 0

        return (self.gasto_real / self.monto_presupuestado) * 100

    @property
    def variacion(self):
        """
        Calcula la variación entre el presupuesto y el gasto real.

        Returns:
            Decimal: Variación (positiva si hay superávit, negativa si hay déficit)
        """
        return self.monto_presupuestado - self.gasto_real


class FondoReserva(models.Model):
    """
    Modelo para gestionar fondos de reserva para contingencias
    o proyectos especiales.
    """

    nombre = models.CharField(max_length=100, verbose_name="Nombre del fondo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    monto_objetivo = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Monto objetivo"
    )
    monto_actual = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Monto actual"
    )
    fecha_creacion = models.DateField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    fecha_objetivo = models.DateField(
        null=True, blank=True, verbose_name="Fecha objetivo"
    )
    estado = models.CharField(max_length=20, default="activo", verbose_name="Estado")
    porcentaje_cuota = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Porcentaje de cuota (%)",
        help_text="Porcentaje de cada cuota que se destina a este fondo",
    )

    class Meta:
        verbose_name = "Fondo de Reserva"
        verbose_name_plural = "Fondos de Reserva"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - ${self.monto_actual:,} / ${self.monto_objetivo:,}"

    @property
    def porcentaje_completado(self):
        """
        Calcula el porcentaje completado del fondo.

        Returns:
            float: Porcentaje completado
        """
        if self.monto_objetivo == 0:
            return 0

        return (self.monto_actual / self.monto_objetivo) * 100

    def registrar_aporte(self, monto, descripcion=None):
        """
        Registra un aporte al fondo.

        Args:
            monto (Decimal): Monto a aportar
            descripcion (str, optional): Descripción del aporte

        Returns:
            MovimientoFondo: Movimiento creado
        """
        if monto <= 0:
            raise ValueError("El monto debe ser positivo")

        # Actualizar monto actual
        self.monto_actual += monto
        self.save()

        # Registrar movimiento
        return MovimientoFondo.objects.create(
            fondo=self,
            tipo="ingreso",
            monto=monto,
            descripcion=descripcion or f"Aporte al fondo {self.nombre}",
        )

    def registrar_uso(self, monto, descripcion):
        """
        Registra un uso del fondo.

        Args:
            monto (Decimal): Monto a utilizar
            descripcion (str): Descripción del uso

        Returns:
            MovimientoFondo: Movimiento creado
        """
        if monto <= 0:
            raise ValueError("El monto debe ser positivo")

        if monto > self.monto_actual:
            raise ValueError("No hay suficiente dinero en el fondo")

        # Actualizar monto actual
        self.monto_actual -= monto
        self.save()

        # Registrar movimiento
        return MovimientoFondo.objects.create(
            fondo=self, tipo="gasto", monto=monto, descripcion=descripcion
        )


class MovimientoFondo(models.Model):
    """
    Modelo para registrar movimientos de los fondos de reserva.
    """

    TIPO_CHOICES = [
        ("ingreso", "Ingreso"),
        ("gasto", "Gasto"),
    ]

    fondo = models.ForeignKey(
        FondoReserva,
        on_delete=models.CASCADE,
        related_name="movimientos",
        verbose_name="Fondo",
    )
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    descripcion = models.TextField(verbose_name="Descripción")
    comprobante = models.FileField(
        upload_to="comprobantes_fondos/",
        null=True,
        blank=True,
        verbose_name="Comprobante",
    )
    registrado_por = models.ForeignKey(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_fondo",
        verbose_name="Registrado por",
    )

    class Meta:
        verbose_name = "Movimiento de Fondo"
        verbose_name_plural = "Movimientos de Fondos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.fondo.nombre} - ${self.monto:,}"
