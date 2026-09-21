"""
Pruebas automáticas de la aplicación 'productos'.

Una PRUEBA automática es código que usa la aplicación como lo haría un usuario
(abre páginas, envía formularios, inicia sesión...) y comprueba que el resultado
sea el esperado. Sirven para demostrar que todo funciona y para detectar errores
si más adelante se cambia algo del proyecto.

CÓMO EJECUTARLAS (con el entorno virtual activado y MySQL encendido):

    python manage.py test

Django crea una base de datos TEMPORAL llamada test_tienda_backend, ejecuta las
pruebas y la elimina al terminar: tus datos reales NO se tocan. Para poder
crearla, el usuario de MySQL necesita permiso CREATE sobre ella (el archivo
crear_base_datos.sql ya lo otorga; con 'root' de XAMPP no hay problema).

Estructura: cada clase agrupa pruebas de un tema, y cada método que empieza con
'test_' es una prueba. Se usan las "aserciones" de Django (assertEqual,
assertContains, assertRedirects...) que fallan si lo obtenido no es lo esperado.

Mapa de las pruebas con la guía y los criterios de evaluación:
    ModelosTests                 -> paso 3 (dos clases relacionadas)
    AdminTests                   -> paso 4 y criterio 2.1.2
    CrudProductoTests            -> paso 5 y criterio 2.1.3
    SeguridadTests               -> paso 6 y criterio 2.1.4 (autenticación)
    ValidacionesProductoTests    -> criterio 2.1.4 (validaciones personalizadas)
    ContactoTests                -> criterios 2.1.1 y 2.1.4
    CatalogoPublicoTests         -> criterio 2.1.1 (catálogo de productos)
    DetalleProductoTests         -> vista de detalle y sugeridos
    CarritoTests                 -> carrito en sesión (con y sin cuenta)
    CheckoutYPedidosTests        -> compra ficticia y reserva de stock
    ValidacionDePedidosTests     -> validación/rechazo por el administrador
    PaletaTests                  -> paleta de colores
"""

import io
import shutil
import tempfile
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from PIL import Image

from .models import Categoria, Mensaje, Pedido, Producto, StockInsuficiente

# Las imágenes que suben las pruebas se guardan en una carpeta temporal (no en
# media/), y se borra al terminar (ver tearDownModule al final del archivo).
MEDIA_TEMPORAL = tempfile.mkdtemp()


def crear_imagen(nombre='foto.png', formato='PNG', pesada=False):
    """Fabrica una imagen válida en memoria para simular un archivo subido."""
    buffer = io.BytesIO()
    if pesada:
        # Ruido aleatorio: casi no se comprime, así el archivo supera los 2 MB.
        import os
        Image.frombytes('RGB', (1200, 1200), os.urandom(1200 * 1200 * 3)).save(buffer, formato)
    else:
        Image.new('RGB', (10, 10), 'red').save(buffer, formato)
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class BaseTest(TestCase):
    """Datos y utilidades comunes a todas las pruebas."""

    @classmethod
    def setUpTestData(cls):
        # setUpTestData se ejecuta UNA vez por clase y los datos se comparten.
        # Cada prueba se ejecuta dentro de una transacción que se revierte al
        # terminar, así que una prueba nunca ensucia a las demás.
        cls.superusuario = User.objects.create_superuser('admin_test', 'a@test.cl', 'clave12345')
        cls.herramientas = Categoria.objects.create(nombre='Herramientas', descripcion='Herramientas manuales de uso general.')
        cls.fijaciones = Categoria.objects.create(nombre='Fijaciones')
        cls.martillo = Producto.objects.create(
            nombre='Martillo', descripcion='Martillo de acero con mango ergonómico.',
            precio=Decimal('300'), stock=10, categoria=cls.herramientas)
        cls.tornillo = Producto.objects.create(
            nombre='Tornillo Autorroscante', descripcion='Tornillo para trabajos de carpintería.',
            precio=Decimal('200'), stock=0, categoria=cls.fijaciones)

    def datos_producto(self, **cambios):
        """Datos válidos para el formulario de producto; 'cambios' los modifica."""
        datos = {'nombre': 'Sierra Circular', 'descripcion': 'Sierra circular de uso profesional.',
                 'precio': '150.50', 'stock': '10', 'categoria': self.herramientas.pk}
        datos.update(cambios)
        return datos

    def contar_consultas(self, url):
        """Cuenta cuántas consultas SQL ejecuta una página."""
        with CaptureQueriesContext(connection) as consultas:
            self.client.get(url)
        return len(consultas)


# ---------------------------------------------------------------------------
# Guía paso 3: dos clases relacionadas + conexión MySQL
# ---------------------------------------------------------------------------
class ModelosTests(BaseTest):

    def test_la_base_de_datos_es_mysql(self):
        # connection.vendor vale 'mysql' tanto para MySQL como para MariaDB.
        self.assertEqual(connection.vendor, 'mysql')

    def test_producto_pertenece_a_una_categoria(self):
        self.assertEqual(self.martillo.categoria, self.herramientas)
        # related_name='productos' permite recorrer la relación al revés.
        self.assertIn(self.martillo, self.herramientas.productos.all())
        self.assertEqual(str(self.martillo), 'Martillo')

    def test_no_se_puede_borrar_una_categoria_con_productos(self):
        # on_delete=PROTECT protege los productos de un borrado accidental.
        with self.assertRaises(ProtectedError):
            self.herramientas.delete()


# ---------------------------------------------------------------------------
# Guía paso 4 y criterio 2.1.2: administrador de Django
# ---------------------------------------------------------------------------
class AdminTests(BaseTest):

    def setUp(self):
        self.client.force_login(self.superusuario)  # inicia sesión sin pasar por el formulario

    def test_los_tres_modelos_estan_registrados_y_sus_paginas_cargan(self):
        for modelo in (Categoria, Producto, Mensaje):
            self.assertTrue(admin.site.is_registered(modelo), modelo.__name__)
        for ruta in ('/admin/', '/admin/productos/categoria/', '/admin/productos/producto/',
                     '/admin/productos/mensaje/', '/admin/productos/producto/add/'):
            self.assertEqual(self.client.get(ruta).status_code, 200, ruta)

    def test_buscar_y_filtrar_productos(self):
        r = self.client.get('/admin/productos/producto/?q=Tornillo')
        self.assertContains(r, 'Tornillo Autorroscante')
        self.assertNotContains(r, 'Martillo')
        r = self.client.get(f'/admin/productos/producto/?categoria__id__exact={self.herramientas.pk}')
        self.assertContains(r, 'Martillo')
        self.assertNotContains(r, 'Tornillo Autorroscante')

    def test_el_admin_rechaza_datos_invalidos_con_nuestras_validaciones(self):
        casos = [
            ('/admin/productos/producto/add/',
             {'nombre': 'ab', 'descripcion': 'corta', 'precio': '0', 'stock': '20000', 'categoria': self.herramientas.pk},
             ('nombre', 'descripcion', 'precio', 'stock')),
            ('/admin/productos/categoria/add/', {'nombre': 'a', 'descripcion': 'corta'}, ('nombre', 'descripcion')),
            ('/admin/productos/mensaje/add/',
             {'nombre': 'Ana2', 'email': 'x@mailinator.com', 'asunto': 'hi', 'mensaje': 'corto'},
             ('nombre', 'email', 'asunto', 'mensaje')),
        ]
        for url, datos, campos_con_error in casos:
            with self.subTest(url=url):
                respuesta = self.client.post(url, datos)
                self.assertEqual(respuesta.status_code, 200)  # 200 = vuelve a mostrar el formulario
                errores = respuesta.context['adminform'].form.errors
                for campo in campos_con_error:
                    self.assertIn(campo, errores)

    def test_crear_editar_y_eliminar_desde_el_admin(self):
        # Crear
        r = self.client.post('/admin/productos/producto/add/', self.datos_producto(nombre='Taladro Pro'))
        self.assertEqual(r.status_code, 302)  # 302 = redirección tras guardar
        nuevo = Producto.objects.get(nombre='Taladro Pro')
        # Editar
        datos = self.datos_producto(nombre='Taladro Pro', precio='999')
        self.client.post(f'/admin/productos/producto/{nuevo.pk}/change/', datos)
        nuevo.refresh_from_db()
        self.assertEqual(nuevo.precio, Decimal('999'))
        # Eliminar
        self.client.post(f'/admin/productos/producto/{nuevo.pk}/delete/', {'post': 'yes'})
        self.assertFalse(Producto.objects.filter(pk=nuevo.pk).exists())

    def test_leer_y_eliminar_mensajes_desde_el_admin(self):
        mensaje = Mensaje.objects.create(nombre='Ana', email='a@a.cl', asunto='Consulta stock', mensaje='m' * 30)
        self.assertContains(self.client.get('/admin/productos/mensaje/'), 'Consulta stock')
        self.client.post(f'/admin/productos/mensaje/{mensaje.pk}/delete/', {'post': 'yes'})
        self.assertFalse(Mensaje.objects.filter(pk=mensaje.pk).exists())


# ---------------------------------------------------------------------------
# Guía paso 5 y criterio 2.1.3: operaciones CRUD
# ---------------------------------------------------------------------------
class CrudProductoTests(BaseTest):

    def setUp(self):
        self.client.force_login(self.superusuario)

    def test_crud_completo(self):
        # CREATE (con imagen)
        r = self.client.post('/productos/nuevo/', {**self.datos_producto(), 'imagen': crear_imagen()})
        self.assertRedirects(r, '/productos/', fetch_redirect_response=False)
        nuevo = Producto.objects.get(nombre='Sierra Circular')
        self.assertEqual(nuevo.precio, Decimal('150.50'))
        self.assertTrue(nuevo.imagen.name.startswith('productos/'))

        # READ: aparece en la lista y se muestra el mensaje de éxito
        r = self.client.get('/productos/')
        self.assertContains(r, 'Sierra Circular')
        self.assertContains(r, 'Producto creado correctamente')

        # UPDATE: el formulario llega con los datos actuales y se puede guardar
        self.assertContains(self.client.get(f'/productos/{nuevo.pk}/editar/'), 'value="Sierra Circular"')
        r = self.client.post(f'/productos/{nuevo.pk}/editar/', self.datos_producto(nombre='Sierra Circular X', stock='99'))
        self.assertRedirects(r, '/productos/', fetch_redirect_response=False)
        nuevo.refresh_from_db()
        self.assertEqual((nuevo.nombre, nuevo.stock), ('Sierra Circular X', 99))

        # DELETE: un GET solo pide confirmación; el POST es el que borra
        self.assertContains(self.client.get(f'/productos/{nuevo.pk}/eliminar/'), '¿Eliminar este producto?')
        self.assertTrue(Producto.objects.filter(pk=nuevo.pk).exists())
        r = self.client.post(f'/productos/{nuevo.pk}/eliminar/')
        self.assertRedirects(r, '/productos/', fetch_redirect_response=False)
        self.assertFalse(Producto.objects.filter(pk=nuevo.pk).exists())

    def test_editar_sin_cambiar_el_nombre_no_choca_consigo_mismo(self):
        r = self.client.post(f'/productos/{self.martillo.pk}/editar/',
                             self.datos_producto(nombre='Martillo', descripcion=self.martillo.descripcion))
        self.assertRedirects(r, '/productos/', fetch_redirect_response=False)

    def test_producto_inexistente_da_error_404(self):
        for ruta in ('/productos/99999/editar/', '/productos/99999/eliminar/'):
            self.assertEqual(self.client.get(ruta).status_code, 404)

    def test_la_lista_no_hace_una_consulta_por_cada_producto(self):
        # Si la vista no usara select_related, agregar 30 productos agregaría
        # ~30 consultas más. Con select_related el número no cambia.
        antes = self.contar_consultas('/productos/')
        Producto.objects.bulk_create([
            Producto(nombre=f'Extra {i}', descripcion='descripcion valida', precio=1, stock=1,
                     categoria=self.fijaciones) for i in range(30)])
        self.assertEqual(self.contar_consultas('/productos/'), antes)

    def test_un_texto_malicioso_se_muestra_escapado(self):
        # Django escapa el HTML automáticamente: el <script> se ve como texto, no se ejecuta.
        self.client.post('/productos/nuevo/', self.datos_producto(descripcion='<script>alert(1)</script> larga'))
        html = self.client.get('/productos/').content.decode()
        self.assertNotIn('<script>alert(1)', html)
        self.assertIn('&lt;script&gt;', html)


# ---------------------------------------------------------------------------
# Guía paso 6 y criterio 2.1.4: seguridad y autenticación
# ---------------------------------------------------------------------------
class SeguridadTests(BaseTest):

    def rutas_privadas(self):
        pk = self.martillo.pk
        return ['/productos/', '/productos/nuevo/', f'/productos/{pk}/editar/', f'/productos/{pk}/eliminar/']

    def test_sin_sesion_el_crud_redirige_a_admin_login(self):
        for ruta in self.rutas_privadas():
            with self.subTest(ruta=ruta):
                r = self.client.get(ruta)
                # El "?next=" hace que, tras iniciar sesión, se vuelva a la página pedida.
                self.assertRedirects(r, f'/admin/login/?next={ruta}', fetch_redirect_response=False)

    def test_las_paginas_publicas_no_piden_sesion(self):
        for ruta in ('/', '/catalogo/', '/contacto/'):
            self.assertEqual(self.client.get(ruta).status_code, 200, ruta)

    def test_login_correcto_e_incorrecto(self):
        malo = self.client.post('/admin/login/?next=/productos/', {'username': 'admin_test', 'password': 'mala'})
        self.assertEqual(malo.status_code, 200)  # se queda en el login
        self.assertEqual(self.client.get('/productos/').status_code, 302)  # sigue sin acceso

        bueno = self.client.post('/admin/login/?next=/productos/', {'username': 'admin_test', 'password': 'clave12345'})
        self.assertRedirects(bueno, '/productos/', fetch_redirect_response=False)
        self.assertContains(self.client.get('/productos/'), 'Martillo')

    def test_login_no_permite_redirigir_a_sitios_externos(self):
        r = self.client.post('/admin/login/?next=//sitio-malo.com/',
                             {'username': 'admin_test', 'password': 'clave12345', 'next': '//sitio-malo.com/'})
        self.assertNotIn('sitio-malo.com', r['Location'])

    def test_la_redireccion_por_defecto_del_login_existe(self):
        from django.conf import settings
        self.assertEqual(settings.LOGIN_REDIRECT_URL, '/productos/')

    def test_un_usuario_que_no_es_staff_no_puede_iniciar_sesion_en_el_admin(self):
        User.objects.create_user('normal', 'n@t.cl', 'clave12345')  # is_staff=False
        r = self.client.post('/admin/login/', {'username': 'normal', 'password': 'clave12345'})
        self.assertEqual(r.status_code, 200)  # el admin lo rechaza y muestra el formulario otra vez

    def test_cerrar_sesion_por_post_vuelve_a_bloquear_el_crud(self):
        self.client.force_login(self.superusuario)
        self.assertRedirects(self.client.post('/admin/logout/'), '/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/productos/').status_code, 302)

    def test_un_staff_sin_permisos_recibe_403_en_todo_el_crud(self):
        staff = User.objects.create_user('sin_permisos', 's@t.cl', 'clave12345', is_staff=True)
        self.client.force_login(staff)
        for ruta in self.rutas_privadas():
            with self.subTest(ruta=ruta):
                r = self.client.get(ruta)
                self.assertContains(r, 'Acceso denegado', status_code=403)  # usa templates/403.html
        self.client.post(f'/productos/{self.martillo.pk}/eliminar/')
        self.assertTrue(Producto.objects.filter(pk=self.martillo.pk).exists(), 'no debe poder borrar')

    def test_los_permisos_se_aplican_por_separado(self):
        staff = User.objects.create_user('solo_lectura', 's@t.cl', 'clave12345', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='view_producto'))
        self.client.force_login(staff)
        self.assertEqual(self.client.get('/productos/').status_code, 200)        # puede ver la lista
        self.assertEqual(self.client.get('/productos/nuevo/').status_code, 403)  # pero no crear
        self.assertEqual(self.client.get(f'/productos/{self.martillo.pk}/editar/').status_code, 403)
        self.assertEqual(self.client.get(f'/productos/{self.martillo.pk}/eliminar/').status_code, 403)


# ---------------------------------------------------------------------------
# Criterio 2.1.4: validaciones personalizadas por cada campo
# ---------------------------------------------------------------------------
class ValidacionesProductoTests(BaseTest):

    def setUp(self):
        self.client.force_login(self.superusuario)

    def errores(self, respuesta, campo):
        # Un formulario inválido NO redirige: vuelve a mostrarse (código 200).
        self.assertEqual(respuesta.status_code, 200)
        return ' '.join(respuesta.context['form'].errors.get(campo, []))

    def test_cada_campo_rechaza_valores_invalidos(self):
        casos = [  # (campo, valor inválido, texto que debe aparecer en el error)
            ('nombre', 'ab', 'al menos 3 caracteres'),
            ('nombre', '<script>', 'solo puede contener'),
            ('nombre', 'martillo', 'Ya existe un producto'),   # repetido, sin distinguir mayúsculas
            ('descripcion', 'corta', 'al menos 10 caracteres'),
            ('descripcion', 'x' * 501, 'no puede superar los 500'),
            ('precio', '0', 'mayor que cero'),
            ('precio', '-5', 'mayor que cero'),
            ('precio', '10000001', 'no puede superar'),
            ('stock', '10001', 'no puede superar'),
        ]
        cantidad = Producto.objects.count()
        for campo, valor, esperado in casos:
            with self.subTest(campo=campo, valor=valor[:12]):
                r = self.client.post('/productos/nuevo/', self.datos_producto(**{campo: valor}))
                self.assertIn(esperado, self.errores(r, campo))
        self.assertEqual(Producto.objects.count(), cantidad, 'ningún dato inválido debe guardarse')

    def test_una_categoria_no_puede_superar_50_productos(self):
        llena = Categoria.objects.create(nombre='Llena')
        Producto.objects.bulk_create([
            Producto(nombre=f'P{i}', descripcion='descripcion valida', precio=1, stock=1, categoria=llena)
            for i in range(50)])
        r = self.client.post('/productos/nuevo/', self.datos_producto(categoria=llena.pk))
        self.assertIn('máximo permitido', self.errores(r, 'categoria'))
        # y dejar la categoría sin elegir también se rechaza
        r = self.client.post('/productos/nuevo/', self.datos_producto(categoria=''))
        self.assertTrue(self.errores(r, 'categoria'))

    def test_validaciones_de_la_imagen(self):
        # Extensión no permitida (un PNG real, pero con nombre .gif)
        r = self.client.post('/productos/nuevo/', {**self.datos_producto(), 'imagen': crear_imagen('foto.gif')})
        self.assertIn('JPG, PNG o WEBP', self.errores(r, 'imagen'))
        # Demasiado pesada (más de 2 MB)
        r = self.client.post('/productos/nuevo/', {**self.datos_producto(), 'imagen': crear_imagen('grande.png', pesada=True)})
        self.assertIn('2 MB', self.errores(r, 'imagen'))
        # Un archivo que dice ser imagen pero no lo es
        r = self.client.post('/productos/nuevo/', {**self.datos_producto(),
                                                   'imagen': SimpleUploadedFile('x.png', b'no soy una imagen')})
        self.assertTrue(self.errores(r, 'imagen'))
        # Un WEBP válido sí se acepta
        r = self.client.post('/productos/nuevo/', {**self.datos_producto(nombre='Con webp'),
                                                   'imagen': crear_imagen('a.webp', 'WEBP')})
        self.assertEqual(r.status_code, 302)


# ---------------------------------------------------------------------------
# Criterios 2.1.1 y 2.1.4: formulario de contacto (público)
# ---------------------------------------------------------------------------
class ContactoTests(BaseTest):

    def datos_contacto(self, **cambios):
        datos = {'nombre': 'Ana Pérez', 'email': 'ana@correo.cl', 'asunto': 'Consulta stock',
                 'mensaje': 'Quisiera saber si tienen taladros inalámbricos disponibles.'}
        datos.update(cambios)
        return datos

    def test_es_publico_y_guarda_el_mensaje_en_la_base_de_datos(self):
        self.assertEqual(self.client.get('/contacto/').status_code, 200)  # sin iniciar sesión
        r = self.client.post('/contacto/', self.datos_contacto(email='ANA@Correo.CL'))
        self.assertRedirects(r, '/contacto/', fetch_redirect_response=False)
        self.assertEqual(Mensaje.objects.get().email, 'ana@correo.cl')  # se guarda en minúsculas
        self.assertContains(self.client.get('/contacto/'), 'Tu mensaje fue enviado')

    def test_cada_campo_rechaza_valores_invalidos(self):
        casos = [
            ('nombre', 'Ana2', 'solo puede contener letras'), ('nombre', 'Al', 'al menos 3'),
            ('email', 'no-es-correo', 'válida'), ('email', 'x@mailinator.com', 'correos temporales'),
            ('asunto', 'Hola', 'al menos 5'),
            ('mensaje', 'muy corto', 'al menos 20'), ('mensaje', 'm' * 1001, 'no puede superar los 1000'),
        ]
        for campo, valor, esperado in casos:
            with self.subTest(campo=campo, valor=valor[:12]):
                r = self.client.post('/contacto/', self.datos_contacto(**{campo: valor}))
                self.assertEqual(r.status_code, 200)
                self.assertIn(esperado, ' '.join(r.context['form'].errors.get(campo, [])))
        self.assertEqual(Mensaje.objects.count(), 0)


# ---------------------------------------------------------------------------
# Criterio 2.1.1: catálogo público de solo lectura
# ---------------------------------------------------------------------------
class CatalogoPublicoTests(BaseTest):

    def test_cualquier_visitante_ve_los_productos_con_precio_y_disponibilidad(self):
        r = self.client.get('/catalogo/')  # sin iniciar sesión
        self.assertContains(r, 'Martillo')
        self.assertContains(r, '$300')
        self.assertContains(r, 'Disponible')   # Martillo tiene stock 10
        self.assertContains(r, 'Agotado')      # Tornillo Autorroscante tiene stock 0

    def test_es_solo_lectura(self):
        r = self.client.get('/catalogo/')
        self.assertNotContains(r, '/editar/')
        self.assertNotContains(r, '/eliminar/')

    def test_se_puede_filtrar_por_categoria(self):
        r = self.client.get(f'/catalogo/?categoria={self.fijaciones.pk}')
        self.assertContains(r, 'Tornillo Autorroscante')
        self.assertNotContains(r, 'Martillo de acero')  # descripción del Martillo

    def test_un_filtro_invalido_se_ignora(self):
        r = self.client.get('/catalogo/?categoria=abc')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Martillo')
        self.assertContains(r, 'Tornillo Autorroscante')

    def test_no_hace_una_consulta_por_cada_producto(self):
        antes = self.contar_consultas('/catalogo/')
        Producto.objects.bulk_create([
            Producto(nombre=f'Extra {i}', descripcion='descripcion valida', precio=1, stock=1,
                     categoria=self.fijaciones) for i in range(30)])
        self.assertEqual(self.contar_consultas('/catalogo/'), antes)


# ---------------------------------------------------------------------------
# Detalle de producto, carrito, pedidos y validación por el administrador
# ---------------------------------------------------------------------------
class DetalleProductoTests(BaseTest):
    """Vista de detalle (pública) y productos sugeridos."""

    def test_detalle_responde_200_y_muestra_datos(self):
        r = self.client.get(f'/catalogo/{self.martillo.pk}/')
        self.assertContains(r, 'Martillo')
        self.assertContains(r, 'Agregar al carrito')

    def test_producto_inexistente_da_404(self):
        self.assertEqual(self.client.get('/catalogo/9999/').status_code, 404)

    def test_producto_agotado_no_muestra_boton_agregar(self):
        r = self.client.get(f'/catalogo/{self.tornillo.pk}/')
        self.assertContains(r, 'Agotado')
        self.assertNotContains(r, 'Agregar al carrito')

    def test_sugeridos_son_de_la_misma_categoria_y_maximo_tres(self):
        for i in range(5):
            Producto.objects.create(nombre=f'Herr {i}', descripcion='descripcion valida', precio=10,
                                    stock=5, categoria=self.herramientas)
        r = self.client.get(f'/catalogo/{self.martillo.pk}/')
        sugeridos = r.context['sugeridos']
        self.assertEqual(len(sugeridos), 3)
        for p in sugeridos:
            self.assertEqual(p.categoria, self.herramientas)
            self.assertNotEqual(p.pk, self.martillo.pk)

    def test_sin_otros_productos_no_hay_seccion_de_sugeridos(self):
        r = self.client.get(f'/catalogo/{self.martillo.pk}/')
        self.assertEqual(r.context['sugeridos'], [])
        self.assertNotContains(r, 'También te puede interesar')

    def test_catalogo_abre_el_detalle_en_pestana_nueva(self):
        r = self.client.get('/catalogo/')
        self.assertContains(r, f'href="/catalogo/{self.martillo.pk}/"')
        self.assertContains(r, 'target="_blank" rel="noopener noreferrer"')

    def test_detalle_no_hace_una_consulta_por_sugerido(self):
        url = f'/catalogo/{self.martillo.pk}/'
        antes = self.contar_consultas(url)
        Producto.objects.bulk_create([
            Producto(nombre=f'Extra {i}', descripcion='descripcion valida', precio=1, stock=1,
                     categoria=self.herramientas) for i in range(10)])
        self.assertEqual(self.contar_consultas(url), antes)


class CarritoTests(BaseTest):
    """Carrito en sesión: funciona sin cuenta y con cuenta."""

    def agregar(self, producto, cantidad=1, **extra):
        return self.client.post(f'/carrito/agregar/{producto.pk}/', {'cantidad': cantidad}, **extra)

    def carrito(self):
        return self.client.session.get('carrito', {})

    def test_agregar_sin_iniciar_sesion(self):
        self.agregar(self.martillo, 2)
        self.assertEqual(self.carrito(), {str(self.martillo.pk): 2})

    def test_agregar_suma_a_lo_existente(self):
        self.agregar(self.martillo, 2)
        self.agregar(self.martillo, 3)
        self.assertEqual(self.carrito()[str(self.martillo.pk)], 5)

    def test_cantidad_se_recorta_al_disponible(self):
        r = self.agregar(self.martillo, 50, follow=True)
        self.assertEqual(self.carrito()[str(self.martillo.pk)], 10)
        self.assertContains(r, 'Solo hay 10 unidades disponibles')

    def test_no_se_agrega_un_producto_agotado(self):
        self.agregar(self.tornillo)
        self.assertEqual(self.carrito(), {})

    def test_cantidades_invalidas_se_rechazan(self):
        for valor in ('0', '-3', 'abc', '100', ''):
            self.agregar(self.martillo, valor)
        self.assertEqual(self.carrito(), {})

    def test_agregar_por_get_da_405(self):
        self.assertEqual(self.client.get(f'/carrito/agregar/{self.martillo.pk}/').status_code, 405)

    def test_agregar_producto_inexistente_da_404(self):
        self.assertEqual(self.client.post('/carrito/agregar/9999/', {'cantidad': 1}).status_code, 404)

    def test_next_externo_se_ignora(self):
        r = self.client.post(f'/carrito/agregar/{self.martillo.pk}/',
                             {'cantidad': 1, 'next': 'https://malo.example.com/'})
        self.assertRedirects(r, '/carrito/', fetch_redirect_response=False)

    def test_next_del_mismo_sitio_se_respeta(self):
        r = self.client.post(f'/carrito/agregar/{self.martillo.pk}/',
                             {'cantidad': 1, 'next': '/catalogo/?categoria=1'})
        self.assertRedirects(r, '/catalogo/?categoria=1', fetch_redirect_response=False)

    def test_actualizar_quitar_y_vaciar(self):
        self.agregar(self.martillo, 2)
        self.client.post(f'/carrito/actualizar/{self.martillo.pk}/', {'cantidad': 4})
        self.assertEqual(self.carrito()[str(self.martillo.pk)], 4)
        self.client.post(f'/carrito/quitar/{self.martillo.pk}/')
        self.assertEqual(self.carrito(), {})
        self.agregar(self.martillo, 1)
        self.client.post('/carrito/vaciar/')
        self.assertEqual(self.carrito(), {})

    def test_actualizar_producto_que_no_esta_en_el_carrito(self):
        self.client.post(f'/carrito/actualizar/{self.martillo.pk}/', {'cantidad': 4})
        self.assertEqual(self.carrito(), {})

    def test_pagina_del_carrito_muestra_total(self):
        self.agregar(self.martillo, 2)
        r = self.client.get('/carrito/')
        self.assertContains(r, '$600')
        self.assertEqual(r.context['carrito_cantidad'], 2)

    def test_carrito_vacio(self):
        self.assertContains(self.client.get('/carrito/'), 'Tu carrito está vacío')

    def test_el_carrito_sobrevive_al_iniciar_sesion(self):
        self.agregar(self.martillo, 2)
        self.client.login(username='admin_test', password='clave12345')
        self.assertEqual(self.carrito()[str(self.martillo.pk)], 2)

    def test_agregar_con_sesion_iniciada(self):
        self.client.login(username='admin_test', password='clave12345')
        self.agregar(self.martillo, 1)
        self.assertEqual(self.carrito()[str(self.martillo.pk)], 1)

    def test_producto_eliminado_se_quita_del_carrito(self):
        extra = Producto.objects.create(nombre='Temporal', descripcion='descripcion valida',
                                        precio=5, stock=3, categoria=self.herramientas)
        self.agregar(extra, 1)
        extra.delete()
        self.client.get('/carrito/')
        self.assertEqual(self.carrito(), {})

    def test_carrito_excedido_bloquea_el_checkout(self):
        self.agregar(self.martillo, 5)
        Producto.objects.filter(pk=self.martillo.pk).update(stock=2)  # bajó el stock
        r = self.client.get('/carrito/')
        self.assertTrue(r.context['hay_problemas'])
        self.assertRedirects(self.client.get('/checkout/'), '/carrito/', fetch_redirect_response=False)


class CheckoutYPedidosTests(BaseTest):
    """Finalizar compra: crea un pedido pendiente y RESERVA (no descuenta) el stock."""

    def datos_pedido(self, **cambios):
        datos = {'nombre': 'Ana Pérez', 'email': 'Ana@Correo.cl', 'telefono': '+56 9 1234 5678',
                 'direccion': 'Av. Siempre Viva 742, Santiago', 'notas': ''}
        datos.update(cambios)
        return datos

    def llenar_carrito(self, cantidad=3):
        self.client.post(f'/carrito/agregar/{self.martillo.pk}/', {'cantidad': cantidad})

    def test_checkout_con_carrito_vacio_redirige_al_catalogo(self):
        self.assertRedirects(self.client.get('/checkout/'), '/catalogo/', fetch_redirect_response=False)

    def test_compra_exitosa_reserva_pero_no_descuenta(self):
        self.llenar_carrito(3)
        r = self.client.post('/checkout/', self.datos_pedido())
        pedido = Pedido.objects.get()
        self.assertRedirects(r, f'/pedidos/{pedido.pk}/')
        self.assertEqual(pedido.estado, Pedido.Estado.PENDIENTE)
        self.assertEqual(pedido.email, 'ana@correo.cl')
        self.assertEqual(pedido.telefono, '+56912345678')
        self.assertEqual(pedido.total, Decimal('900'))
        self.assertIsNone(pedido.usuario)
        self.martillo.refresh_from_db()
        self.assertEqual(self.martillo.stock, 10)       # el stock físico NO cambia
        self.assertEqual(self.martillo.disponible, 7)   # pero 3 quedan reservadas
        self.assertEqual(self.client.session.get('carrito', {}), {})  # carrito vacío

    def test_pedido_con_sesion_iniciada_queda_asociado_al_usuario(self):
        self.client.login(username='admin_test', password='clave12345')
        self.llenar_carrito(1)
        self.client.post('/checkout/', self.datos_pedido())
        self.assertEqual(Pedido.objects.get().usuario, self.superusuario)

    def test_el_pedido_guarda_una_copia_del_precio(self):
        self.llenar_carrito(1)
        self.client.post('/checkout/', self.datos_pedido())
        Producto.objects.filter(pk=self.martillo.pk).update(precio=999)
        self.assertEqual(Pedido.objects.get().total, Decimal('300'))

    def test_validaciones_de_cada_campo(self):
        self.llenar_carrito(1)
        casos = {
            'nombre': ['Al', 'Ana123'],
            'email': ['sin-arroba', 'x@mailinator.com'],
            'telefono': ['123', 'abcdefghij'],
            'direccion': ['corta'],
            'notas': ['x' * 301],
        }
        for campo, valores in casos.items():
            for valor in valores:
                r = self.client.post('/checkout/', self.datos_pedido(**{campo: valor}))
                self.assertEqual(r.status_code, 200, f'{campo}={valor!r}')
                self.assertIn(campo, r.context['form'].errors, f'{campo}={valor!r}')
        self.assertEqual(Pedido.objects.count(), 0)

    def test_stock_insuficiente_al_confirmar_no_crea_pedido(self):
        self.llenar_carrito(5)
        # Otro cliente reserva 8 unidades justo antes de confirmar.
        Pedido.crear([(self.martillo.pk, 8)], {**self.datos_pedido(), 'email': 'o@correo.cl'})
        r = self.client.post('/checkout/', self.datos_pedido(), follow=True)
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertContains(r, 'superan el stock disponible')

    def test_no_se_puede_reservar_mas_de_lo_disponible(self):
        with self.assertRaises(StockInsuficiente):
            Pedido.crear([(self.martillo.pk, 11)], self.datos_pedido())
        self.assertEqual(Pedido.objects.count(), 0)

    def test_reserva_reduce_disponible_en_catalogo(self):
        Pedido.crear([(self.martillo.pk, 10)], self.datos_pedido())
        r = self.client.get('/catalogo/')
        self.assertContains(r, 'Agotado')  # las 10 unidades están reservadas
        self.assertNotContains(r, 'Disponible')

    def test_confirmacion_solo_la_ve_su_dueno(self):
        self.llenar_carrito(1)
        self.client.post('/checkout/', self.datos_pedido())
        pedido = Pedido.objects.get()
        self.assertEqual(self.client.get(f'/pedidos/{pedido.pk}/').status_code, 200)
        self.assertContains(self.client.get('/pedidos/'), f'#{pedido.pk}')
        otro = self.client_class()  # otro navegador, sin sesión
        self.assertEqual(otro.get(f'/pedidos/{pedido.pk}/').status_code, 404)
        self.assertNotContains(otro.get('/pedidos/'), f'#{pedido.pk}')

    def test_un_revisor_con_permiso_puede_ver_cualquier_pedido(self):
        pedido = Pedido.crear([(self.martillo.pk, 1)], self.datos_pedido())
        self.client.login(username='admin_test', password='clave12345')
        self.assertEqual(self.client.get(f'/pedidos/{pedido.pk}/').status_code, 200)

    def test_pedidos_de_un_usuario_aparecen_al_iniciar_sesion(self):
        Pedido.crear([(self.martillo.pk, 1)], self.datos_pedido(), usuario=self.superusuario)
        self.client.login(username='admin_test', password='clave12345')
        self.assertContains(self.client.get('/pedidos/'), 'Pendiente de validación')

    def test_no_se_puede_eliminar_un_producto_con_pedidos(self):
        Pedido.crear([(self.martillo.pk, 1)], self.datos_pedido())
        with self.assertRaises(ProtectedError):
            self.martillo.delete()

    def test_la_vista_eliminar_muestra_error_y_no_500(self):
        Pedido.crear([(self.martillo.pk, 1)], self.datos_pedido())
        self.client.login(username='admin_test', password='clave12345')
        r = self.client.post(f'/productos/{self.martillo.pk}/eliminar/', follow=True)
        self.assertContains(r, 'forma parte de uno o más pedidos')
        self.assertTrue(Producto.objects.filter(pk=self.martillo.pk).exists())


class ValidacionDePedidosTests(BaseTest):
    """El administrador valida (descuenta stock) o rechaza (libera la reserva)."""

    URL = '/admin/productos/pedido/'

    def setUp(self):
        self.pedido = Pedido.crear(
            [(self.martillo.pk, 4)],
            {'nombre': 'Ana Pérez', 'email': 'ana@correo.cl', 'telefono': '+56912345678',
             'direccion': 'Av. Siempre Viva 742', 'notas': ''})

    def accion(self, nombre, pedido=None):
        return self.client.post(self.URL, {
            'action': nombre, '_selected_action': [(pedido or self.pedido).pk]}, follow=True)

    def stock(self):
        return Producto.objects.get(pk=self.martillo.pk).stock

    def test_validar_descuenta_el_stock_y_registra_al_revisor(self):
        self.client.login(username='admin_test', password='clave12345')
        self.accion('validar_pedidos')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.VALIDADO)
        self.assertEqual(self.pedido.revisado_por, self.superusuario)
        self.assertIsNotNone(self.pedido.revisado_en)
        self.assertEqual(self.stock(), 6)

    def test_rechazar_libera_la_reserva_sin_tocar_el_stock(self):
        self.client.login(username='admin_test', password='clave12345')
        self.assertEqual(Producto.objects.get(pk=self.martillo.pk).disponible, 6)
        self.accion('rechazar_pedidos')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.RECHAZADO)
        self.assertEqual(self.stock(), 10)
        self.assertEqual(Producto.objects.get(pk=self.martillo.pk).disponible, 10)

    def test_validar_dos_veces_no_descuenta_dos_veces(self):
        self.client.login(username='admin_test', password='clave12345')
        self.accion('validar_pedidos')
        r = self.accion('validar_pedidos')
        self.assertEqual(self.stock(), 6)
        self.assertContains(r, 'ya fue revisado')

    def test_no_se_puede_rechazar_un_pedido_validado(self):
        self.client.login(username='admin_test', password='clave12345')
        self.accion('validar_pedidos')
        self.accion('rechazar_pedidos')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.VALIDADO)

    def test_validar_falla_si_el_stock_real_bajo(self):
        self.client.login(username='admin_test', password='clave12345')
        Producto.objects.filter(pk=self.martillo.pk).update(stock=2)  # alguien lo bajó a mano
        r = self.accion('validar_pedidos')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.PENDIENTE)
        self.assertEqual(self.stock(), 2)
        self.assertContains(r, 'stock real es 2')

    def test_staff_sin_el_permiso_validar_no_puede_ejecutar_la_accion(self):
        staff = User.objects.create_user('staff', password='clave12345', is_staff=True)
        staff.user_permissions.add(*Permission.objects.filter(codename__in=['view_pedido', 'change_pedido']))
        self.client.login(username='staff', password='clave12345')
        r = self.client.get(self.URL)
        self.assertNotContains(r, 'Validar pedidos seleccionados')
        self.accion('validar_pedidos')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.PENDIENTE)
        self.assertEqual(self.stock(), 10)

    def test_staff_con_el_permiso_validar_si_puede(self):
        staff = User.objects.create_user('staff', password='clave12345', is_staff=True)
        staff.user_permissions.add(*Permission.objects.filter(
            codename__in=['view_pedido', 'change_pedido', 'validar_pedido']))
        self.client.login(username='staff', password='clave12345')
        self.accion('validar_pedidos')
        self.assertEqual(self.stock(), 6)

    def test_el_admin_no_permite_crear_pedidos_a_mano(self):
        self.client.login(username='admin_test', password='clave12345')
        self.assertEqual(self.client.get(self.URL + 'add/').status_code, 403)

    def test_pedido_validado_no_se_puede_borrar_desde_el_admin(self):
        self.client.login(username='admin_test', password='clave12345')
        self.accion('validar_pedidos')
        self.assertEqual(self.client.get(f'{self.URL}{self.pedido.pk}/delete/').status_code, 403)

    def test_lista_admin_y_detalle_cargan_y_muestran_total(self):
        self.client.login(username='admin_test', password='clave12345')
        self.assertContains(self.client.get(self.URL), '$1.200')
        self.assertContains(self.client.get(f'{self.URL}{self.pedido.pk}/change/'), 'Martillo')

    def test_lista_de_productos_del_admin_muestra_reservado(self):
        self.client.login(username='admin_test', password='clave12345')
        r = self.client.get('/admin/productos/producto/')
        self.assertContains(r, 'Reservado')

    def test_el_menu_avisa_de_pedidos_pendientes_solo_a_quien_valida(self):
        self.assertNotContains(self.client.get('/'), 'Validar pedidos')
        self.client.login(username='admin_test', password='clave12345')
        self.assertContains(self.client.get('/'), 'Validar pedidos')


class PaletaTests(BaseTest):
    """La paleta 'azul acero + amarillo señal' reemplazó al rojo del proyecto anterior."""

    def test_variables_de_la_paleta(self):
        r = self.client.get('/')
        self.assertContains(r, '#1F3A5F')
        self.assertContains(r, '#FFC20E')

    def test_ya_no_quedan_restos_del_rojo_anterior(self):
        contenido = self.client.get('/').content.decode().lower()
        for rojo in ('#e3350d', '#c0392b', '#dc3545'):
            self.assertNotIn(rojo, contenido)


def tearDownModule():
    """Se ejecuta una vez al terminar todas las pruebas: borra las imágenes temporales."""
    shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)
