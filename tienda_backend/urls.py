"""
Rutas principales del proyecto tienda_backend.

Este es el PRIMER archivo de rutas que consulta Django. Desde aquí se
"delegan" las direcciones a otros archivos con include():

    /admin/...   -> panel de administración de Django (login incluido)
    /...         -> rutas de nuestra aplicación 'productos' (productos/urls.py)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Panel de administración. Su formulario de login (/admin/login/) es el
    # que usa el proyecto para autenticar usuarios (guía paso 6).
    path('admin/', admin.site.urls),

    # Todas las demás direcciones las resuelve la aplicación 'productos'.
    path('', include('productos.urls')),
]

# Durante el desarrollo (DEBUG=True) Django sirve las imágenes subidas
# desde MEDIA_ROOT en la dirección MEDIA_URL (/media/...).
# En un servidor real esto lo hace el servidor web, no Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
