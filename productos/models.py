"""
Modelos de la aplicación 'productos'.

Un MODELO es una clase de Python que representa una TABLA de la base de datos:
  - cada clase       -> una tabla
  - cada atributo    -> una columna de esa tabla
  - cada instancia   -> una fila (un registro)

Django traduce estas clases a tablas MySQL con dos comandos:
    python manage.py makemigrations   (genera el "plano" de los cambios)
    python manage.py migrate          (crea/modifica las tablas en MySQL)

GUÍA PASO 3: "Crear dos clases relacionadas en models.py".
Aquí las dos clases relacionadas son Categoria y Producto:
una categoría tiene MUCHOS productos, y cada producto pertenece a UNA categoría.

EXTENSIÓN (carrito de compras simulado): se agregan los modelos Pedido y
DetallePedido, que registran las compras ficticias, y la lógica de "stock
reservado" (ver más abajo). Ninguna de estas tablas modifica la tabla de productos.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone


class StockInsuficiente(Exception):
    """Se lanza cuando no hay unidades suficientes para completar una operación.

    'problemas' es una lista de textos que explican qué producto falló, para
    mostrárselos al usuario.
    """

    def __init__(self, problemas):
        self.problemas = problemas
        super().__init__(' '.join(problemas))


class PedidoNoPendiente(Exception):
    """Se lanza al intentar validar o rechazar un pedido que ya fue revisado."""


class ProductoQuerySet(models.QuerySet):
    """Consultas extra para Producto (se usan como Producto.objects.con_reservas())."""

    def con_reservas(self):
        """Agrega a cada producto el campo 'reservado'.

        'reservado' = unidades que están en pedidos PENDIENTES de validación:
        ya fueron "tomadas" por un cliente, pero el stock todavía no se descontó.
        Se calcula con SUM en MySQL, en la misma consulta que trae los productos.
        """
        return self.annotate(reservado=Coalesce(
            Sum('detalles__cantidad', filter=Q(detalles__pedido__estado='pendiente')),
            Value(0),
            output_field=IntegerField(),
        ))


class Categoria(models.Model):
    """Grupo al que pertenece un producto (ej.: Herramientas, Fijaciones, Eléctrico)."""

    # CharField: texto corto. max_length es obligatorio (largo máximo).
    # unique=True: no pueden existir dos categorías con el mismo nombre.
    nombre = models.CharField(max_length=60, unique=True)

    # TextField: texto largo. blank=True permite dejarlo vacío en los formularios.
    descripcion = models.TextField(blank=True)

    class Meta:
        # ordering: orden por defecto al consultar (alfabético por nombre).
        ordering = ['nombre']
        # Nombres "bonitos" que se muestran en el panel de administración.
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        # __str__ define cómo se muestra el objeto (en el admin, en listas, etc.).
        return self.nombre


class Producto(models.Model):
    """Artículo que se promociona en la tienda."""

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    # DecimalField: número con decimales exactos (ideal para dinero).
    # max_digits=10 -> hasta 10 dígitos en total; decimal_places=2 -> 2 decimales.
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    # PositiveIntegerField: entero que no admite negativos (unidades en bodega).
    stock = models.PositiveIntegerField(default=0)

    # ImageField: guarda una imagen. El archivo se copia a la carpeta
    # MEDIA_ROOT/productos/ y en la base de datos queda solo su ruta.
    # Requiere la librería Pillow. blank/null=True la hacen opcional.
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    # ForeignKey (clave foránea): RELACIÓN entre las dos clases.
    #  - on_delete=PROTECT: si una categoría tiene productos, Django NO permite
    #    borrarla (evita perder productos por accidente).
    #  - related_name='productos': permite hacer categoria.productos.all()
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
    )

    # auto_now_add=True: Django guarda la fecha y hora de creación automáticamente.
    creado = models.DateTimeField(auto_now_add=True)

    # Manager personalizado: permite escribir Producto.objects.con_reservas()
    # además de todos los métodos habituales (filter, get, all...).
    objects = ProductoQuerySet.as_manager()

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def disponible(self):
        """Unidades que un cliente puede comprar ahora: stock físico - reservado.

        Ejemplo: stock 10 y un pedido pendiente por 3 unidades -> disponible 7.
        Si el producto viene de con_reservas(), el dato ya está calculado; si no,
        se consulta a la base de datos (una consulta extra).
        """
        reservado = getattr(self, 'reservado', None)
        if reservado is None:
            reservado = DetallePedido.objects.filter(
                producto=self, pedido__estado=Pedido.Estado.PENDIENTE,
            ).aggregate(total=Coalesce(Sum('cantidad'), Value(0)))['total']
        return max(self.stock - int(reservado), 0)


class Mensaje(models.Model):
    """Mensaje enviado desde el formulario de contacto (criterio 2.1.1)."""

    nombre = models.CharField(max_length=80)
    # EmailField: texto que Django valida como correo electrónico.
    email = models.EmailField()
    asunto = models.CharField(max_length=120)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        # El signo '-' significa orden descendente: primero los más recientes.
        ordering = ['-fecha_envio']

    def __str__(self):
        return f'{self.asunto} — {self.nombre}'


class Pedido(models.Model):
    """Compra FICTICIA registrada cuando el cliente finaliza su carrito.

    Nadie paga nada: es una simulación. El stock se maneja en tres momentos:

      1. PENDIENTE  - El cliente finalizó la compra. Las unidades quedan
                      RESERVADAS (no se pueden vender a otra persona), pero el
                      stock físico del producto todavía NO cambia.
      2. VALIDADO   - Un administrador con permiso revisó el pedido. Recién aquí
                      se DESCUENTA el stock físico de cada producto.
      3. RECHAZADO  - El administrador lo rechazó. Se liberan las unidades
                      reservadas y el stock físico queda igual.
    """

    class Estado(models.TextChoices):
        # (valor guardado en MySQL, texto que ve el usuario)
        PENDIENTE = 'pendiente', 'Pendiente de validación'
        VALIDADO = 'validado', 'Validado'
        RECHAZADO = 'rechazado', 'Rechazado'

    # Quien compró. Es opcional (null=True) porque también se puede comprar SIN
    # iniciar sesión. SET_NULL: si se borra el usuario, el pedido se conserva.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='pedidos',
    )

    # Datos de contacto y despacho que escribe el cliente en el checkout.
    nombre = models.CharField(max_length=80)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    notas = models.TextField(blank=True)

    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    creado = models.DateTimeField(auto_now_add=True)

    # Quién y cuándo revisó el pedido (se llenan al validar o rechazar).
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='pedidos_revisados',
    )
    revisado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado']
        # Permiso propio: Django ya crea add/change/delete/view; este es el que
        # se asigna a los administradores que pueden validar o rechazar pedidos.
        permissions = [('validar_pedido', 'Puede validar o rechazar pedidos')]

    def __str__(self):
        return f'Pedido #{self.pk} · {self.nombre}'

    @property
    def total(self):
        """Suma de los subtotales de todos los productos del pedido."""
        return sum((detalle.subtotal for detalle in self.detalles.all()), Decimal('0'))

    @classmethod
    def crear(cls, lineas, datos, usuario=None):
        """Registra la compra ficticia y RESERVA las unidades.

        lineas:  lista de tuplas (producto_id, cantidad) tomadas del carrito.
        datos:   diccionario con nombre, email, telefono, direccion y notas.
        usuario: el usuario con sesión iniciada, o None si compra como invitado.

        Todo ocurre dentro de una TRANSACCIÓN (transaction.atomic): o se guarda
        el pedido completo o no se guarda nada. select_for_update() bloquea las
        filas de los productos mientras se revisa el stock, así dos clientes que
        compran al mismo tiempo no pueden reservar las mismas unidades.
        """
        if not lineas:
            raise StockInsuficiente(['El carrito está vacío.'])

        with transaction.atomic():
            ids = [producto_id for producto_id, _ in lineas]
            productos = {
                p.pk: p for p in
                Producto.objects.select_for_update().filter(pk__in=ids).order_by('pk')
            }
            # Unidades ya reservadas por OTROS pedidos pendientes, por producto.
            reservados = dict(
                DetallePedido.objects
                .filter(pedido__estado=cls.Estado.PENDIENTE, producto_id__in=ids)
                .order_by().values('producto_id').annotate(total=Sum('cantidad'))
                .values_list('producto_id', 'total')
            )

            problemas = []
            for producto_id, cantidad in lineas:
                producto = productos.get(producto_id)
                if producto is None:
                    problemas.append('Uno de los productos del carrito ya no existe.')
                    continue
                disponible = max(producto.stock - int(reservados.get(producto_id, 0)), 0)
                if cantidad > disponible:
                    problemas.append(
                        f'«{producto.nombre}»: pediste {cantidad} y solo hay {disponible} disponibles.')
            if problemas:
                raise StockInsuficiente(problemas)

            pedido = cls.objects.create(usuario=usuario, **datos)
            # Se guarda una COPIA del nombre y del precio del momento de la compra:
            # si el producto cambia de precio después, el pedido no se altera.
            DetallePedido.objects.bulk_create([
                DetallePedido(
                    pedido=pedido, producto=productos[producto_id],
                    nombre_producto=productos[producto_id].nombre,
                    precio_unitario=productos[producto_id].precio,
                    cantidad=cantidad,
                )
                for producto_id, cantidad in lineas
            ])
            return pedido

    def validar(self, usuario):
        """El administrador aprueba el pedido: AQUÍ se descuenta el stock físico."""
        with transaction.atomic():
            pedido = Pedido.objects.select_for_update().get(pk=self.pk)
            if pedido.estado != self.Estado.PENDIENTE:
                raise PedidoNoPendiente(
                    f'El pedido #{pedido.pk} ya fue revisado ({pedido.get_estado_display()}).')

            detalles = list(pedido.detalles.all())
            productos = {
                p.pk: p for p in
                Producto.objects.select_for_update()
                .filter(pk__in=[d.producto_id for d in detalles]).order_by('pk')
            }
            # Por si alguien bajó el stock a mano después de la reserva.
            problemas = [
                f'«{d.nombre_producto}»: el pedido pide {d.cantidad} y el stock real es '
                f'{productos[d.producto_id].stock}.'
                for d in detalles if productos[d.producto_id].stock < d.cantidad
            ]
            if problemas:
                raise StockInsuficiente(problemas)

            for detalle in detalles:
                # F('stock') - n: la resta la hace MySQL directamente (segura ante
                # cambios simultáneos), en vez de leer el valor y volver a escribirlo.
                Producto.objects.filter(pk=detalle.producto_id).update(stock=F('stock') - detalle.cantidad)

            pedido._cerrar(self.Estado.VALIDADO, usuario)
        self.refresh_from_db()

    def rechazar(self, usuario):
        """El administrador rechaza el pedido: se liberan las unidades reservadas."""
        with transaction.atomic():
            pedido = Pedido.objects.select_for_update().get(pk=self.pk)
            if pedido.estado != self.Estado.PENDIENTE:
                raise PedidoNoPendiente(
                    f'El pedido #{pedido.pk} ya fue revisado ({pedido.get_estado_display()}).')
            pedido._cerrar(self.Estado.RECHAZADO, usuario)
        self.refresh_from_db()

    def _cerrar(self, estado, usuario):
        """Guarda el resultado de la revisión (estado, quién y cuándo)."""
        self.estado = estado
        self.revisado_por = usuario
        self.revisado_en = timezone.now()
        self.save(update_fields=['estado', 'revisado_por', 'revisado_en'])


class DetallePedido(models.Model):
    """Una línea de un pedido: un producto, su cantidad y el precio al comprar."""

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    # PROTECT: no se puede borrar un producto que forma parte de algún pedido.
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles')
    nombre_producto = models.CharField(max_length=100)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'detalle del pedido'
        verbose_name_plural = 'detalles del pedido'
        constraints = [
            # Regla a nivel de base de datos: no puede haber líneas de 0 unidades.
            models.CheckConstraint(check=Q(cantidad__gte=1), name='detallepedido_cantidad_minima_1'),
        ]

    def __str__(self):
        return f'{self.cantidad} × {self.nombre_producto}'

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad
