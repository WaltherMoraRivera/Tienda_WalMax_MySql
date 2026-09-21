"""
Configuración (settings) del proyecto tienda_backend.

Proyecto generado con 'django-admin startproject' usando Django 4.2.
Este archivo concentra TODA la configuración del proyecto: aplicaciones
instaladas, base de datos, plantillas, idioma, archivos subidos, etc.

Los comentarios marcados como "GUÍA PASO n" indican qué punto de la guía
"Programación Backend" se resuelve en cada bloque.

Documentación oficial:
  https://docs.djangoproject.com/en/4.2/topics/settings/
  https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

# Importamos las constantes de niveles de mensajes (success, error, etc.)
# para poder ajustar su color en Bootstrap (ver MESSAGE_TAGS más abajo).
from django.contrib.messages import constants as messages

# BASE_DIR es la carpeta raíz del proyecto (la que contiene manage.py).
# Desde aquí armamos rutas a otras carpetas: BASE_DIR / 'templates', etc.
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Seguridad básica (valores de desarrollo)
# ---------------------------------------------------------------------------
# ADVERTENCIA: en un sitio real la SECRET_KEY se mantiene en secreto y
# DEBUG se pone en False. Para esta guía (desarrollo local) se dejan así.
SECRET_KEY = 'django-insecure-q#uj$koadbq0h8p!suegux2sro+eljexjmj1nbe2_z0$%kyul6'

DEBUG = True

ALLOWED_HOSTS = []


# ---------------------------------------------------------------------------
# GUÍA PASO 2 (parte 2): registrar la aplicación en settings.py
# ---------------------------------------------------------------------------
# Django solo "ve" las aplicaciones que aparecen en INSTALLED_APPS.
# Aquí agregamos nuestra app 'productos' al final de la lista.
INSTALLED_APPS = [
    'django.contrib.admin',        # Panel de administración (/admin/)
    'django.contrib.auth',         # Sistema de usuarios, login y permisos
    'django.contrib.contenttypes',
    'django.contrib.sessions',     # Sesiones: recuerdan al usuario logueado
    'django.contrib.messages',     # Mensajes flash ("Producto creado", etc.)
    'django.contrib.staticfiles',
    'productos',                   # <-- NUESTRA APLICACIÓN (guía paso 1 y 2)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tienda_backend.urls'


# ---------------------------------------------------------------------------
# Plantillas (templates HTML)
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # DIRS: carpetas adicionales donde Django busca plantillas.
        # Usamos una carpeta 'templates' en la raíz del proyecto.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                # 'auth' deja disponible la variable {{ user }} en las plantillas.
                'django.contrib.auth.context_processors.auth',
                # 'messages' deja disponible {{ messages }} en las plantillas.
                'django.contrib.messages.context_processors.messages',
                # Propio: deja disponibles {{ carrito_cantidad }} y
                # {{ pedidos_pendientes }} en todas las plantillas (ver
                # productos/context_processors.py).
                'productos.context_processors.tienda',
            ],
        },
    },
]

WSGI_APPLICATION = 'tienda_backend.wsgi.application'


# ---------------------------------------------------------------------------
# GUÍA PASO 2 (parte 1): configurar la base de datos MySQL
# ---------------------------------------------------------------------------
# Por defecto Django usa SQLite. Aquí lo cambiamos por MySQL.
# Requisitos (ver DOCUMENTACION.md):
#   1. Tener un servidor MySQL en ejecución.
#   2. Haber creado la base de datos y el usuario (archivo crear_base_datos.sql).
#   3. Tener instalado el driver 'mysqlclient' (pip install mysqlclient).
DATABASES = {
    'default': {
        # ENGINE: le dice a Django qué "motor" de base de datos usar.
        'ENGINE': 'django.db.backends.mysql',
        # NAME: nombre de la base de datos (debe existir en MySQL).
        'NAME': 'tienda_backend',
        # USER / PASSWORD: credenciales del usuario MySQL creado para este proyecto.
        # (En el laboratorio suele usarse el usuario 'root' de XAMPP, con la
        #  contraseña vacía: en ese caso cambia estos dos valores.)
        'USER': 'tienda_user',
        'PASSWORD': 'TiendaDev2026',
        # HOST: dirección del servidor MySQL. Se usa '127.0.0.1' y NO 'localhost'
        # porque en Windows 'localhost' puede resolverse a IPv6 (::1) y llegar a
        # otro servidor distinto del que esperamos.
        'HOST': '127.0.0.1',
        # PORT: puerto de MySQL (3306 es el estándar).
        'PORT': '3306',
        'OPTIONS': {
            # utf8mb4 permite guardar tildes, ñ y emojis sin problemas.
            'charset': 'utf8mb4',
        },
    }
}


# ---------------------------------------------------------------------------
# Validación de contraseñas (usuarios de Django)
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ---------------------------------------------------------------------------
# Idioma y zona horaria
# ---------------------------------------------------------------------------
# 'es' traduce el admin y los mensajes de validación de Django al español.
LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# ---------------------------------------------------------------------------
# Archivos estáticos y archivos subidos (imágenes de productos)
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'

# STATICFILES_DIRS: carpeta del proyecto con archivos propios (logo, favicon).
# Django los sirve desde /static/ (ej.: /static/images/logo.png).
STATICFILES_DIRS = [BASE_DIR / 'static']

# MEDIA_ROOT: carpeta del disco donde se guardan las imágenes que suben los
# usuarios (campo ImageField de Producto). MEDIA_URL: dirección web desde la
# que se sirven. Se necesita la librería Pillow para trabajar con imágenes.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# GUÍA PASO 6: seguridad y autenticación
# ---------------------------------------------------------------------------
# LOGIN_URL: a dónde envía Django a un usuario que NO ha iniciado sesión y
# intenta entrar a una vista protegida con @login_required.
# La guía pide redirigir a /admin/login/ (el login del panel de Django).
# Ejemplo: /productos/ -> /admin/login/?next=/productos/
LOGIN_URL = '/admin/login/'

# LOGIN_REDIRECT_URL: adónde va el usuario tras iniciar sesión cuando NO viene
# de una página protegida (es decir, cuando no hay un "?next=..." válido).
# Sin este ajuste, Django usa por defecto /accounts/profile/, una dirección
# que no existe en este proyecto y mostraría un error 404.
LOGIN_REDIRECT_URL = '/productos/'

# LOGOUT_REDIRECT_URL: página a la que se vuelve después de cerrar sesión.
LOGOUT_REDIRECT_URL = '/'


# ---------------------------------------------------------------------------
# Mensajes (django.contrib.messages) con colores de Bootstrap
# ---------------------------------------------------------------------------
# Bootstrap usa la clase "alert-danger" (no "alert-error"), así que
# traducimos el nivel ERROR de Django a la etiqueta 'danger'.
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}
