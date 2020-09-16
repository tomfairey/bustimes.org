# Generated by Django 3.1.1 on 2020-09-16 22:07

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('busstops', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('bounds', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='Livery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('colours', models.CharField(blank=True, max_length=255)),
                ('css', models.CharField(blank=True, max_length=255)),
                ('horizontal', models.BooleanField(default=False)),
                ('angle', models.PositiveSmallIntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'liveries',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=255)),
                ('fleet_number', models.PositiveIntegerField(blank=True, null=True)),
                ('fleet_code', models.CharField(blank=True, max_length=24)),
                ('reg', models.CharField(blank=True, max_length=24)),
                ('colours', models.CharField(blank=True, max_length=255)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('branding', models.CharField(blank=True, max_length=255)),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('withdrawn', models.BooleanField(default=False)),
                ('data', models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='VehicleEdit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fleet_number', models.CharField(blank=True, max_length=24)),
                ('reg', models.CharField(blank=True, max_length=24)),
                ('vehicle_type', models.CharField(blank=True, max_length=255)),
                ('colours', models.CharField(blank=True, max_length=255)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('branding', models.CharField(blank=True, max_length=255)),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('withdrawn', models.BooleanField(null=True)),
                ('changes', models.JSONField(blank=True, null=True)),
                ('url', models.URLField(blank=True, max_length=255)),
                ('approved', models.BooleanField(db_index=True, null=True)),
                ('datetime', models.DateTimeField(blank=True, null=True)),
                ('username', models.CharField(blank=True, max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='VehicleFeature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='VehicleJourney',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('route_name', models.CharField(blank=True, max_length=64)),
                ('code', models.CharField(blank=True, max_length=255)),
                ('destination', models.CharField(blank=True, max_length=255)),
                ('direction', models.CharField(blank=True, max_length=8)),
                ('data', models.JSONField(blank=True, null=True)),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='busstops.service')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.datasource')),
                ('vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='vehicles.vehicle')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='VehicleType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('double_decker', models.BooleanField(null=True)),
                ('coach', models.BooleanField(null=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='VehicleRevision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('changes', models.JSONField(blank=True, null=True)),
                ('message', models.TextField(blank=True)),
                ('username', models.CharField(blank=True, max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('from_operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='revision_from', to='busstops.operator')),
                ('to_operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='revision_to', to='busstops.operator')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vehicles.vehicle')),
            ],
        ),
        migrations.CreateModel(
            name='VehicleLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('latlong', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('heading', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('early', models.SmallIntegerField(blank=True, null=True)),
                ('delay', models.SmallIntegerField(blank=True, null=True)),
                ('current', models.BooleanField(default=False)),
                ('journey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vehicles.vehiclejourney')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='VehicleEditFeature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('add', models.BooleanField(default=True)),
                ('edit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vehicles.vehicleedit')),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vehicles.vehiclefeature')),
            ],
        ),
        migrations.AddField(
            model_name='vehicleedit',
            name='features',
            field=models.ManyToManyField(blank=True, through='vehicles.VehicleEditFeature', to='vehicles.VehicleFeature'),
        ),
        migrations.AddField(
            model_name='vehicleedit',
            name='livery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='vehicles.livery'),
        ),
        migrations.AddField(
            model_name='vehicleedit',
            name='vehicle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vehicles.vehicle'),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='features',
            field=models.ManyToManyField(blank=True, to='vehicles.VehicleFeature'),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='latest_location',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='latest_vehicle', to='vehicles.vehiclelocation'),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='livery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='vehicles.livery'),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='operator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='busstops.operator'),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='busstops.datasource'),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='vehicle_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='vehicles.vehicletype'),
        ),
        migrations.CreateModel(
            name='JourneyCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=64)),
                ('destination', models.CharField(blank=True, max_length=255)),
                ('data_source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='busstops.datasource')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='busstops.service')),
                ('siri_source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='busstops.sirisource')),
            ],
        ),
        migrations.CreateModel(
            name='Call',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visit_number', models.PositiveSmallIntegerField()),
                ('aimed_arrival_time', models.DateTimeField(null=True)),
                ('expected_arrival_time', models.DateTimeField(null=True)),
                ('aimed_departure_time', models.DateTimeField(null=True)),
                ('expected_departure_time', models.DateTimeField(null=True)),
                ('journey', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='vehicles.vehiclejourney')),
                ('stop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busstops.stoppoint')),
            ],
        ),
        migrations.AddIndex(
            model_name='vehiclelocation',
            index=models.Index(condition=models.Q(current=True), fields=['datetime'], name='datetime'),
        ),
        migrations.AddIndex(
            model_name='vehiclelocation',
            index=models.Index(condition=models.Q(current=True), fields=['datetime', 'latlong'], name='datetime_latlong'),
        ),
        migrations.AlterUniqueTogether(
            name='vehiclejourney',
            unique_together={('vehicle', 'datetime')},
        ),
        migrations.AlterIndexTogether(
            name='vehiclejourney',
            index_together={('service', 'datetime')},
        ),
        migrations.AlterUniqueTogether(
            name='vehicle',
            unique_together={('code', 'operator')},
        ),
        migrations.AlterUniqueTogether(
            name='journeycode',
            unique_together={('code', 'service', 'siri_source'), ('code', 'service', 'data_source')},
        ),
        migrations.AlterUniqueTogether(
            name='call',
            unique_together={('journey', 'visit_number')},
        ),
        migrations.AlterIndexTogether(
            name='call',
            index_together={('stop', 'expected_departure_time')},
        ),
    ]
