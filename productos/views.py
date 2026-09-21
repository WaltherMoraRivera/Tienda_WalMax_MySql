"""
Vistas de la aplicación 'productos'.

Una VISTA es una función de Python que recibe la petición del navegador
(request) y devuelve una respuesta (normalmente una página HTML).

GUÍA PASO 5: "Crear operaciones CRUD (views)".
CRUD = Create (crear), Read (leer/listar), Update (actualizar), Delete (eliminar):

    Operación   Vista                 URL                          Método
    ---------   -------------------   --------------------------   ------
    Read        lista_productos       /productos/                  GET
    Create      crear_producto        /productos/nuevo/            GET / POST
    Update      editar_producto       /productos/<id>/editar/      GET / POST
    Delete      eliminar_producto     /productos/<id>/eliminar/    GET / POST

Patrón que siguen las vistas con formulario:
  - GET  -> se muestra el formulario (vacío, o con los datos del producto).
  - POST -> el usuario envió el formulario: se valida; si es válido se guarda
            y se redirige a la lista; si no, se vuelve a mostrar el formulario
            con los mensajes de error.

GUÍA PASO 6: "solo usuarios autenticados puedan acceder a las vistas CRUD".
Esto se logra con el decorador @login_required (ver más abajo). Además, cada
vista exige el PERMISO de Django correspondiente (@permission_required).

Vistas PÚBLICAS (no requieren iniciar sesión): inicio, catalogo, producto_detalle
y contacto. Las vistas del carrito y las compras están en views_compra.py.
"""

import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .carrito import Carrito
from .forms import CantidadForm, MensajeForm, ProductoForm
from .models import Categoria, Producto

# Cuántos productos "sugeridos" (de la misma categoría) se muestran en el detalle.
CANTIDAD_SUGERIDOS = 3


def inicio(request):
    """Página de inicio. Es PÚBLICA: cualquier visitante puede verla."""
    return render(request, 'productos/inicio.html')


def catalogo(request):
    """Catálogo de productos. Es PÚBLICO y de solo lectura (no permite modificar nada).

    Muestra los productos como tarjetas. Se puede filtrar por categoría con la
    dirección /catalogo/?categoria=<id>. El CRUD para administrar los productos
    sigue siendo privado (ver más abajo).
    """
    # select_related('categoria') le pide a MySQL traer cada producto JUNTO con
    # su categoría en una sola consulta (JOIN). Sin esto, la plantilla haría
    # una consulta extra por cada producto para leer producto.categoria.nombre.
    # con_reservas() agrega cuántas unidades están reservadas por pedidos
    # pendientes; así la tarjeta muestra la disponibilidad REAL (stock - reservado).
    productos = Producto.objects.con_reservas().select_related('categoria')

    # request.GET contiene lo que viene después del "?" en la dirección.
    categoria_id = request.GET.get('categoria', '')
    categoria_activa = None
    if categoria_id.isdigit():  # ignoramos valores raros como ?categoria=abc
        categoria_activa = int(categoria_id)
        productos = productos.filter(categoria_id=categoria_activa)

    return render(request, 'productos/catalogo.html', {
        'productos': productos,
        'categorias': Categoria.objects.all(),
        'categoria_activa': categoria_activa,
    })


def producto_detalle(request, pk):
    """Detalle de UN producto (PÚBLICO). Se abre en una pestaña nueva desde el catálogo.

    Muestra la información completa, el formulario para agregarlo al carrito y
    de 2 a 3 productos SUGERIDOS de la misma categoría (como hacen las tiendas
    en línea con "También te puede interesar").
    """
    productos = Producto.objects.con_reservas().select_related('categoria')
    producto = get_object_or_404(productos, pk=pk)

    # Candidatos: los demás productos de la misma categoría (sin el actual).
    candidatos = list(productos.filter(categoria=producto.categoria).exclude(pk=producto.pk))
    # random.sample elige al azar sin repetir; si hay menos candidatos que
    # CANTIDAD_SUGERIDOS, se muestran todos los que existan.
    sugeridos = random.sample(candidatos, min(len(candidatos), CANTIDAD_SUGERIDOS))

    return render(request, 'productos/producto_detalle.html', {
        'producto': producto,
        'sugeridos': sugeridos,
        'form': CantidadForm(initial={'cantidad': 1}),
        # Cuántas unidades de este producto ya tiene el cliente en su carrito.
        'en_carrito': Carrito(request).cantidad_de(producto.pk),
    })


# ---------------------------------------------------------------------------
# Seguridad de las vistas del CRUD (GUÍA PASO 6)
# ---------------------------------------------------------------------------
# Cada vista privada lleva DOS decoradores, en este orden:
#
#   @login_required
#       - Si el usuario NO inició sesión, Django lo redirige a
#         settings.LOGIN_URL (= /admin/login/) y, una vez que inicia sesión,
#         lo devuelve a la página que quería visitar.
#
#   @permission_required('productos.<permiso>', raise_exception=True)
#       - Si inició sesión pero su cuenta NO tiene ese permiso, se muestra un
#         error 403 "Acceso denegado" (ver templates/403.html) en lugar de
#         dejarlo pasar. Los superusuarios tienen todos los permisos.
#       - Django crea 4 permisos por cada modelo: add_, change_, delete_ y view_
#         (se asignan a cada usuario desde /admin/). Así el CRUD propio es tan
#         estricto como el panel de administración.
#
# Importante: @login_required va PRIMERO (arriba) para que un visitante anónimo
# reciba la redirección al login y no el error 403.
# ---------------------------------------------------------------------------

@login_required
@permission_required('productos.view_producto', raise_exception=True)
def lista_productos(request):
    """READ: muestra todos los productos guardados en la base de datos."""
    # Producto.objects.select_related('categoria') = SELECT ... JOIN categoria
    # (ORM de Django). Trae producto y categoría en UNA sola consulta.
    # con_reservas() permite mostrar también cuántas unidades están reservadas.
    productos = Producto.objects.con_reservas().select_related('categoria')
    return render(request, 'productos/lista.html', {'productos': productos})


@login_required
@permission_required('productos.add_producto', raise_exception=True)
def crear_producto(request):
    """CREATE: formulario para agregar un producto nuevo."""
    if request.method == 'POST':
        # request.POST trae los textos; request.FILES trae la imagen subida.
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():  # ejecuta las validaciones (incluye los clean_<campo>)
            form.save()      # INSERT en la base de datos
            messages.success(request, 'Producto creado correctamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm()  # formulario vacío

    return render(request, 'productos/formulario.html', {
        'form': form,
        'titulo': 'Nuevo producto',
    })


@login_required
@permission_required('productos.change_producto', raise_exception=True)
def editar_producto(request, pk):
    """UPDATE: formulario para modificar un producto existente."""
    # get_object_or_404 busca el producto por su id; si no existe, muestra
    # una página de error 404 en lugar de romper el programa.
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        # instance=producto le dice al formulario que ACTUALICE ese registro
        # (UPDATE) en vez de crear uno nuevo.
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)  # formulario con los datos actuales

    return render(request, 'productos/formulario.html', {
        'form': form,
        'titulo': f'Editar producto: {producto.nombre}',
    })


@login_required
@permission_required('productos.delete_producto', raise_exception=True)
def eliminar_producto(request, pk):
    """DELETE: pide confirmación y luego elimina el producto."""
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        # Solo se borra cuando el usuario CONFIRMA (envía el formulario por POST).
        # Nunca se borra con un simple enlace (GET), para evitar borrados accidentales.
        try:
            producto.delete()  # DELETE en la base de datos
        except ProtectedError:
            # El producto forma parte de algún pedido (DetallePedido usa
            # on_delete=PROTECT): borrarlo dejaría los pedidos sin su producto.
            messages.error(
                request,
                f'No se puede eliminar «{producto.nombre}»: forma parte de uno o más pedidos.')
            return redirect('lista_productos')
        messages.success(request, f'Producto «{producto.nombre}» eliminado.')
        return redirect('lista_productos')

    # GET: mostramos la página que pregunta "¿Seguro que quieres eliminarlo?"
    return render(request, 'productos/confirmar_eliminar.html', {'producto': producto})


def contacto(request):
    """Formulario de contacto. Es PÚBLICO: guarda el mensaje en la base de datos."""
    if request.method == 'POST':
        form = MensajeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Gracias! Tu mensaje fue enviado correctamente.')
            # Redirigir después de un POST evita que, al recargar la página,
            # el navegador reenvíe el formulario.
            return redirect('contacto')
    else:
        form = MensajeForm()

    return render(request, 'productos/contacto.html', {'form': form})
