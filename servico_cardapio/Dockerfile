FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY infraestrutura/django_app/ .

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=cardapio_config.settings

RUN python manage.py collectstatic --noinput

EXPOSE 8002

CMD ["sh", "-c", "python manage.py migrate && python manage.py loaddata produtos/fixtures/produtos_cardapio.json || true && gunicorn cardapio_config.wsgi:application --bind 0.0.0.0:8002 --workers 2"]
