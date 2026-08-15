"""
WSGI config for kb_project (Task 1).

Exposes the WSGI callable as a module-level variable named ``application``.
Referenced by ``settings.WSGI_APPLICATION`` and used by ``runserver`` and gunicorn.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kb_project.settings')

application = get_wsgi_application()
