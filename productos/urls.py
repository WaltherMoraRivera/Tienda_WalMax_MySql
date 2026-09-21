"""
Rutas (URLs) de la aplicación 'productos'.

GUÍA PASO 5: "Agregar las rutas correspondientes en urls.py".

Una RUTA conecta una dirección web con una vista:
    path('direccion/', vista, name='nombre_de_la_ruta')

  - '<int:pk>' captura un número de la URL y se lo pasa a la vista como
    parámetro (pk = "primary key", el id del producto).
  - name='...' es un apodo de la ruta: en las plantillas se usa
    {% url 'nombre' %} para no escribir la dirección a mano.
"""

from django.urls import path

from . import views, views_compra

urlpatterns = [
    # Páginas públicas (cualquier visitante puede verlas)
    path('', views.inicio, name='inicio'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('catalogo/<int:pk>/', views.producto_detalle, name='producto_detalle'),
    path('contacto/', views.contacto, name='contacto'),

    # Carrito de compras (públicas: funcionan con o sin sesión iniciada).
    # Las que modifican el carrito solo aceptan POST (ver views_compra.py).
    path('carrito/', views_compra.carrito_ver, name='carrito'),
    path('carrito/agregar/<int:pk>/', views_compra.carrito_agregar, name='carrito_agregar'),
    path('carrito/actualizar/<int:pk>/', views_compra.carrito_actualizar, name='carrito_actualizar'),
    path('carrito/quitar/<int:pk>/', views_compra.carrito_quitar, name='carrito_quitar'),
    path('carrito/vaciar/', views_compra.carrito_vaciar, name='carrito_vaciar'),

    # Checkout (compra ficticia) y pedidos
    path('checkout/', views_compra.checkout, name='checkout'),
    path('pedidos/', views_compra.mis_pedidos, name='mis_pedidos'),
    path('pedidos/<int:pk>/', views_compra.pedido_detalle, name='pedido_detalle'),

    # CRUD de productos (protegidas con @login_required y @permission_required)
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
]
