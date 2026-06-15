from django.db import migrations
from django.contrib.auth.hashers import make_password


def criar_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            email='admin@lanchonete.com',
            password=make_password('admin1234'),
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0002_alter_itempedido_options_alter_pedido_options_and_more'),
    ]

    operations = [
        migrations.RunPython(criar_admin, migrations.RunPython.noop),
    ]