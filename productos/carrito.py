"""
Carrito de compras basado en la SESIÓN de Django.

¿Qué es la sesión? Django guarda un pequeño diccionario por cada navegador
(identificado por una cookie). Ahí guardamos el carrito, así que:

  - Funciona SIN iniciar sesión: el carrito pertenece a ese navegador.
  - Funciona CON sesión iniciada: al iniciar sesión el carrito se conserva.
  - Al CERRAR sesión, Django borra la sesión completa y el carrito se vacía.

El carrito es un diccionario de Python guardado en la sesión:

    request.session['carrito'] = {'12': 2, '7': 1}
                                  ^id del producto  ^cantidad

(Las claves son texto porque la sesión se guarda como JSON.)

Importante: agregar productos al carrito NO reserva stock. El stock recién se
reserva cuando el cliente finaliza la compra (ver Pedido.crear en models.py).
"""

from collections import namedtuple

from .models import Producto

# Nombre de la clave dentro de la sesión.
CLAVE_SESION = 'carrito'

# Tope de unidades de un mismo producto en el carrito.
CANTIDAD_MAXIMA_POR_PRODUCTO = 99

# Una línea del carrito lista para mostrar en la plantilla:
#   producto   -> el objeto Producto (con su categoría y sus reservas)
#   cantidad   -> unidades que el cliente quiere
#   subtotal   -> precio * cantidad
#   disponible -> unidades que realmente se pueden comprar hoy
#   excede     -> True si la cantidad pedida supera lo disponible
Linea = namedtuple('Linea', 'producto cantidad subtotal disponible excede')


class Carrito:
    """Encapsula todas las operaciones del carrito para no repetir código en las vistas."""

    def __init__(self, request):
        self.session = request.session
        # Se copia el diccionario para poder modificarlo con seguridad.
        self.items = dict(self.session.get(CLAVE_SESION, {}))

    def _guardar(self):
        """Escribe el carrito en la sesión y avisa a Django que cambió."""
        self.session[CLAVE_SESION] = self.items
        self.session.modified = True

    def __len__(self):
        """Cantidad TOTAL de unidades (no de líneas). Sirve para el contador del menú."""
        return sum(self.items.values())

    def cantidad_de(self, producto_id):
        """Cuántas unidades de ese producto hay hoy en el carrito."""
        return self.items.get(str(producto_id), 0)

    # ---- Operaciones ------------------------------------------------------
    def agregar(self, producto, cantidad=1):
        """Suma unidades a lo que ya hay en el carrito."""
        return self._fijar(producto, self.cantidad_de(producto.pk) + cantidad)

    def actualizar(self, producto, cantidad):
        """Cambia la cantidad de un producto a un valor exacto."""
        return self._fijar(producto, cantidad)

    def _fijar(self, producto, deseada):
        """Deja la cantidad pedida, sin pasarse de lo disponible ni del tope.

        Devuelve (cantidad_final, se_ajusto). 'se_ajusto' es True cuando se pidió
        más de lo que se puede comprar y hubo que recortar la cantidad.
        """
        limite = min(producto.disponible, CANTIDAD_MAXIMA_POR_PRODUCTO)
        final = min(deseada, limite)
        if final <= 0:
            self.items.pop(str(producto.pk), None)
        else:
            self.items[str(producto.pk)] = final
        self._guardar()
        return max(final, 0), final < deseada

    def quitar(self, producto_id):
        """Elimina un producto del carrito."""
        self.items.pop(str(producto_id), None)
        self._guardar()

    def vaciar(self):
        """Deja el carrito sin productos."""
        self.items = {}
        self._guardar()

    # ---- Lectura ----------------------------------------------------------
    def lineas(self):
        """Devuelve las líneas del carrito con sus datos calculados.

        Consulta todos los productos en UNA sola consulta a MySQL. Si algún
        producto fue eliminado desde que se agregó, se quita del carrito.
        """
        if not self.items:
            return []

        ids = [int(clave) for clave in self.items]
        productos = (Producto.objects.con_reservas()
                     .select_related('categoria').filter(pk__in=ids).order_by('nombre'))

        lineas = []
        for producto in productos:
            cantidad = self.items[str(producto.pk)]
            disponible = producto.disponible
            lineas.append(Linea(
                producto=producto, cantidad=cantidad,
                subtotal=producto.precio * cantidad,
                disponible=disponible, excede=cantidad > disponible,
            ))

        # Limpieza: productos que ya no existen.
        existentes = {str(linea.producto.pk) for linea in lineas}
        if set(self.items) - existentes:
            self.items = {k: v for k, v in self.items.items() if k in existentes}
            self._guardar()
        return lineas

    @staticmethod
    def total(lineas):
        """Suma de los subtotales de las líneas."""
        return sum((linea.subtotal for linea in lineas), 0)
