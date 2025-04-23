# Assistant App

Una aplicación web Python que sirve como interfaz entre un asistente de IA y tu iPhone. Esta aplicación te permite:

- Almacenar conversaciones con el asistente de IA
- Gestionar listas de tareas
- Integrar con calendario y recordatorios
- Iniciar sesión con cuentas de Google o Apple (iCloud)

## Instrucciones de configuración

### Requisitos previos

- Python 3.7 o superior
- pip (gestor de paquetes de Python)
- Un servidor web para despliegue (opcional)

### Configuración de desarrollo local

1. Clona este repositorio:

git clone https://github.com/omarblumen/manusinterface
cd manusinterface

2. Instala las dependencias:
pip install -r requirements.txt

3. Configura las variables de entorno:
- Copia el archivo `.env.example` a `.env`
- Edita el archivo `.env` para añadir tus credenciales OAuth para Google y Apple

4. Inicializa la base de datos:
flask shell
from app import db
db.create_all()
exit()

5. Ejecuta la aplicación:
python app.py

6. Accede a la aplicación en `http://localhost:5000`

## Opciones de despliegue

### Opción 1: Desplegar en un servicio de hosting web

1. Elige un servicio de hosting compatible con Python como Heroku, PythonAnywhere o AWS.
2. Sigue las instrucciones del servicio de hosting para desplegar una aplicación Flask.
3. Configura las variables de entorno para tu entorno de producción.
4. Configura una base de datos de producción si es necesario.

### Opción 2: Desplegar en tu propio servidor

1. Configura un servidor con Python instalado.
2. Instala un servidor WSGI de producción como Gunicorn:
pip install gunicorn
3. Ejecuta la aplicación con Gunicorn:
gunicorn -w 4 -b 0.0.0.0:8000 app:app
4. Configura un proxy inverso con Nginx o Apache para reenviar las solicitudes a Gunicorn.

## Acceso desde tu iPhone

Una vez desplegada, puedes acceder a la aplicación desde tu iPhone:

1. Abre Safari o tu navegador preferido
2. Navega a la URL de tu aplicación
3. Añade el sitio web a tu pantalla de inicio para un acceso fácil:
- Toca el icono de compartir
- Selecciona "Añadir a pantalla de inicio"
- La aplicación aparecerá como un icono en tu pantalla de inicio

## Configuración de OAuth

Para habilitar el inicio de sesión con Google y Apple:

1. Crea un ID de cliente OAuth de Google desde la [Consola de Desarrolladores de Google](https://console.developers.google.com/) 
2. Crea un ID de aplicación de Apple y configura "Iniciar sesión con Apple" desde el [Portal de Desarrolladores de Apple](https://developer.apple.com/) 
3. Añade estas credenciales a tu archivo `.env`

## Sincronización con Calendario y Recordatorios del iPhone

La funcionalidad de sincronización está actualmente simulada. Para implementar la sincronización real:

1. Para la integración con Calendario, necesitarías usar la API CalDAV de Apple o la API de Google Calendar
2. Para la integración con Recordatorios, necesitarías usar la API de Recordatorios de Apple

Estas implementaciones requerirían desarrollo adicional y autenticación adecuada con los servicios respectivos.
