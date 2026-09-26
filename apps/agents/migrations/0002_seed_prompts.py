from django.db import migrations

# Siembra la tabla PromptSistema con el texto que YA estaba fijo en código
# (apps/agents/prompts.py, constantes _DEFAULT_PROMPT_SISTEMA_*) -- así el
# admin ve y puede editar desde /admin/ exactamente el prompt que el
# asistente venía usando, en vez de empezar con una fila vacía. Se
# importa el texto en vez de duplicarlo a mano para que no se desincronice
# si alguien edita el default en código antes de correr esta migración en
# un ambiente nuevo.


def sembrar(apps, schema_editor):
    from apps.agents.prompts import (
        _DEFAULT_PROMPT_SISTEMA_SINTESIS,
        _DEFAULT_PROMPT_SISTEMA_SINTESIS_FAMILIAR,
        _DEFAULT_PROMPT_SISTEMA_TIPS_NUTRICION,
    )

    PromptSistema = apps.get_model("agents", "PromptSistema")
    filas = [
        ("sintesis_clinica", _DEFAULT_PROMPT_SISTEMA_SINTESIS, 1),
        ("sintesis_familiar", _DEFAULT_PROMPT_SISTEMA_SINTESIS_FAMILIAR, 2),
        ("tips_nutricion", _DEFAULT_PROMPT_SISTEMA_TIPS_NUTRICION, 3),
    ]
    for clave, contenido, orden in filas:
        PromptSistema.objects.get_or_create(
            clave=clave,
            defaults={"contenido": contenido, "orden": orden, "activo": True},
        )


def deshacer(apps, schema_editor):
    PromptSistema = apps.get_model("agents", "PromptSistema")
    PromptSistema.objects.filter(
        clave__in=["sintesis_clinica", "sintesis_familiar", "tips_nutricion"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("agents", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sembrar, deshacer),
    ]
