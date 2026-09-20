"""
Formularios de la aplicación 'productos'.

Un ModelForm es un formulario que Django CONSTRUYE AUTOMÁTICAMENTE a partir
de un modelo: cada campo del modelo se convierte en un campo del formulario,
ya con sus validaciones básicas (largo máximo, tipo de dato, obligatorio...).

GUÍA PASO 5: "Las vistas deben usar formularios de Django (ModelForm)".
CRITERIO 2.1.4 (nivel Destacado): "validaciones personalizadas por cada campo
de formulario". Para lograrlo, CADA campo de cada formulario tiene su propio
método clean_<nombre_del_campo>() con reglas propias.

Cómo funcionan los métodos clean_<campo>():
  1. Django primero valida el campo con sus reglas por defecto.
  2. Si pasa, llama a clean_<campo>() para las reglas PERSONALIZADAS.
  3. Si hay un problema, se lanza ValidationError('mensaje'): el formulario NO
     se guarda y el mensaje se muestra al usuario junto a ese campo.
  4. Si todo está bien, se devuelve el valor (ya limpio) del campo.
"""

import os
import re
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from .models import Categoria, Mensaje, Producto

# ---------------------------------------------------------------------------
# Constantes con los límites de las validaciones (fáciles de cambiar aquí).
# ---------------------------------------------------------------------------
PRECIO_MAXIMO = Decimal('10000000')          # precio máximo permitido
STOCK_MAXIMO = 10000                         # unidades máximas en stock
MAX_PRODUCTOS_POR_CATEGORIA = 50             # tope de productos por categoría
TAMANO_MAXIMO_IMAGEN = 2 * 1024 * 1024       # 2 MB expresados en bytes
EXTENSIONES_IMAGEN = {'.jpg', '.jpeg', '.png', '.webp'}
DOMINIOS_NO_PERMITIDOS = {'mailinator.com', 'tempmail.com', '10minutemail.com'}


def con_puntos(numero):
    """Formatea un número con punto como separador de miles (10000 -> '10.000').

    Python usa la coma para los miles (formato inglés: 10,000). Como el sitio
    está en español, reemplazamos la coma por punto para mostrar los mensajes.
    """
    return f'{numero:,.0f}'.replace(',', '.')


class CategoriaForm(forms.ModelForm):
    """Formulario de categorías. Se usa en el panel /admin/ (ver admin.py), para
    que también allí se apliquen las validaciones personalizadas."""

    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']

    def clean_nombre(self):
        """Nombre: mínimo 3 caracteres y solo letras, números, espacios y guiones."""
        nombre = self.cleaned_data['nombre'].strip()

        if len(nombre) < 3:
            raise ValidationError('El nombre de la categoría debe tener al menos 3 caracteres.')
        if not re.fullmatch(r"[\w .'’\-]+", nombre):
            raise ValidationError('El nombre solo puede contener letras, números, espacios, puntos, apóstrofes y guiones.')

        return nombre

    def clean_descripcion(self):
        """Descripción (opcional): si se escribe, entre 10 y 200 caracteres."""
        descripcion = self.cleaned_data['descripcion'].strip()

        # Es opcional: un texto vacío es válido. Solo revisamos si escribieron algo.
        if descripcion and len(descripcion) < 10:
            raise ValidationError('Si escribes una descripción, debe tener al menos 10 caracteres.')
        if len(descripcion) > 200:
            raise ValidationError('La descripción no puede superar los 200 caracteres.')

        return descripcion


class ProductoForm(forms.ModelForm):
    """Formulario para CREAR y EDITAR productos (operaciones C y U del CRUD)."""

    class Meta:
        # model: de qué modelo se genera el formulario.
        model = Producto
        # fields: qué campos del modelo se incluyen (y en qué orden).
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'categoria', 'imagen']
        # labels: texto de la etiqueta que ve el usuario.
        labels = {
            'nombre': 'Nombre del producto',
            'descripcion': 'Descripción',
            'precio': 'Precio ($)',
            'stock': 'Stock (unidades)',
            'categoria': 'Categoría',
            'imagen': 'Imagen (opcional)',
        }
        # widgets: cómo se dibuja cada campo en HTML. Aquí solo le agregamos
        # las clases de Bootstrap ("form-control", "form-select") para el estilo.
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: Súper Poción'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    # -----------------------------------------------------------------------
    # Validaciones personalizadas: una por cada campo del formulario.
    # -----------------------------------------------------------------------
    def clean_nombre(self):
        """Nombre: mínimo 3 caracteres, caracteres válidos y sin duplicados."""
        nombre = self.cleaned_data['nombre'].strip()  # quita espacios sobrantes

        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')

        # Expresión regular: letras (con tildes), números, espacios, punto,
        # apóstrofe y guion. \w incluye letras y números de cualquier idioma.
        if not re.fullmatch(r"[\w .'’\-]+", nombre):
            raise ValidationError(
                'El nombre solo puede contener letras, números, espacios, '
                'puntos, apóstrofes y guiones.'
            )

        # No puede repetirse el nombre (sin distinguir mayúsculas/minúsculas).
        # .exclude(pk=...) evita que al EDITAR un producto choque consigo mismo.
        repetido = Producto.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetido.exists():
            raise ValidationError('Ya existe un producto con ese nombre.')

        return nombre

    def clean_descripcion(self):
        """Descripción: entre 10 y 500 caracteres."""
        descripcion = self.cleaned_data['descripcion'].strip()

        if len(descripcion) < 10:
            raise ValidationError('La descripción debe tener al menos 10 caracteres.')
        if len(descripcion) > 500:
            raise ValidationError('La descripción no puede superar los 500 caracteres.')

        return descripcion

    def clean_precio(self):
        """Precio: mayor que cero y con un tope razonable."""
        precio = self.cleaned_data['precio']

        if precio <= 0:
            raise ValidationError('El precio debe ser mayor que cero.')
        if precio > PRECIO_MAXIMO:
            raise ValidationError(f'El precio no puede superar ${con_puntos(PRECIO_MAXIMO)}.')

        return precio

    def clean_stock(self):
        """Stock: no negativo (lo garantiza el modelo) y con un tope máximo."""
        stock = self.cleaned_data['stock']

        if stock > STOCK_MAXIMO:
            raise ValidationError(f'El stock no puede superar las {con_puntos(STOCK_MAXIMO)} unidades.')

        return stock

    def clean_categoria(self):
        """Categoría: una misma categoría no puede tener más de 50 productos."""
        categoria = self.cleaned_data['categoria']

        # categoria.productos viene del related_name definido en el modelo.
        # Contamos los productos ya existentes, sin contar el que estamos editando.
        cantidad = categoria.productos.exclude(pk=self.instance.pk).count()
        if cantidad >= MAX_PRODUCTOS_POR_CATEGORIA:
            raise ValidationError(
                f'La categoría «{categoria}» ya tiene {MAX_PRODUCTOS_POR_CATEGORIA} '
                'productos (el máximo permitido). Elige otra categoría.'
            )

        return categoria

    def clean_imagen(self):
        """Imagen (opcional): solo JPG, PNG o WEBP, de máximo 2 MB."""
        imagen = self.cleaned_data.get('imagen')

        # Solo validamos si el usuario SUBIÓ un archivo nuevo. Cuando se edita
        # un producto sin cambiar la foto, 'imagen' es la que ya estaba guardada.
        if isinstance(imagen, UploadedFile):
            extension = os.path.splitext(imagen.name)[1].lower()
            if extension not in EXTENSIONES_IMAGEN:
                raise ValidationError('La imagen debe ser un archivo JPG, PNG o WEBP.')
            if imagen.size > TAMANO_MAXIMO_IMAGEN:
                raise ValidationError('La imagen no puede pesar más de 2 MB.')

        return imagen


class MensajeForm(forms.ModelForm):
    """Formulario de contacto. Es público: no requiere haber iniciado sesión."""

    class Meta:
        model = Mensaje
        fields = ['nombre', 'email', 'asunto', 'mensaje']
        labels = {
            'nombre': 'Tu nombre',
            'email': 'Tu correo electrónico',
            'asunto': 'Asunto',
            'mensaje': 'Mensaje',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nombre@correo.com'}),
            'asunto': forms.TextInput(attrs={'class': 'form-control'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    def clean_nombre(self):
        """Nombre: solo letras (con tildes), separadas por espacio, guion o apóstrofe."""
        nombre = self.cleaned_data['nombre'].strip()

        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')

        # [^\W\d_] = "una letra" (ni símbolo, ni número, ni guion bajo).
        # El patrón acepta: Ana, Ana María, José-Luis, D'Angelo...
        if not re.fullmatch(r"[^\W\d_]+(?:[ '\-][^\W\d_]+)*", nombre):
            raise ValidationError('El nombre solo puede contener letras y espacios.')

        return nombre

    def clean_email(self):
        """Email: se guarda en minúsculas y no se aceptan correos temporales."""
        email = self.cleaned_data['email'].strip().lower()

        # Tomamos lo que viene después de la '@' (el dominio del correo).
        dominio = email.split('@')[-1]
        if dominio in DOMINIOS_NO_PERMITIDOS:
            raise ValidationError('No se aceptan correos temporales. Usa un correo personal.')

        return email

    def clean_asunto(self):
        """Asunto: mínimo 5 caracteres."""
        asunto = self.cleaned_data['asunto'].strip()

        if len(asunto) < 5:
            raise ValidationError('El asunto debe tener al menos 5 caracteres.')

        return asunto

    def clean_mensaje(self):
        """Mensaje: entre 20 y 1000 caracteres."""
        mensaje = self.cleaned_data['mensaje'].strip()

        if len(mensaje) < 20:
            raise ValidationError('El mensaje debe tener al menos 20 caracteres.')
        if len(mensaje) > 1000:
            raise ValidationError('El mensaje no puede superar los 1000 caracteres.')

        return mensaje
