# DOCUMENTACIÓN — Programación Backend

**Proyecto:** Ferretería Walmax (`tienda_backend`) — Django 4.2 con base de datos MySQL
**Asignatura:** Programación Backend · Aprendizaje esperado 2.1 «Framework Backend»
**Ítem I:** Implementa un proyecto en framework Django con conexión a base de datos MySQL

Este documento explica, paso a paso y en orden, cómo se construyó el proyecto de la guía,
qué hace cada archivo y cómo se cumple cada criterio de la tabla de evaluación.
Está pensado para que puedas **reconstruir el proyecto desde cero** y también para **explicarlo en la demostración del laboratorio**.

---

## Índice

1. [¿Qué hace el proyecto?](#1-qué-hace-el-proyecto)
2. [Tecnologías y versiones](#2-tecnologías-y-versiones)
3. [Estructura de carpetas](#3-estructura-de-carpetas)
4. [Puesta en marcha rápida](#4-puesta-en-marcha-rápida)
5. [Paso a paso de la realización de la guía](#5-paso-a-paso-de-la-realización-de-la-guía)
   - [Paso 0 — Preparar el entorno](#paso-0--preparar-el-entorno)
   - [Paso 1 — Crear el proyecto y la aplicación](#paso-1--crear-el-proyecto-y-la-aplicación)
   - [Paso 2 — Configurar la base de datos](#paso-2--configurar-la-base-de-datos)
   - [Paso 3 — Definir los modelos](#paso-3--definir-los-modelos)
   - [Paso 4 — Registrar los modelos en el admin](#paso-4--registrar-los-modelos-en-el-admin)
   - [Paso 5 — Operaciones CRUD](#paso-5--operaciones-crud-formularios-vistas-rutas-y-plantillas)
   - [Paso 6 — Seguridad y autenticación](#paso-6--seguridad-y-autenticación)
   - [Paso 7 — Demostración en el laboratorio](#paso-7--demostración-en-el-laboratorio)
   - [Extra — Formulario de contacto](#extra--formulario-de-contacto)
6. [Verificación de la tabla de criterios (puntaje máximo)](#6-verificación-de-la-tabla-de-criterios-puntaje-máximo)
7. [Pruebas realizadas](#7-pruebas-realizadas)
8. [Solución de problemas](#8-solución-de-problemas)
9. [Glosario](#9-glosario)
10. [Anexo: credenciales y comandos útiles](#10-anexo-credenciales-y-comandos-útiles)
11. [Recomendaciones fuera del alcance de la guía y riesgos del laboratorio](#11-recomendaciones-fuera-del-alcance-de-la-guía-y-riesgos-del-laboratorio)

---

## 1. ¿Qué hace el proyecto?

**Ferretería Walmax** es una aplicación web que permite **promocionar y administrar productos** (herramientas, fijaciones, pinturas, etc.).

| Funcionalidad | Quién puede usarla | Dónde |
|---|---|---|
| Ver la página de inicio | Cualquier visitante | `/` |
| **Ver el catálogo** de productos (solo lectura, con filtro por categoría) | Cualquier visitante | `/catalogo/` |
| Enviar un mensaje de contacto (se guarda en MySQL) | Cualquier visitante | `/contacto/` |
| **Listar** productos (administración) | Sesión iniciada + permiso `view_producto` | `/productos/` |
| **Crear** un producto | Sesión iniciada + permiso `add_producto` | `/productos/nuevo/` |
| **Editar** un producto | Sesión iniciada + permiso `change_producto` | `/productos/<id>/editar/` |
| **Eliminar** un producto (con confirmación) | Sesión iniciada + permiso `delete_producto` | `/productos/<id>/eliminar/` |
| Gestionar categorías, productos y mensajes | Administradores | `/admin/` |

Si alguien intenta entrar a `/productos/` sin haber iniciado sesión, el sistema lo **redirige a `/admin/login/`**, tal como pide la guía. Si inició sesión pero su cuenta **no tiene el permiso**, ve una página «Acceso denegado» (error 403). El superusuario tiene todos los permisos.

---

## 2. Tecnologías y versiones

| Tecnología | Versión | Para qué se usa |
|---|---|---|
| Python | 3.12 | Lenguaje de programación |
| Django | 4.2 LTS (4.2.30) | Framework web (la guía pide Django 4.2) |
| MySQL | 8.0 | Base de datos relacional |
| mysqlclient | 2.3.0 | «Driver»: permite que Django hable con MySQL |
| Pillow | 12.3.0 | Librería de imágenes (requerida por el campo `ImageField`) |
| Bootstrap | 5.3.3 (CDN) | Estilos de las páginas (botones, tablas, formularios) |

**¿Por qué Python 3.12 y no el más reciente?** Django 4.2 (la versión que exige la guía) no es compatible con Python 3.14, que era el Python por defecto del equipo. Python 3.12 sí es compatible, así que el proyecto vive en un **entorno virtual** (`venv`) creado con Python 3.12. El entorno virtual es una «cajita» que guarda las librerías de este proyecto sin mezclarlas con las de otros proyectos.

---

## 3. Estructura de carpetas

```
Programacion_Backend/
├── DOCUMENTACION.md            ← este documento
├── manage.py                   ← herramienta de línea de comandos de Django
├── requirements.txt            ← lista de librerías a instalar (pip install -r ...)
├── crear_base_datos.sql        ← crea la base de datos y el usuario en MySQL
├── .gitignore
├── venv/                       ← entorno virtual (Python 3.12 + librerías)
│
├── tienda_backend/             ← CONFIGURACIÓN del proyecto
│   ├── settings.py             ← base de datos, apps instaladas, login, media...
│   └── urls.py                 ← rutas principales (admin + delegación a 'productos')
│
├── productos/                  ← APLICACIÓN (la lógica del negocio)
│   ├── models.py               ← tablas: Categoria, Producto, Mensaje
│   ├── admin.py                ← registro de los modelos en /admin/
│   ├── forms.py                ← formularios (ModelForm) + VALIDACIONES personalizadas
│   ├── views.py                ← vistas: inicio, catálogo público, CRUD de productos, contacto
│   ├── urls.py                 ← rutas de la aplicación
│   ├── tests.py                ← 32 pruebas automáticas (python manage.py test)
│   ├── migrations/0001_initial.py   ← «plano» para crear las tablas en MySQL
│   └── fixtures/datos_iniciales.json ← datos de ejemplo (opcional)
│
├── templates/                  ← PLANTILLAS HTML
│   ├── base.html               ← diseño común (menú, mensajes, pie de página)
│   ├── 403.html                ← página «Acceso denegado» (falta de permisos)
│   └── productos/
│       ├── inicio.html · catalogo.html · lista.html · formulario.html
│       ├── confirmar_eliminar.html · contacto.html
│       └── _campos_formulario.html  ← fragmento reutilizable de campos de formulario
│
└── media/productos/            ← imágenes de los productos (subidas por formulario)
```

---

## 4. Puesta en marcha rápida

Esta sección es para **ejecutar el proyecto ya terminado** (por ejemplo, en el laboratorio). Para entender cómo se construyó, sigue la sección 5.

Abre PowerShell dentro de la carpeta `Programacion_Backend` y ejecuta, en orden:

```powershell
# 1. Crear y activar el entorno virtual con Python 3.12 (solo la primera vez la creación)
py -3.12 -m venv venv
venv\Scripts\activate

# 2. Instalar las librerías del proyecto
pip install -r requirements.txt

# 3. Crear la base de datos y el usuario en MySQL (una sola vez; pide la contraseña de root)
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -e "source crear_base_datos.sql"

# 4. Crear las tablas en MySQL
python manage.py migrate

# 5. (Opcional) Cargar productos de ejemplo
python manage.py loaddata datos_iniciales

# 6. Crear un usuario administrador (te pedirá nombre, correo y contraseña)
python manage.py createsuperuser

# 7. Iniciar el servidor
python manage.py runserver

# (Opcional) Ejecutar las 32 pruebas automáticas (usa una base temporal; no toca tus datos)
python manage.py test
```

Luego abre <http://127.0.0.1:8000/> en el navegador.

> **Si el laboratorio usa XAMPP** (MySQL/MariaDB con usuario `root` sin contraseña), revisa la sección [Plan B para el laboratorio](#plan-b-si-el-laboratorio-usa-xampp).

---

## 5. Paso a paso de la realización de la guía

La guía tiene 7 pasos. Aquí se agrega un «Paso 0» para preparar el entorno y un «Extra» para el formulario de contacto que menciona la tabla de criterios.

### Paso 0 — Preparar el entorno

**Objetivo:** tener instalado todo lo necesario antes de escribir código.

1. **Instalar y arrancar MySQL** (la guía pide MySQL o PostgreSQL; se eligió MySQL porque la tabla de criterios lo nombra en todos sus niveles). Debe existir un servidor MySQL en ejecución. Puedes comprobarlo así:

   ```powershell
   Get-Service MySQL80        # debe decir "Running"
   ```

2. **Crear la carpeta del proyecto y su entorno virtual:**

   ```powershell
   mkdir Programacion_Backend
   cd Programacion_Backend
   py -3.12 -m venv venv          # crea el entorno virtual con Python 3.12
   venv\Scripts\activate          # lo activa (el prompt mostrará "(venv)")
   ```

3. **Instalar Django 4.2, el driver de MySQL y Pillow:**

   ```powershell
   python -m pip install "Django>=4.2,<4.3" mysqlclient Pillow
   ```

   `Django>=4.2,<4.3` significa «cualquier versión 4.2.x»: así respetamos lo que pide la guía y recibimos las correcciones de seguridad.

4. Dejar registradas las versiones exactas en `requirements.txt`:

   ```text
   Django==4.2.30
   mysqlclient==2.3.0
   Pillow==12.3.0
   ```

> **Regla de oro:** cada vez que abras una terminal nueva, activa el entorno con `venv\Scripts\activate` antes de usar `python manage.py ...`. Si no lo haces, Python no encontrará Django.

---

### Paso 1 — Crear el proyecto y la aplicación

**Guía:** «Crear el proyecto Django (ejemplo: `tienda_backend`) y crear una aplicación».

```powershell
django-admin startproject tienda_backend .
python manage.py startapp productos
```

- `startproject tienda_backend .` crea la carpeta de **configuración** `tienda_backend/` y el archivo `manage.py`. El punto final (`.`) evita que Django cree una carpeta extra anidada.
- `startapp productos` crea la **aplicación** `productos/`. Un proyecto Django puede tener varias aplicaciones; cada una agrupa una parte de la lógica (aquí, todo lo relacionado con productos).

> **Proyecto vs. aplicación:** el *proyecto* es el sitio completo (configuración global); la *aplicación* es un módulo con una función concreta dentro de ese sitio.

También se crearon las carpetas `templates/` (HTML) y `media/` (imágenes subidas) en la raíz.

---

### Paso 2 — Configurar la base de datos

**Guía:** «Utilizar MySQL o PostgreSQL. Registrar la app en el archivo `settings.py`».

#### 2.1 Crear la base de datos y el usuario en MySQL

Django **no crea la base de datos**: solo crea las *tablas* dentro de una base que ya exista. Por eso se preparó el archivo `crear_base_datos.sql`:

```sql
CREATE DATABASE IF NOT EXISTS tienda_backend
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'tienda_user'@'localhost' IDENTIFIED BY 'TiendaDev2026';

GRANT ALL PRIVILEGES ON tienda_backend.* TO 'tienda_user'@'localhost';
GRANT ALL PRIVILEGES ON `test\_tienda_backend`.* TO 'tienda_user'@'localhost';
FLUSH PRIVILEGES;
```

- `utf8mb4` permite guardar tildes, «ñ» y emojis sin problemas.
- Se crea un **usuario propio del proyecto** con permisos solo sobre `tienda_backend`. Así Django nunca usa el superusuario `root` (buena práctica de seguridad).
- La línea `test\_tienda_backend` solo se necesita para ejecutar pruebas automáticas.

Se ejecuta una sola vez, con el usuario administrador de MySQL:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -e "source crear_base_datos.sql"
```

> Si no muestra ningún mensaje, **significa que salió bien** (MySQL solo habla cuando hay un error).

#### 2.2 Conectar Django con MySQL — `tienda_backend/settings.py`

Por defecto Django usa SQLite. Se reemplazó el bloque `DATABASES`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',   # motor: MySQL
        'NAME': 'tienda_backend',               # nombre de la base de datos
        'USER': 'tienda_user',                  # usuario creado en el paso anterior
        'PASSWORD': 'TiendaDev2026',
        'HOST': '127.0.0.1',                    # el servidor está en este mismo equipo
        'PORT': '3306',                         # puerto estándar de MySQL
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}
```

> **¿Por qué `127.0.0.1` y no `localhost`?** En Windows, `localhost` a veces se resuelve por IPv6 (`::1`) y puede llegar a *otro* servidor distinto del esperado. `127.0.0.1` es siempre IPv4 y evita esa confusión.

#### 2.3 Registrar la aplicación — `INSTALLED_APPS`

Django solo «ve» las aplicaciones listadas aquí. Se agregó `'productos'` al final:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'productos',          # <-- nuestra aplicación
]
```

#### 2.4 Otros ajustes en `settings.py`

| Ajuste | Valor | Para qué sirve |
|---|---|---|
| `TEMPLATES['DIRS']` | `[BASE_DIR / 'templates']` | Django busca las plantillas HTML en la carpeta `templates/` |
| `LANGUAGE_CODE` | `'es'` | Admin y mensajes de error en español |
| `TIME_ZONE` | `'America/Santiago'` | Fechas en hora de Chile |
| `MEDIA_URL` / `MEDIA_ROOT` | `'/media/'` / `BASE_DIR / 'media'` | Dónde se guardan y sirven las imágenes subidas |
| `LOGIN_URL` | `'/admin/login/'` | Adónde se envía a quien no ha iniciado sesión (**paso 6**) |
| `LOGOUT_REDIRECT_URL` | `'/'` | Adónde se vuelve después de cerrar sesión |
| `MESSAGE_TAGS` | `{ERROR: 'danger'}` | Los mensajes de error usan el color rojo de Bootstrap |

**Comprobación:** `python manage.py check` debe responder `System check identified no issues`.

---

### Paso 3 — Definir los modelos

**Guía:** «Crear dos clases relacionadas en `models.py`, con sus correspondientes campos».

Un **modelo** es una clase de Python que representa una **tabla** de la base de datos: cada atributo es una columna y cada objeto es una fila.

Las dos clases relacionadas son `Categoria` y `Producto`: **una categoría tiene muchos productos** y **cada producto pertenece a una categoría** (relación uno-a-muchos).

```python
class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    descripcion = models.TextField(blank=True)

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    creado = models.DateTimeField(auto_now_add=True)
```

| Campo | Tipo Django | Explicación |
|---|---|---|
| `nombre` | `CharField` | Texto corto con largo máximo obligatorio |
| `descripcion` | `TextField` | Texto largo |
| `precio` | `DecimalField` | Número con decimales exactos (ideal para dinero) |
| `stock` | `PositiveIntegerField` | Entero que no admite negativos |
| `imagen` | `ImageField` | Foto del producto; en la BD solo se guarda su ruta |
| `categoria` | `ForeignKey` | **La relación** entre las dos clases |
| `creado` | `DateTimeField(auto_now_add=True)` | Django guarda solo la fecha de creación |

**`on_delete=models.PROTECT`**: si una categoría tiene productos, Django **no permite borrarla** (evita perder productos por accidente).

Además existe un tercer modelo, `Mensaje` (nombre, email, asunto, mensaje, fecha), para el formulario de contacto (ver [Extra](#extra--formulario-de-contacto)).

#### Crear las tablas en MySQL: migraciones

Las migraciones traducen los modelos a tablas. Son **dos comandos**:

```powershell
python manage.py makemigrations   # 1) genera el «plano» (productos/migrations/0001_initial.py)
python manage.py migrate          # 2) ejecuta el plano en MySQL y crea las tablas
```

Tablas creadas en MySQL: `productos_categoria`, `productos_producto` y `productos_mensaje`, además de las tablas internas de Django (usuarios, sesiones, permisos, etc.).

> Puedes ver el SQL exacto que se ejecutará con: `python manage.py sqlmigrate productos 0001`.

---

### Paso 4 — Registrar los modelos en el admin

**Guía:** «En `admin.py`, registrar el modelo para gestionarlo desde el panel administrativo».

El **panel de administración** de Django (`/admin/`) permite crear, ver, editar y borrar registros sin programar pantallas. Un modelo solo aparece allí si se registra en `productos/admin.py`:

```python
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoForm                                   # usa nuestras validaciones
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'creado')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'descripcion')
```

Se registraron los **tres** modelos (`Categoria`, `Producto`, `Mensaje`), cada uno con:

- `list_display`: qué columnas se muestran en la lista.
- `search_fields`: activa el cuadro de búsqueda.
- `list_filter`: filtros laterales (en productos, por categoría).
- `form = ...`: hace que el admin use **los mismos formularios validados** del proyecto (ver paso 5). Sin esto, el admin usaría un formulario automático y permitiría guardar datos inválidos.

Para entrar al panel se necesita un **superusuario**:

```powershell
python manage.py createsuperuser
```

Luego se ingresa en <http://127.0.0.1:8000/admin/>.

---

### Paso 5 — Operaciones CRUD (formularios, vistas, rutas y plantillas)

**Guía:** «Implementar vistas para listar, crear, editar y eliminar productos. Las vistas deben usar formularios de Django (`ModelForm`). Agregar las rutas correspondientes en `urls.py`».

**CRUD** son las cuatro operaciones básicas sobre datos: **C**reate (crear), **R**ead (leer/listar), **U**pdate (actualizar) y **D**elete (eliminar).

El flujo completo de una petición es:

```
Navegador ──► urls.py (¿qué vista atiende esta dirección?)
          ──► views.py (lógica: usa el formulario y la base de datos)
          ──► forms.py (valida los datos)  /  models.py (guarda en MySQL)
          ──► templates/ (arma el HTML de respuesta)
```

#### 5.1 Formularios — `productos/forms.py`

Un **`ModelForm`** es un formulario que Django construye automáticamente a partir de un modelo. Se definió uno por cada modelo:

- `ProductoForm` → crear y editar productos.
- `CategoriaForm` → categorías (se usa en el panel `/admin/`).
- `MensajeForm` → formulario de contacto.

```python
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'categoria', 'imagen']
```

**Validaciones personalizadas — una por cada campo.** Django ya valida lo básico (tipo de dato, largo máximo, obligatorio). Para reglas propias se escribe un método `clean_<nombre_del_campo>()`:

1. Django valida el campo con sus reglas por defecto.
2. Si pasa, llama a `clean_<campo>()`.
3. Si algo está mal, se lanza `ValidationError('mensaje')`: el formulario **no se guarda** y el mensaje aparece junto al campo.
4. Si todo está bien, se devuelve el valor limpio.

Ejemplo real del proyecto:

```python
def clean_precio(self):
    precio = self.cleaned_data['precio']
    if precio <= 0:
        raise ValidationError('El precio debe ser mayor que cero.')
    if precio > PRECIO_MAXIMO:
        raise ValidationError(f'El precio no puede superar ${con_puntos(PRECIO_MAXIMO)}.')
    return precio
```

**Todas las validaciones del proyecto:**

| Formulario | Campo | Regla personalizada |
|---|---|---|
| `ProductoForm` | `nombre` | Mínimo 3 caracteres · solo letras, números, espacios, `.` `'` `-` · no repetido (sin distinguir mayúsculas) |
| | `descripcion` | Entre 10 y 500 caracteres |
| | `precio` | Mayor que cero y máximo $10.000.000 |
| | `stock` | No negativo y máximo 10.000 unidades |
| | `categoria` | Máximo 50 productos por categoría |
| | `imagen` | Solo JPG, PNG o WEBP · máximo 2 MB |
| `CategoriaForm` | `nombre` | Mínimo 3 caracteres · caracteres válidos |
| | `descripcion` | Opcional; si se escribe, entre 10 y 200 caracteres |
| `MensajeForm` | `nombre` | Mínimo 3 · solo letras (con tildes) separadas por espacio, guion o apóstrofe (expresión regular) |
| | `email` | Se guarda en minúsculas · no se aceptan correos temporales (ej.: mailinator.com) |
| | `asunto` | Mínimo 5 caracteres |
| | `mensaje` | Entre 20 y 1000 caracteres |

Al editar un producto, las validaciones que buscan «repetidos» excluyen al propio producto (`.exclude(pk=self.instance.pk)`); si no, un producto siempre chocaría consigo mismo.

#### 5.2 Vistas — `productos/views.py`

Una **vista** es una función que recibe la petición del navegador y devuelve una respuesta. Las vistas del CRUD:

| Operación | Vista | URL | Métodos |
|---|---|---|---|
| Read | `lista_productos` | `/productos/` | GET |
| Create | `crear_producto` | `/productos/nuevo/` | GET / POST |
| Update | `editar_producto` | `/productos/<id>/editar/` | GET / POST |
| Delete | `eliminar_producto` | `/productos/<id>/eliminar/` | GET / POST |

Además hay tres vistas **públicas**: `inicio`, `catalogo` (tarjetas de solo lectura, con filtro `?categoria=<id>`) y `contacto`.

**Eficiencia de las consultas:** en la lista y el catálogo se usa `Producto.objects.select_related('categoria')`. Cada producto muestra el nombre de su categoría; sin `select_related`, Django haría **una consulta SQL extra por producto** (con 500 productos, 500 consultas de más). Con él, MySQL entrega producto y categoría juntos en una sola consulta (un `JOIN`).

Las vistas con formulario siguen siempre el mismo patrón:

```python
@login_required
@permission_required('productos.add_producto', raise_exception=True)
def crear_producto(request):
    if request.method == 'POST':                       # el usuario envió el formulario
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():                            # ejecuta todas las validaciones
            form.save()                                # INSERT en MySQL
            messages.success(request, 'Producto creado correctamente.')
            return redirect('lista_productos')         # vuelve a la lista
    else:                                              # GET: primera visita
        form = ProductoForm()                          # formulario vacío
    return render(request, 'productos/formulario.html', {'form': form, 'titulo': 'Nuevo producto'})
```

Puntos clave:

- **GET vs POST:** GET = «muéstrame la página»; POST = «te envío datos».
- `request.FILES` trae la imagen subida; sin él, la foto no llegaría al formulario.
- **Redirigir después de guardar** (`redirect(...)`) evita que, al recargar la página, el navegador reenvíe el formulario y se duplique el registro.
- **Editar** usa `ProductoForm(..., instance=producto)`: el formulario actualiza ese registro en vez de crear uno nuevo. `get_object_or_404` muestra un error 404 si el producto no existe.
- **Eliminar** nunca borra con un simple enlace: primero muestra una página de confirmación (GET) y solo borra cuando el usuario confirma (POST).

#### 5.3 Rutas — `productos/urls.py` y `tienda_backend/urls.py`

Una **ruta** conecta una dirección web con una vista:

```python
# productos/urls.py
urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('contacto/', views.contacto, name='contacto'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
]
```

- `<int:pk>` captura un número de la URL (el id del producto) y se lo entrega a la vista.
- `name='...'` es un apodo: en las plantillas se escribe `{% url 'lista_productos' %}` en vez de la dirección fija.

El `urls.py` **principal** (`tienda_backend/urls.py`) delega: `/admin/` va al panel de Django y todo lo demás (`''`) va a `productos.urls` mediante `include()`.

#### 5.4 Plantillas — `templates/`

Las plantillas son archivos HTML con «huecos» dinámicos:

- `{{ variable }}` muestra un dato; `{% if %}` / `{% for %}` son condicionales y bucles.
- **Herencia:** `base.html` contiene lo que se repite (menú, mensajes, pie de página) y define bloques `{% block contenido %}`. Las demás plantillas usan `{% extends 'base.html' %}` y solo rellenan esos bloques.
- **Reutilización:** `_campos_formulario.html` dibuja los campos de cualquier formulario (con sus mensajes de error) y se inserta con `{% include %}` en el formulario de productos y en el de contacto.
- `{% csrf_token %}` es obligatorio en todo formulario POST: es una protección de seguridad de Django.
- El formulario de productos lleva `enctype="multipart/form-data"`, necesario para poder subir la imagen.
- Los comentarios en plantillas se escriben con `{# ... #}` o `{% comment %}`; **no** con `<!-- -->`, porque Django interpreta las etiquetas `{% %}` incluso dentro de un comentario HTML.

| Plantilla | Función |
|---|---|
| `lista.html` | Tabla de productos (imagen, nombre, categoría, precio, stock) con botones **Editar** y **Eliminar** |
| `formulario.html` | Crear/editar producto (la misma plantilla sirve para ambas cosas) |
| `confirmar_eliminar.html` | «¿Eliminar este producto?» con botón de confirmación |
| `catalogo.html` | Catálogo público: tarjetas con imagen, categoría, precio y «Disponible/Agotado», y filtro por categoría |
| `inicio.html` / `contacto.html` | Páginas públicas |
| `403.html` | «Acceso denegado» cuando falta un permiso (Django la usa automáticamente por su nombre) |

#### 5.5 Imágenes subidas

Al guardar un producto con foto, Django copia el archivo a `media/productos/` y en MySQL guarda solo su ruta. Para mostrarla en desarrollo, `tienda_backend/urls.py` agrega al final:

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

### Paso 6 — Seguridad y autenticación

**Guía:** «Configurar el sistema de autenticación para que solo usuarios autenticados puedan acceder a las vistas CRUD. Redirigir a `/admin/login/` si el usuario no ha iniciado sesión».

Se logra con **tres piezas**:

1. En `settings.py`: `LOGIN_URL = '/admin/login/'` (adónde enviar a quien no ha iniciado sesión) y `LOGIN_REDIRECT_URL = '/productos/'` (adónde ir tras iniciar sesión cuando no venía de una página protegida; sin él, Django iría a `/accounts/profile/`, que no existe).
2. En `views.py`: el decorador **`@login_required`** encima de cada vista del CRUD.
3. En `views.py`: el decorador **`@permission_required(..., raise_exception=True)`**, que exige además el permiso de Django correspondiente.

```python
@login_required
@permission_required('productos.view_producto', raise_exception=True)
def lista_productos(request):
    ...
```

Django crea automáticamente 4 permisos por modelo (`add_`, `change_`, `delete_`, `view_`), que se asignan a cada usuario desde `/admin/` → Usuarios. Sin `@permission_required`, cualquier usuario con acceso al admin podría borrar productos desde el CRUD aunque el propio panel se lo prohibiera. **El orden importa:** `@login_required` va primero, para que un visitante anónimo sea enviado al login y no reciba un error 403.

Flujo real:

```
Visitante sin sesión ── pide /productos/ ──► @login_required lo detecta
        ──► redirige a /admin/login/?next=/productos/
        ──► inicia sesión ──► vuelve automáticamente a /productos/
```

Detalles importantes:

- El `?next=/productos/` hace que, tras iniciar sesión, el usuario **regrese a la página que quería**.
- El formulario de `/admin/login/` **es el formulario de autenticación** del proyecto. Solo acepta usuarios con permiso de acceso al admin (`is_staff`), como el superusuario creado con `createsuperuser`. Un usuario normal recibe el mensaje de credenciales incorrectas.
- **Cerrar sesión** se hace con un botón que envía un POST a `/admin/logout/` (con `csrf_token`); después redirige a `/` (`LOGOUT_REDIRECT_URL`).
- El menú (`base.html`) usa `{% if user.is_authenticated %}` para mostrar «Hola, usuario / Cerrar sesión» o «Iniciar sesión».
- Las páginas **públicas** (`inicio`, `catalogo` y `contacto`) no llevan `@login_required`.
- Si un usuario con sesión iniciada no tiene el permiso, ve `templates/403.html` («Acceso denegado»).

---

### Paso 7 — Demostración en el laboratorio

**Guía:** «Debe hacer demostración del sistema conectado a una base de datos MySQL o PostgreSQL».

#### Antes de la demostración (checklist)

- [ ] El servidor MySQL está en ejecución.
- [ ] El entorno virtual está activado (`venv\Scripts\activate`).
- [ ] `python manage.py migrate` no muestra errores.
- [ ] Existe un superusuario para iniciar sesión.
- [ ] `python manage.py runserver` está corriendo.

#### Guion sugerido (en este orden)

| # | Qué hacer | Qué demuestra |
|---|---|---|
| 1 | Mostrar el bloque `DATABASES` de `settings.py` | **Conexión a MySQL** configurada |
| 2 | En MySQL: `SHOW TABLES;` | Las tablas creadas por Django existen en MySQL |
| 3 | Abrir `/catalogo/` **sin** iniciar sesión; probar el filtro por categoría | **Catálogo de productos** leído desde MySQL |
| 4 | Abrir `/contacto/`; enviar un mensaje con datos válidos | Formulario público que **guarda en MySQL** |
| 5 | Enviar el formulario de contacto con datos inválidos | **Validaciones personalizadas** por campo |
| 6 | Abrir `/productos/` **sin** iniciar sesión | Redirección a `/admin/login/` (**seguridad**) |
| 7 | Iniciar sesión | **Autenticación** y regreso automático a `/productos/` |
| 8 | **Crear** un producto con imagen | CRUD: Create |
| 9 | Intentar crear uno inválido (precio 0, nombre corto…) | Validaciones por campo |
| 10 | **Editar** el producto | CRUD: Update |
| 11 | **Eliminar** el producto (pantalla de confirmación) | CRUD: Delete |
| 12 | Abrir `/admin/`: mostrar Categorías, Productos y Mensajes | **Uso del administrador de Django** |
| 13 | En MySQL: `SELECT id, nombre, precio, stock FROM productos_producto;` | Los datos realmente están en MySQL |
| 14 | (Opcional) `python manage.py test` | 32 pruebas automáticas en verde |

Comandos para el paso 2 y el 13 (te pedirán la contraseña del usuario `tienda_user`):

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u tienda_user -p tienda_backend -e "SHOW TABLES;"
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u tienda_user -p tienda_backend -e "SELECT id, nombre, precio, stock FROM productos_producto;"
```

#### Plan B: si el laboratorio usa XAMPP

XAMPP incluye MySQL (en realidad MariaDB, que funciona igual con Django) con el usuario `root` **sin contraseña**.

1. Abre el panel de XAMPP y pulsa **Start** en *MySQL*.
2. Crea la base de datos: abre <http://localhost/phpmyadmin>, pestaña *SQL*, y ejecuta solo:
   `CREATE DATABASE tienda_backend CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
3. En `tienda_backend/settings.py` cambia únicamente estas dos líneas:
   ```python
   'USER': 'root',
   'PASSWORD': '',
   ```
4. Continúa con `pip install -r requirements.txt`, `python manage.py migrate`, `createsuperuser` y `runserver`.

Si el servidor MySQL del laboratorio usa otro puerto (por ejemplo 3307), cambia también `'PORT'`.

---

### Extra — Formulario de contacto

La tabla de criterios (criterio 2.1.1, nivel Destacado) menciona «formularios de autentificación **y contacto**», aunque el texto de la guía no lo detalla. Por eso se agregó:

| Pieza | Archivo | Descripción |
|---|---|---|
| Modelo `Mensaje` | `models.py` | Guarda nombre, email, asunto, mensaje y fecha de envío |
| `MensajeForm` | `forms.py` | `ModelForm` con validación personalizada en sus 4 campos |
| Vista `contacto` | `views.py` | **Pública** (sin `@login_required`); si el formulario es válido, guarda el mensaje y muestra «¡Gracias!» |
| Plantilla | `templates/productos/contacto.html` | Formulario con estilo Bootstrap |
| Admin | `admin.py` | Los mensajes recibidos se leen desde `/admin/` → Mensajes |

---

## 6. Verificación de la tabla de criterios (puntaje máximo)

Cada fila cita el texto del nivel **Destacado (20 puntos)** y dónde está la evidencia en el proyecto.

### 2.1.1 — Configura conexión a una base de datos según requerimientos

> *«Configura un sitio web en Django con conexión a una base de datos con MySQL, realiza un catálogo de productos, agrega formularios de autentificación y contacto según requerimientos.»*

| Exigencia | Evidencia |
|---|---|
| Sitio web en Django | Proyecto `tienda_backend` con la app `productos` (Django 4.2) |
| Conexión a MySQL | `settings.py` → `DATABASES` con `ENGINE = django.db.backends.mysql`. Comprobado: Django reporta motor `mysql`, versión 8.0.46, base `tienda_backend` |
| Catálogo de productos | Modelos `Categoria` + `Producto`; **catálogo público** (`/catalogo/`, `catalogo.html`) y pantalla de administración `lista.html` con imagen, nombre, categoría, precio y stock |
| Formulario de autenticación | Login de Django en `/admin/login/` (`LOGIN_URL`) |
| Formulario de contacto | `MensajeForm` + vista `contacto` + modelo `Mensaje` (se guarda en MySQL) |

**Resultado: 20 / 20**

### 2.1.2 — Utiliza el administrador de Django

> *«Utiliza el administrador de Django, y registra el modelo para gestionarlo desde el panel administrativo.»*

| Exigencia | Evidencia |
|---|---|
| Registra el modelo | `productos/admin.py`: `@admin.register` para `Categoria`, `Producto` y `Mensaje` |
| Se gestiona desde el panel | En `/admin/` se pueden crear, listar, buscar, filtrar, editar y eliminar los tres modelos (comprobado) |
| Sin errores | Las páginas del admin responden correctamente y aplican las mismas validaciones del proyecto (`form = ...`) |

**Resultado: 20 / 20**

### 2.1.3 — Codifica funciones que realicen operaciones CRUD

> *«Implementa y codifica correctamente las funciones CRUD que permitan guardar, listar, actualizar y borrar datos, con formularios, vistas y rutas en Django.»*

| Operación | Formulario | Vista | Ruta |
|---|---|---|---|
| Guardar | `ProductoForm` | `crear_producto` | `/productos/nuevo/` |
| Listar | — | `lista_productos` | `/productos/` |
| Actualizar | `ProductoForm(instance=...)` | `editar_producto` | `/productos/<id>/editar/` |
| Borrar | Confirmación por POST | `eliminar_producto` | `/productos/<id>/eliminar/` |

Las vistas usan `ModelForm` (lo que exige la guía), y se comprobó el ciclo completo crear → listar → editar → eliminar contra MySQL, además del error 404 para productos inexistentes. La lista usa `select_related` (una sola consulta aunque haya cientos de productos) y el texto malicioso ingresado en un formulario se muestra escapado (no se ejecuta).

**Resultado: 20 / 20**

### 2.1.4 — Codifica una aplicación backend con acceso a base de datos y seguridad

> *«Utiliza validaciones personalizadas por cada campo de formulario y realiza autentificación de usuario.»*

| Exigencia | Evidencia |
|---|---|
| Validaciones personalizadas **por cada campo** | 12 métodos `clean_<campo>()` en `forms.py`: 6 en `ProductoForm`, 2 en `CategoriaForm` y 4 en `MensajeForm` (tabla completa en el [paso 5.1](#51-formularios--productosformspy)). También se aplican en el panel `/admin/` |
| Autenticación de usuario | `@login_required` en las 4 vistas del CRUD + `LOGIN_URL = '/admin/login/'` (redirección comprobada). Además, `@permission_required` exige el permiso de Django de cada operación (error 403 si falta) |
| Acceso a base de datos | Todo se guarda y consulta en MySQL mediante el ORM de Django |

**Resultado: 20 / 20**

### Puntaje total esperado: **80 / 80**

> La tabla anterior refleja lo que se **verificó técnicamente**. La nota final la asigna el docente en la demostración; para no perder puntos en el laboratorio, revisa el checklist del [paso 7](#paso-7--demostración-en-el-laboratorio) y confirma que MySQL esté encendido antes de comenzar.

---

## 7. Pruebas realizadas

El proyecto incluye **32 pruebas automáticas** en `productos/tests.py`. Una prueba automática usa la aplicación como lo haría un usuario (abre páginas, envía formularios, inicia sesión) y comprueba el resultado. Se ejecutan con:

```powershell
python manage.py test
```

Django crea una base MySQL **temporal** (`test_tienda_backend`), corre las pruebas y la elimina al terminar: los datos reales no se tocan. Todas pasaron. Además se comprobó que **las pruebas detectan errores de verdad**: al quitar a propósito `select_related` y los permisos, 8 pruebas fallaron; al restaurar el código, volvieron a pasar.

| Clase de pruebas | Qué se comprueba |
|---|---|
| `ModelosTests` | El motor es MySQL; `Producto` y `Categoria` están relacionados; una categoría con productos no se puede borrar |
| `AdminTests` | Los 3 modelos están registrados; sus páginas cargan; búsqueda y filtro; el admin rechaza datos inválidos y acepta los válidos; crear, editar y eliminar |
| `CrudProductoTests` | Crear (con imagen), listar, editar, eliminar con confirmación; error 404; sin consultas extra por producto; el texto malicioso se muestra escapado |
| `SeguridadTests` | Sin sesión el CRUD redirige a `/admin/login/?next=...`; login correcto e incorrecto; no se puede redirigir a sitios externos; un usuario sin `is_staff` no entra; cerrar sesión; un usuario sin permisos recibe 403; los permisos se aplican por separado |
| `ValidacionesProductoTests` | Cada regla de `ProductoForm` con valores inválidos (nombre, descripción, precio, stock, categoría llena o vacía, imagen con extensión incorrecta, pesada o que no es imagen) |
| `ContactoTests` | Es público, guarda en MySQL, normaliza el correo y valida cada campo |
| `CatalogoPublicoTests` | Visible sin sesión, con precio y disponibilidad; solo lectura; filtro por categoría (y filtro inválido ignorado); sin consultas extra por producto |

También se verificó visualmente la lista de productos, el catálogo público, el formulario con mensajes de error, la confirmación de borrado, la página 403 y la página de inicio, y se comprobó que el proyecto se reconstruye desde cero (entorno virtual nuevo con solo `pip install -r requirements.txt`, base vacía, `migrate` y `loaddata`).

---

## 8. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError: No module named 'django'` o `'MySQLdb'` | El entorno virtual no está activado | Ejecuta `venv\Scripts\activate` (el prompt debe mostrar `(venv)`) |
| `Unknown database 'tienda_backend'` | La base no existe todavía | Ejecuta `crear_base_datos.sql` (paso 2.1) |
| `Access denied for user 'tienda_user'` | Usuario o contraseña distintos entre MySQL y `settings.py` | Deben coincidir con los de `crear_base_datos.sql`; en XAMPP usa `root` y contraseña vacía |
| `Can't connect to MySQL server on '127.0.0.1'` | El servidor MySQL está apagado o usa otro puerto | Enciende el servicio (`Get-Service MySQL80` o el panel de XAMPP) y revisa `PORT` |
| La instalación de `mysqlclient` falla al compilar | Versión de Python sin «rueda» precompilada | Usa Python 3.12 (con el que se armó el proyecto) |
| `django.core.exceptions.ImproperlyConfigured: ... requires mysqlclient` | `mysqlclient` no está instalado en el entorno activo | `pip install mysqlclient` con el `venv` activado |
| Error de sintaxis al ejecutar el `.sql` con `<` en PowerShell | PowerShell no admite el operador `<` | Usa `-e "source archivo.sql"` como en el paso 2.1 |
| El comando `source crear_base_datos.sql` dice «Failed to open file» | La terminal no está en la carpeta del proyecto | Haz `cd` a `Programacion_Backend` primero |
| Al iniciar sesión en `/admin/login/` dice credenciales incorrectas | El usuario no tiene permiso de acceso al admin (`is_staff`) | Crea un superusuario con `python manage.py createsuperuser` |
| Aparece «Acceso denegado» (error 403) al entrar a `/productos/` | Iniciaste sesión con una cuenta sin el permiso del modelo | Usa el superusuario, o asigna permisos en `/admin/` → Usuarios (`view_`, `add_`, `change_`, `delete_` producto) |
| `python manage.py test` falla con `Access denied ... test_tienda_backend` | El usuario de MySQL no puede crear la base temporal de pruebas | Ejecuta `crear_base_datos.sql` (incluye ese permiso) o usa `root` en `settings.py` |
| Las imágenes no se ven | `DEBUG=False`, falta la ruta `static(MEDIA_URL...)` o el formulario sin `enctype="multipart/form-data"` | Revisa el paso 5.5 y `formulario.html` |
| La plantilla muestra un error extraño con un comentario `<!-- ... -->` | Django interpreta `{% %}` dentro de comentarios HTML | Usa `{# ... #}` o `{% comment %}` |
| `localhost` conecta a un servidor distinto del esperado | En Windows `localhost` puede resolverse por IPv6 | Usa siempre `127.0.0.1` en `HOST` |
| `pip install Django==4.2` da problemas con Python 3.14 | Django 4.2 no soporta Python 3.14 | Crea el entorno virtual con Python 3.12 (`py -3.12 -m venv venv`) |

---

## 9. Glosario

| Término | Significado |
|---|---|
| **Framework** | Conjunto de herramientas que ya resuelve lo repetitivo de una aplicación web. Django es un framework backend. |
| **Backend** | La parte «invisible» de una aplicación: lógica, base de datos y seguridad. |
| **ORM** | Permite trabajar con la base de datos usando clases de Python en lugar de escribir SQL. |
| **Modelo** | Clase de Python que representa una tabla. |
| **Migración** | Archivo que describe un cambio en las tablas; se aplica con `migrate`. |
| **Vista** | Función que atiende una petición y devuelve una respuesta. |
| **Plantilla (template)** | Archivo HTML con partes dinámicas. |
| **Ruta (URL)** | Asocia una dirección web con una vista. |
| **ModelForm** | Formulario generado a partir de un modelo. |
| **CRUD** | Create, Read, Update, Delete: crear, leer, actualizar y borrar. |
| **Decorador** | Línea con `@` que agrega comportamiento a una función (ej.: `@login_required`). |
| **Sesión** | Mecanismo que «recuerda» al usuario que ya inició sesión. |
| **CSRF** | Ataque en el que otro sitio envía formularios en nombre del usuario; `{% csrf_token %}` lo previene. |
| **Fixture** | Archivo con datos de ejemplo que se carga con `loaddata`. |
| **Entorno virtual (venv)** | Carpeta aislada con las librerías de un proyecto. |
| **Superusuario** | Usuario con todos los permisos, incluido el acceso a `/admin/`. |

---

## 10. Anexo: credenciales y comandos útiles

### Credenciales de desarrollo

> Son **solo para desarrollo local**. En un sitio real nunca se dejan contraseñas dentro de `settings.py`.

| Qué | Usuario | Contraseña |
|---|---|---|
| Usuario MySQL del proyecto | `tienda_user` | `TiendaDev2026` |
| Administrador de Django (creado para las pruebas) | `admin` | `AdminTienda2026` |

### Comandos útiles

| Comando | Para qué sirve |
|---|---|
| `python manage.py runserver` | Inicia el servidor de desarrollo en <http://127.0.0.1:8000/> |
| `python manage.py check` | Revisa que la configuración no tenga errores |
| `python manage.py test` | Ejecuta las 32 pruebas automáticas (base temporal) |
| `python manage.py makemigrations` | Genera migraciones tras cambiar `models.py` |
| `python manage.py migrate` | Aplica las migraciones a MySQL |
| `python manage.py sqlmigrate productos 0001` | Muestra el SQL de una migración |
| `python manage.py createsuperuser` | Crea un administrador |
| `python manage.py loaddata datos_iniciales` | Carga los productos de ejemplo |
| `python manage.py shell` | Consola interactiva para probar el ORM |
| `pip freeze` | Lista las librerías instaladas |

Ejemplos del ORM en `python manage.py shell`:

```python
from productos.models import Categoria, Producto

Categoria.objects.count()                         # cuántas categorías hay
Producto.objects.filter(precio__lt=500)           # productos de menos de $500
Categoria.objects.get(nombre='Fijaciones').productos.all()   # productos de una categoría
```

---

## 11. Recomendaciones fuera del alcance de la guía y riesgos del laboratorio

Esta sección reúne lo que **no** pide la guía (por eso no se implementó) pero convendría hacer en un proyecto real, y lo que puede fallar en el laboratorio. Se detectó al revisar el proyecto con pruebas específicas.

### 11.1 Mejoras posibles (no implementadas a propósito)

| Tema | Situación actual | Recomendación |
|---|---|---|
| **Validaciones solo en formularios** | Las reglas (`clean_<campo>`) viven en `forms.py`. Quien cree datos desde el shell o un script (ORM) puede saltárselas: se comprobó que así se puede guardar un producto duplicado con precio 0. | Repetir las reglas críticas en el modelo (`validators`, `UniqueConstraint` sobre el nombre) para que la protección llegue a la base de datos. |
| **Sin paginación** | La lista de administración muestra todos los productos. Con 500 productos, la página pesa ~420 KB. | Usar `Paginator` de Django (por ejemplo, 20 productos por página). |
| **Imágenes huérfanas** | Al borrar un producto (o reemplazar su foto), el archivo queda en `media/`. | Borrar el archivo con una señal `post_delete` o con la librería `django-cleanup`. |
| **Sin límite de intentos de login** | Se pueden probar contraseñas sin bloqueo (15 intentos fallidos y luego el correcto entró sin problema). | Instalar `django-axes`. |
| **Formulario de contacto sin antispam** | Se pueden enviar mensajes idénticos de forma repetida. | Un campo «trampa» (honeypot), un captcha o un límite por IP. |
| **Credenciales en `settings.py`** | Contraseña de MySQL y `SECRET_KEY` escritas en el archivo. | Leerlas desde variables de entorno (o un archivo `.env` que no se suba a Git). |
| **Configuración de desarrollo** | `DEBUG=True` y `ALLOWED_HOSTS` vacío. El comando `python manage.py check --deploy` lista 7 avisos. | Para publicar el sitio: `DEBUG=False`, `ALLOWED_HOSTS`, HTTPS y cookies seguras. |
| **Versión de Django** | La guía exige Django 4.2, cuyo soporte de seguridad **terminó el 7 de abril de 2026** (fuente: djangoproject.com/download). | Para un proyecto real, usar Django 5.2 LTS. Para esta guía, mantener 4.2. |
| **Mensajes creados a mano en el admin** | El panel permite «agregar» un mensaje de contacto, aunque estos deberían llegar solo desde el formulario público. | `has_add_permission` que devuelva `False` en `MensajeAdmin`. |

### 11.2 Riesgos para el laboratorio (revísalos antes de la demostración)

| Riesgo | Por qué importa | Qué hacer |
|---|---|---|
| **Versión de MariaDB de XAMPP** | Django 4.2 exige **MySQL 8 o superior** y **MariaDB 10.4 o superior** (documentación oficial). Un XAMPP antiguo no funcionará. | Antes de empezar, en phpMyAdmin o en la consola de MySQL, ejecuta `SELECT VERSION();` |
| **Versión de Python del laboratorio** | Django 4.2 funciona hasta Python 3.12. Con Python 3.13 o 3.14 puede fallar. | Usa `py -3.12` (o 3.10/3.11) para crear el entorno virtual. |
| **Sin internet** | `pip install` necesita descargar Django, mysqlclient y Pillow. | En tu equipo: `pip download -r requirements.txt -d wheels`. En el laboratorio: `pip install --no-index --find-links wheels -r requirements.txt` (deben coincidir sistema operativo y versión de Python). |
| **El entorno virtual no es portable** | La carpeta `venv/` no funciona al copiarla a otro computador. | Copia el proyecto **sin** `venv/` y créalo de nuevo en el laboratorio. |
| **Puerto o credenciales distintos** | El MySQL del laboratorio puede usar otro puerto, usuario o contraseña. | Cambia `PORT`, `USER` y `PASSWORD` en `settings.py` (ver «Plan B» del paso 7). |
| **Pantalla del laboratorio** | Si la demostración incluye subir una imagen, necesitas un archivo JPG, PNG o WEBP de menos de 2 MB a mano. | Deja una imagen de prueba en el escritorio. |

### 11.3 Alcance de la verificación

Todas las pruebas se ejecutaron contra **MySQL 8.0.46 con Python 3.12 en Windows**. **No** se probó con MariaDB/XAMPP, con otra versión de Python ni en varios navegadores. Las pantallas que exigen sesión se revisaron visualmente con HTML generado por código, no iniciando sesión en un navegador real.
