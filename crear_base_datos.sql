-- ============================================================================
-- crear_base_datos.sql
-- Prepara MySQL para el proyecto tienda_backend (GUÍA PASO 2: configurar la
-- base de datos). Se ejecuta UNA SOLA VEZ, con un usuario administrador de
-- MySQL (root), ANTES de correr "python manage.py migrate".
--
-- Este script SOLO crea la base de datos vacía y el usuario del proyecto.
-- Las TABLAS las crea Django después, con los comandos makemigrations/migrate.
-- ============================================================================

-- 1) Base de datos del proyecto.
--    utf8mb4 permite guardar tildes, ñ y emojis correctamente.
CREATE DATABASE IF NOT EXISTS tienda_backend
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 2) Usuario exclusivo del proyecto (así Django no necesita usar "root").
--    Su nombre y contraseña deben coincidir con DATABASES en settings.py.
CREATE USER IF NOT EXISTS 'tienda_user'@'localhost' IDENTIFIED BY 'TiendaDev2026';

-- 3) Permisos: control total, pero SOLO sobre la base tienda_backend.
GRANT ALL PRIVILEGES ON tienda_backend.* TO 'tienda_user'@'localhost';

-- 4) (Solo para pruebas automáticas) Django crea una base temporal llamada
--    test_tienda_backend cuando se ejecuta "python manage.py test".
GRANT ALL PRIVILEGES ON `test\_tienda_backend`.* TO 'tienda_user'@'localhost';

FLUSH PRIVILEGES;
