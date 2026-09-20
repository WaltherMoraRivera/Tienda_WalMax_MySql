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

from django.contrib import admin

from .forms import CategoriaForm, MensajeForm, ProductoForm
from .models import Categoria, Mensaje, Producto


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
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'creado')
    # list_filter: agrega filtros laterales (aquí, por categoría).
    list_filter = ('categoria',)
    search_fields = ('nombre', 'descripcion')


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    form = MensajeForm
    list_display = ('asunto', 'nombre', 'email', 'fecha_envio')
    search_fields = ('asunto', 'nombre', 'email')
    # readonly_fields: la fecha de envío se muestra pero no se puede modificar.
    readonly_fields = ('fecha_envio',)
