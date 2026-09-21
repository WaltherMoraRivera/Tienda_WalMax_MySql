"""
Vistas del carrito de compras, el checkout (compra FICTICIA) y los pedidos.

Recorrido completo de una compra:

    catálogo -> detalle del producto -> "Agregar al carrito" -> carrito
             -> "Finalizar compra" (checkout: datos de contacto)
             -> pedido PENDIENTE (las unidades quedan RESERVADAS)
             -> un administrador VALIDA el pedido desde /admin/ (se descuenta
                el stock) o lo RECHAZA (se liberan las unidades).

Todas estas vistas son PÚBLICAS: se puede comprar con o sin sesión iniciada.
Nadie paga nada: es una simulación.
"""

from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .carrito import Carrito
from .forms import CantidadForm, PedidoForm
from .models import Pedido, Producto, StockInsuficiente

# Clave de la sesión donde se recuerdan los pedidos hechos desde este navegador
# (así un cliente sin cuenta puede volver a ver su pedido).
CLAVE_PEDIDOS_SESION = 'pedidos'


def _destino(request, por_defecto):
    """A dónde volver después de una acción del carrito.

    Los formularios envían un campo oculto 'next' con la página de origen, para
    que agregar un producto no saque al cliente de donde estaba. Solo se acepta
    una dirección de ESTE mismo sitio (evita redirecciones a páginas externas).
    """
    siguiente = request.POST.get('next', '')
    if siguiente and url_has_allowed_host_and_scheme(
            siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return siguiente
    return por_defecto


def _pedidos_de_la_sesion(request):
    return request.session.get(CLAVE_PEDIDOS_SESION, [])


# ---------------------------------------------------------------------------
# Carrito
# ---------------------------------------------------------------------------
def carrito_ver(request):
    """Muestra el carrito con sus productos, cantidades y el total."""
    lineas = Carrito(request).lineas()
    return render(request, 'productos/carrito.html', {
        'lineas': lineas,
        'total': Carrito.total(lineas),
        # Si alguna línea pide más de lo disponible, se avisa y se bloquea el checkout.
        'hay_problemas': any(linea.excede for linea in lineas),
    })


# @require_POST: estas vistas solo aceptan POST (formularios). Si alguien abre
# la dirección escribiéndola en el navegador (GET), Django responde 405. Así
# un simple enlace nunca modifica el carrito.
@require_POST
def carrito_agregar(request, pk):
    """Agrega un producto al carrito (o suma unidades si ya estaba)."""
    producto = get_object_or_404(Producto.objects.con_reservas(), pk=pk)
    destino = _destino(request, 'carrito')

    form = CantidadForm(request.POST)
    if not form.is_valid():
        for error in form.errors['cantidad']:
            messages.error(request, error)
        return redirect(destino)

    if producto.disponible <= 0:
        messages.error(request, f'«{producto.nombre}» está agotado por ahora.')
        return redirect(destino)

    final, ajustada = Carrito(request).agregar(producto, form.cleaned_data['cantidad'])
    if ajustada:
        messages.warning(
            request,
            f'Solo hay {producto.disponible} unidades disponibles de «{producto.nombre}». '
            f'En tu carrito quedaron {final}.')
    else:
        messages.success(request, f'«{producto.nombre}» agregado al carrito.')
    return redirect(destino)


@require_POST
def carrito_actualizar(request, pk):
    """Cambia la cantidad de un producto que ya está en el carrito."""
    producto = get_object_or_404(Producto.objects.con_reservas(), pk=pk)
    carrito = Carrito(request)

    form = CantidadForm(request.POST)
    if not form.is_valid():
        for error in form.errors['cantidad']:
            messages.error(request, error)
    elif carrito.cantidad_de(pk) == 0:
        messages.error(request, f'«{producto.nombre}» no está en tu carrito.')
    else:
        final, ajustada = carrito.actualizar(producto, form.cleaned_data['cantidad'])
        if final == 0:
            messages.warning(request, f'«{producto.nombre}» se quitó del carrito porque ya no hay stock.')
        elif ajustada:
            messages.warning(
                request,
                f'Solo hay {producto.disponible} unidades disponibles de «{producto.nombre}». '
                f'En tu carrito quedaron {final}.')
        else:
            messages.success(request, 'Cantidad actualizada.')
    return redirect('carrito')


@require_POST
def carrito_quitar(request, pk):
    """Quita un producto del carrito."""
    Carrito(request).quitar(pk)
    messages.info(request, 'Producto quitado del carrito.')
    return redirect('carrito')


@require_POST
def carrito_vaciar(request):
    """Deja el carrito sin productos."""
    Carrito(request).vaciar()
    messages.info(request, 'Tu carrito quedó vacío.')
    return redirect('carrito')


# ---------------------------------------------------------------------------
# Checkout y pedidos
# ---------------------------------------------------------------------------
def checkout(request):
    """Finalizar compra (SIMULADA): pide los datos de contacto y crea el pedido.

    Al crear el pedido las unidades quedan RESERVADAS, pero el stock físico no
    cambia hasta que un administrador valide el pedido.
    """
    carrito = Carrito(request)
    lineas = carrito.lineas()

    if not lineas:
        messages.info(request, 'Tu carrito está vacío. Agrega productos para finalizar la compra.')
        return redirect('catalogo')
    if any(linea.excede for linea in lineas):
        messages.error(request, 'Algunos productos superan el stock disponible. Ajusta las cantidades para continuar.')
        return redirect('carrito')

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            usuario = request.user if request.user.is_authenticated else None
            try:
                pedido = Pedido.crear(
                    [(linea.producto.pk, linea.cantidad) for linea in lineas],
                    form.cleaned_data, usuario=usuario)
            except StockInsuficiente as error:
                # Otro cliente reservó las unidades justo antes: no se crea nada.
                for problema in error.problemas:
                    messages.error(request, problema)
                return redirect('carrito')

            carrito.vaciar()
            # Se recuerda el pedido en la sesión para poder mostrarlo después.
            request.session[CLAVE_PEDIDOS_SESION] = _pedidos_de_la_sesion(request) + [pedido.pk]
            messages.success(
                request,
                'Compra simulada registrada. Tus productos quedaron reservados hasta que '
                'un administrador valide el pedido.')
            return redirect('pedido_detalle', pk=pedido.pk)
    else:
        # Con sesión iniciada, se adelantan los datos que ya conocemos.
        inicial = {}
        if request.user.is_authenticated:
            inicial = {'nombre': request.user.get_full_name(), 'email': request.user.email}
        form = PedidoForm(initial=inicial)

    return render(request, 'productos/checkout.html', {
        'form': form,
        'lineas': lineas,
        'total': Carrito.total(lineas),
    })


def pedido_detalle(request, pk):
    """Resumen de un pedido. Lo pueden ver: su dueño, quien lo hizo desde este
    mismo navegador, y los administradores con permiso para ver pedidos."""
    pedido = get_object_or_404(Pedido.objects.prefetch_related('detalles'), pk=pk)

    usuario = request.user
    es_dueno = (usuario.is_authenticated and pedido.usuario_id == usuario.pk) \
        or pedido.pk in _pedidos_de_la_sesion(request)
    es_revisor = usuario.is_authenticated and usuario.has_perm('productos.view_pedido')
    if not (es_dueno or es_revisor):
        # 404 (y no 403) para no revelar que ese número de pedido existe.
        raise Http404('Pedido no encontrado')

    return render(request, 'productos/pedido_detalle.html', {'pedido': pedido})


def mis_pedidos(request):
    """Lista los pedidos del usuario con sesión iniciada y los hechos desde este navegador."""
    filtro = Q(pk__in=_pedidos_de_la_sesion(request))
    if request.user.is_authenticated:
        filtro |= Q(usuario=request.user)
    pedidos = Pedido.objects.filter(filtro).prefetch_related('detalles')
    return render(request, 'productos/mis_pedidos.html', {'pedidos': pedidos})
