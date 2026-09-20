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
"""

from django.db import models


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

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


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
