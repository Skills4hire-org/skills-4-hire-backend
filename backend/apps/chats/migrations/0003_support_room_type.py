from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='room_type',
            field=models.CharField(
                choices=[('direct', 'Direct'), ('support', 'Support')],
                default='direct',
                db_index=True,
                max_length=20,
                help_text='Type of conversation room'
            ),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['room_type'], name='conversation_room_type_idx'),
        ),
    ]
