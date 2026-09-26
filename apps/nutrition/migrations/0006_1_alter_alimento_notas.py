from django.db import migrations, models


class Migration(migrations.Migration):
    """Se inserta ANTES de 0007_reemplazos_culturales_kogui, que revienta al sembrar notas
    reales de más de 200 caracteres (hasta 455) contra el CharField(200) original -- entre
    ellas una advertencia de seguridad clínica sobre la chicha fermentada que no se debe
    truncar. Ver apps/nutrition/models.py::Alimento.notas."""

    dependencies = [
        ("nutrition", "0006_alimento_excluido_para_region"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alimento",
            name="notas",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Ej. 'picar en trozos pequeños para evitar atragantamiento'.",
            ),
        ),
    ]
