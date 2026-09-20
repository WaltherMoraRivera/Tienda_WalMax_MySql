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

from . import views

urlpatterns = [
    # Páginas públicas (cualquier visitante puede verlas)
    path('', views.inicio, name='inicio'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('contacto/', views.contacto, name='contacto'),

    # CRUD de productos (protegidas con @login_required y @permission_required)
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
]
