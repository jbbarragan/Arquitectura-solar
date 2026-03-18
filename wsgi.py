"""
WSGI entry point for gunicorn on AWS Linux.

Run with:
    gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 2 --timeout 120

Or use the start.sh script.
"""
from app import app as application
