FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY infraestrutura/django_app/ .

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=lanchonete.settings

RUN python manage.py collectstatic --noinput

EXPOSE 8001

CMD ["sh", "-c", "python manage.py migrate && gunicorn lanchonete.wsgi:application --bind 0.0.0.0:8001 --workers 2"]