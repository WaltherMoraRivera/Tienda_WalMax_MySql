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

from .models import Categoria, Mensaje, Producto

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
        cls.pociones = Categoria.objects.create(nombre='Pociones', descripcion='Curan a tus Pokémon.')
        cls.bayas = Categoria.objects.create(nombre='Bayas')
        cls.pocion = Producto.objects.create(
            nombre='Poción', descripcion='Restaura 20 PS de un Pokémon.',
            precio=Decimal('300'), stock=10, categoria=cls.pociones)
        cls.baya = Producto.objects.create(
            nombre='Baya Aranja', descripcion='Cura los PS de un Pokémon.',
            precio=Decimal('200'), stock=0, categoria=cls.bayas)

    def datos_producto(self, **cambios):
        """Datos válidos para el formulario de producto; 'cambios' los modifica."""
        datos = {'nombre': 'Cinta Premier', 'descripcion': 'Cinta conmemorativa muy especial.',
                 'precio': '150.50', 'stock': '10', 'categoria': self.pociones.pk}
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
        self.assertEqual(self.pocion.categoria, self.pociones)
        # related_name='productos' permite recorrer la relación al revés.
        self.assertIn(self.pocion, self.pociones.productos.all())
        self.assertEqual(str(self.pocion), 'Poción')

    def test_no_se_puede_borrar_una_categoria_con_productos(self):
        # on_delete=PROTECT protege los productos de un borrado accidental.
        with self.assertRaises(ProtectedError):
            self.pociones.delete()


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
        r = self.client.get('/admin/productos/producto/?q=Baya')
        self.assertContains(r, 'Baya Aranja')
        self.assertNotContains(r, 'Poción')
        r = self.client.get(f'/admin/productos/producto/?categoria__id__exact={self.pociones.pk}')
        self.assertContains(r, 'Poción')
        self.assertNotContains(r, 'Baya Aranja')

    def test_el_admin_rechaza_datos_invalidos_con_nuestras_validaciones(self):
        casos = [
            ('/admin/productos/producto/add/',
             {'nombre': 'ab', 'descripcion': 'corta', 'precio': '0', 'stock': '20000', 'categoria': self.pociones.pk},
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
        r = self.client.post('/admin/productos/producto/add/', self.datos_producto(nombre='Cinta Ultra'))
        self.assertEqual(r.status_code, 302)  # 302 = redirección tras guardar
        nuevo = Producto.objects.get(nombre='Cinta Ultra')
        # Editar
        datos = self.datos_producto(nombre='Cinta Ultra', precio='999')
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
        nuevo = Producto.objects.get(nombre='Cinta Premier')
        self.assertEqual(nuevo.precio, Decimal('150.50'))
        self.assertTrue(nuevo.imagen.name.startswith('productos/'))

        # READ: aparece en la lista y se muestra el mensaje de éxito
        r = self.client.get('/productos/')
        self.assertContains(r, 'Cinta Premier')
        self.assertContains(r, 'Producto creado correctamente')

        # UPDATE: el formulario llega con los datos actuales y se puede guardar
        self.assertContains(self.client.get(f'/productos/{nuevo.pk}/editar/'), 'value="Cinta Premier"')
        r = self.client.post(f'/productos/{nuevo.pk}/editar/', self.datos_producto(nombre='Cinta Premier X', stock='99'))
        self.assertRedirects(r, '/productos/', fetch_redirect_response=False)
        nuevo.refresh_from_db()
        self.assertEqual((nuevo.nombre, nuevo.stock), ('Cinta Premier X', 99))

        # DELETE: un GET solo pide confirmación; el POST es el que borra
        self.assertContains(self.client.get(f'/productos/{nuevo.pk}/eliminar/'), '¿Eliminar este producto?')
        self.assertTrue(Producto.objects.filter(pk=nuevo.pk).exists())
        r = self.client.post(f'/productos/{nuevo.pk}/eliminar/')
        self.assertRedirects(r, '/productos/', fetch_redirect_response=False)
        self.assertFalse(Producto.objects.filter(pk=nuevo.pk).exists())

    def test_editar_sin_cambiar_el_nombre_no_choca_consigo_mismo(self):
        r = self.client.post(f'/productos/{self.pocion.pk}/editar/',
                             self.datos_producto(nombre='Poción', descripcion=self.pocion.descripcion))
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
                     categoria=self.bayas) for i in range(30)])
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
        pk = self.pocion.pk
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
        self.assertContains(self.client.get('/productos/'), 'Poción')

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
        self.client.post(f'/productos/{self.pocion.pk}/eliminar/')
        self.assertTrue(Producto.objects.filter(pk=self.pocion.pk).exists(), 'no debe poder borrar')

    def test_los_permisos_se_aplican_por_separado(self):
        staff = User.objects.create_user('solo_lectura', 's@t.cl', 'clave12345', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='view_producto'))
        self.client.force_login(staff)
        self.assertEqual(self.client.get('/productos/').status_code, 200)        # puede ver la lista
        self.assertEqual(self.client.get('/productos/nuevo/').status_code, 403)  # pero no crear
        self.assertEqual(self.client.get(f'/productos/{self.pocion.pk}/editar/').status_code, 403)
        self.assertEqual(self.client.get(f'/productos/{self.pocion.pk}/eliminar/').status_code, 403)


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
            ('nombre', 'poción', 'Ya existe un producto'),   # repetido, sin distinguir mayúsculas
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
                 'mensaje': 'Quisiera saber si tienen Master Ball.'}
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
        self.assertContains(r, 'Poción')
        self.assertContains(r, '$300')
        self.assertContains(r, 'Disponible')   # Poción tiene stock 10
        self.assertContains(r, 'Agotado')      # Baya Aranja tiene stock 0

    def test_es_solo_lectura(self):
        r = self.client.get('/catalogo/')
        self.assertNotContains(r, '/editar/')
        self.assertNotContains(r, '/eliminar/')

    def test_se_puede_filtrar_por_categoria(self):
        r = self.client.get(f'/catalogo/?categoria={self.bayas.pk}')
        self.assertContains(r, 'Baya Aranja')
        self.assertNotContains(r, 'Restaura 20 PS')  # descripción de la Poción

    def test_un_filtro_invalido_se_ignora(self):
        r = self.client.get('/catalogo/?categoria=abc')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Poción')
        self.assertContains(r, 'Baya Aranja')

    def test_no_hace_una_consulta_por_cada_producto(self):
        antes = self.contar_consultas('/catalogo/')
        Producto.objects.bulk_create([
            Producto(nombre=f'Extra {i}', descripcion='descripcion valida', precio=1, stock=1,
                     categoria=self.bayas) for i in range(30)])
        self.assertEqual(self.contar_consultas('/catalogo/'), antes)


def tearDownModule():
    """Se ejecuta una vez al terminar todas las pruebas: borra las imágenes temporales."""
    shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)
