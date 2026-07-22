from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("callcenters", "0004_alter_callcenter_closed_audio_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="callcenter",
            name="schedule_version",
            field=models.PositiveBigIntegerField(default=1, editable=False),
        ),
    ]
