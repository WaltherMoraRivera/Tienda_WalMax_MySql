"""
Procesador de contexto: variables que TODAS las plantillas reciben automáticamente.

Un "context processor" es una función que Django ejecuta al dibujar cada página
y cuyo resultado queda disponible en las plantillas sin pasarlo desde la vista.
Se activa agregándolo a TEMPLATES -> context_processors en settings.py.

Aquí entrega dos datos para el menú superior (base.html):
  - carrito_cantidad:   unidades en el carrito (el contador junto al ícono).
  - pedidos_pendientes: cuántos pedidos esperan validación; solo lo reciben los
                        administradores con permiso para validar pedidos.
"""

from .carrito import CLAVE_SESION
from .models import Pedido


def tienda(request):
    # La cantidad se calcula directamente desde la sesión: no consulta MySQL.
    contexto = {'carrito_cantidad': sum(request.session.get(CLAVE_SESION, {}).values())}

    usuario = request.user
    if usuario.is_authenticated and usuario.has_perm('productos.validar_pedido'):
        contexto['pedidos_pendientes'] = Pedido.objects.filter(estado=Pedido.Estado.PENDIENTE).count()
    return contexto
