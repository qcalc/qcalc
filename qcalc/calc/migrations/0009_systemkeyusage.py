from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calc', '0008_mycredential_suffix4'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemKeyUsage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=40)),
                ('scope', models.CharField(max_length=10)),
                ('subject', models.CharField(blank=True, default='', max_length=64)),
                ('period', models.CharField(max_length=10)),
                ('count', models.PositiveIntegerField(default=0)),
                ('changed_on', models.DateTimeField(auto_now=True)),
            ],
            options={
                'indexes': [models.Index(fields=['period'], name='calc_system_period_e10b70_idx')],
                'constraints': [
                    models.UniqueConstraint(
                        fields=('provider', 'scope', 'subject', 'period'), name='unique_system_key_usage'
                    )
                ],
            },
        ),
    ]
