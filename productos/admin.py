"""
Registro de los modelos en el panel de administración de Django.

GUÍA PASO 4: "En admin.py, registrar el modelo para gestionarlo desde el
panel administrativo".
CRITERIO 2.1.2: "Utiliza el administrador de Django y registra el modelo
para gestionarlo desde el panel administrativo".

El panel de administración (http://127.0.0.1:8000/admin/) permite crear,
ver, editar y borrar registros de la base de datos sin escribir vistas.
Solo aparece un modelo en el panel si lo registramos aquí.

Se usa el decorador @admin.register(Modelo) sobre una clase ModelAdmin, que
permite personalizar cómo se ve cada modelo dentro del panel.

Cada ModelAdmin usa además  form = <NuestroForm>  para que el panel aplique las
MISMAS validaciones personalizadas (clean_<campo>) que definimos en forms.py.
Sin esa línea, el admin usaría un formulario automático sin nuestras reglas y
permitiría guardar, por ejemplo, un producto con precio 0.
"""

from django.contrib import admin, messages
from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from .forms import CategoriaForm, MensajeForm, ProductoForm
from .models import (
    Categoria, DetallePedido, Mensaje, Pedido, PedidoNoPendiente, Producto, StockInsuficiente,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    form = CategoriaForm
    # list_display: columnas que se muestran en la lista de categorías.
    list_display = ('nombre', 'descripcion')
    # search_fields: habilita el cuadro de búsqueda sobre estos campos.
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoForm
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'stock_reservado', 'creado')
    # list_filter: agrega filtros laterales (aquí, por categoría).
    list_filter = ('categoria',)
    search_fields = ('nombre', 'descripcion')

    def get_queryset(self, request):
        # con_reservas() suma las unidades de pedidos pendientes en la misma consulta.
        return super().get_queryset(request).con_reservas()

    @admin.display(description='Reservado', ordering='reservado')
    def stock_reservado(self, producto):
        """Unidades tomadas por pedidos que esperan validación (aún no descontadas)."""
        return producto.reservado


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    form = MensajeForm
    list_display = ('asunto', 'nombre', 'email', 'fecha_envio')
    search_fields = ('asunto', 'nombre', 'email')
    # readonly_fields: la fecha de envío se muestra pero no se puede modificar.
    readonly_fields = ('fecha_envio',)


# ---------------------------------------------------------------------------
# Pedidos (compras ficticias): el administrador los VALIDA o los RECHAZA
# ---------------------------------------------------------------------------
class DetallePedidoInline(admin.TabularInline):
    """Muestra los productos del pedido dentro de la página del pedido (solo lectura)."""

    model = DetallePedido
    extra = 0
    can_delete = False
    fields = ('nombre_producto', 'precio_unitario', 'cantidad', 'subtotal')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'email', 'estado', 'total_pedido', 'creado', 'revisado_por')
    list_filter = ('estado',)
    search_fields = ('nombre', 'email')
    inlines = [DetallePedidoInline]
    actions = ['validar_pedidos', 'rechazar_pedidos']

    # Todos los datos son de solo lectura: el estado NO se cambia a mano, solo con
    # las acciones de abajo (que aplican las reglas de stock).
    readonly_fields = ('usuario', 'nombre', 'email', 'telefono', 'direccion', 'notas',
                       'estado', 'creado', 'revisado_por', 'revisado_en', 'total_pedido')

    def get_queryset(self, request):
        # Calcula el total de cada pedido en MySQL (una sola consulta para toda la lista).
        return super().get_queryset(request).annotate(total_calculado=Sum(
            ExpressionWrapper(F('detalles__cantidad') * F('detalles__precio_unitario'),
                              output_field=DecimalField(max_digits=12, decimal_places=2))))

    @admin.display(description='Pedido', ordering='pk')
    def numero(self, pedido):
        return f'#{pedido.pk}'

    @admin.display(description='Total', ordering='total_calculado')
    def total_pedido(self, pedido):
        total = getattr(pedido, 'total_calculado', None)
        return f'${(total if total is not None else pedido.total):,.0f}'.replace(',', '.')

    # Los pedidos nacen solo desde el checkout de la tienda, nunca a mano.
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Un pedido ya validado descontó stock: borrarlo dejaría el inventario incoherente.
        if obj is not None and obj.estado == Pedido.Estado.VALIDADO:
            return False
        return super().has_delete_permission(request, obj)

    # permissions=['validar'] hace que Django busque el método has_validar_permission
    # y solo muestre la acción a quien lo cumpla.
    def has_validar_permission(self, request):
        return request.user.has_perm('productos.validar_pedido')

    @admin.action(description='Validar pedidos seleccionados (descuenta el stock)', permissions=['validar'])
    def validar_pedidos(self, request, queryset):
        validados = 0
        for pedido in queryset:
            try:
                pedido.validar(request.user)
                validados += 1
            except PedidoNoPendiente as error:
                self.message_user(request, str(error), messages.WARNING)
            except StockInsuficiente as error:
                self.message_user(request, f'Pedido #{pedido.pk} sin validar. {error}', messages.ERROR)
        if validados:
            self.message_user(request, f'{validados} pedido(s) validado(s). El stock fue descontado.', messages.SUCCESS)

    @admin.action(description='Rechazar pedidos seleccionados (libera el stock reservado)', permissions=['validar'])
    def rechazar_pedidos(self, request, queryset):
        rechazados = 0
        for pedido in queryset:
            try:
                pedido.rechazar(request.user)
                rechazados += 1
            except PedidoNoPendiente as error:
                self.message_user(request, str(error), messages.WARNING)
        if rechazados:
            self.message_user(request, f'{rechazados} pedido(s) rechazado(s). Se liberó el stock reservado.', messages.SUCCESS)
