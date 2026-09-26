"""Genera un lote de evaluaciones de prueba (casos representativos, no
datos reales de pacientes) y sus reportes PDF -- técnico y familiar --
para revisar visualmente antes de un despliegue, sin tener que llamar la
API a mano ni escribir un paciente real en producción.

Uso:
    python manage.py generar_reportes_prueba
    python manage.py generar_reportes_prueba --salida /tmp/reportes --manteneR-datos

Cada corrida crea pacientes y evaluaciones NUEVOS (con documento_identidad
prefijado "PRUEBA-" para poder identificarlos y limpiarlos después) -- por
defecto los borra al terminar de copiar los PDFs a `--salida`; usar
--mantener-datos para dejarlos en la base de datos (útil si luego se
quiere ver el JSON en /api/v1/evaluaciones/<id>/ o el registro en /admin/).
"""

from __future__ import annotations

import shutil
from datetime import date, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.assessments.models import Evaluacion
from apps.assessments.services import ejecutar_evaluacion
from apps.patients.models import Paciente
from apps.reports.pdf import obtener_o_generar_pdf, obtener_o_generar_pdf_familiar

PREFIJO_PRUEBA = "PRUEBA-"

# Casos elegidos para cubrir los caminos relevantes del pipeline, no un
# muestreo aleatorio: crecimiento normal, una comunidad con plan
# nutricional propio (Kogui, ver apps/nutrition/plan.py), una etnia sin
# alimentos propios cargados aún (Arhuaco, para ver que el catálogo
# general solo se sigue ofreciendo igual), desnutrición aguda severa con
# alerta crítica, edema bilateral, y un lactante menor de 6 meses (donde
# el plan de alimentación complementaria no aplica).
CASOS = [
    {
        "clave": "normal_24m",
        "descripcion": "Niño de 24 meses, crecimiento dentro de lo esperado",
        "nombres": "Prueba", "apellidos": "CrecimientoNormal",
        "sexo": "M", "etnia": Paciente.Etnia.NINGUNA,
        "edad_meses": "24.0", "peso_kg": "12.2", "talla_cm": "87.0",
        "tipo_medicion_talla": Evaluacion.TipoMedicionTalla.DE_PIE,
        "perimetro_cefalico_cm": "48.0", "perimetro_braquial_cm": "16.0",
        "edema_bilateral": False,
    },
    {
        "clave": "kogui_30m",
        "descripcion": "Niña Kogui de 30 meses, crecimiento normal (plan nutricional Kogui)",
        "nombres": "Prueba", "apellidos": "PlanKogui",
        "sexo": "F", "etnia": Paciente.Etnia.KOGUI,
        "edad_meses": "30.0", "peso_kg": "12.8", "talla_cm": "90.0",
        "tipo_medicion_talla": Evaluacion.TipoMedicionTalla.DE_PIE,
        "perimetro_cefalico_cm": "48.5", "perimetro_braquial_cm": "16.2",
        "edema_bilateral": False,
    },
    {
        "clave": "arhuaco_18m",
        "descripcion": "Niño Arhuaco de 18 meses, riesgo moderado (T/E ligeramente bajo)",
        "nombres": "Prueba", "apellidos": "ComparacionArhuaco",
        "sexo": "M", "etnia": Paciente.Etnia.ARHUACO,
        "edad_meses": "18.0", "peso_kg": "9.5", "talla_cm": "77.0",
        "tipo_medicion_talla": Evaluacion.TipoMedicionTalla.DE_PIE,
        "perimetro_cefalico_cm": "46.5", "perimetro_braquial_cm": "14.8",
        "edema_bilateral": False,
    },
    {
        "clave": "desnutricion_severa_14m",
        "descripcion": "Niña de 14 meses, desnutrición aguda severa (alerta crítica)",
        "nombres": "Prueba", "apellidos": "AlertaCritica",
        "sexo": "F", "etnia": Paciente.Etnia.NINGUNA,
        "edad_meses": "14.0", "peso_kg": "6.3", "talla_cm": "68.0",
        "tipo_medicion_talla": Evaluacion.TipoMedicionTalla.DE_PIE,
        "perimetro_cefalico_cm": "44.0", "perimetro_braquial_cm": "10.8",
        "edema_bilateral": False,
    },
    {
        "clave": "edema_bilateral_20m",
        "descripcion": "Niño de 20 meses con edema bilateral (signo crítico independiente del peso/talla)",
        "nombres": "Prueba", "apellidos": "EdemaBilateral",
        "sexo": "M", "etnia": Paciente.Etnia.NINGUNA,
        "edad_meses": "20.0", "peso_kg": "10.5", "talla_cm": "82.0",
        "tipo_medicion_talla": Evaluacion.TipoMedicionTalla.DE_PIE,
        "perimetro_cefalico_cm": "47.0", "perimetro_braquial_cm": "13.5",
        "edema_bilateral": True,
    },
    {
        "clave": "lactante_4m",
        "descripcion": "Lactante de 4 meses (antes de los 6 meses -- no aplica plan de alimentación complementaria)",
        "nombres": "Prueba", "apellidos": "LactanteMenor",
        "sexo": "F", "etnia": Paciente.Etnia.NINGUNA,
        "edad_meses": "4.0", "peso_kg": "6.4", "talla_cm": "61.0",
        "tipo_medicion_talla": Evaluacion.TipoMedicionTalla.ACOSTADO,
        "perimetro_cefalico_cm": "40.5", "perimetro_braquial_cm": None,
        "edema_bilateral": False,
    },
]


class Command(BaseCommand):
    help = "Genera evaluaciones y reportes PDF de prueba para revisar antes de un despliegue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--salida",
            default="reportes_prueba",
            help="Carpeta donde copiar los PDF generados (default: ./reportes_prueba)",
        )
        parser.add_argument(
            "--mantener-datos",
            action="store_true",
            help="No borrar los pacientes/evaluaciones de prueba de la base de datos al terminar.",
        )
        parser.add_argument(
            "--caso",
            choices=[caso["clave"] for caso in CASOS],
            help="Generar solo este caso (por defecto genera los 6). Usar --listar-casos para ver las claves.",
        )
        parser.add_argument(
            "--listar-casos",
            action="store_true",
            help="Listar las claves de caso disponibles y salir, sin generar nada.",
        )

    def handle(self, *args, **options):
        if options["listar_casos"]:
            for caso in CASOS:
                self.stdout.write(f"{caso['clave']}: {caso['descripcion']}")
            return

        casos_a_generar = CASOS
        if options["caso"]:
            casos_a_generar = [c for c in CASOS if c["clave"] == options["caso"]]

        salida = Path(options["salida"]).resolve()
        salida.mkdir(parents=True, exist_ok=True)

        resumen = []
        for caso in casos_a_generar:
            self.stdout.write(f"Generando: {caso['clave']} -- {caso['descripcion']}")
            evaluacion = self._crear_evaluacion(caso)

            if evaluacion.estado != Evaluacion.Estado.COMPLETADA:
                self.stderr.write(
                    self.style.ERROR(
                        f"  ERROR en {caso['clave']}: {evaluacion.error_detalle}"
                    )
                )
                resumen.append((caso["clave"], None, None, evaluacion.error_detalle))
                continue

            pdf_tecnico = obtener_o_generar_pdf(evaluacion)
            pdf_familiar = obtener_o_generar_pdf_familiar(evaluacion)

            destino_tecnico = salida / f"{caso['clave']}__tecnico.pdf"
            destino_familiar = salida / f"{caso['clave']}__familiar.pdf"
            shutil.copyfile(pdf_tecnico.path, destino_tecnico)
            shutil.copyfile(pdf_familiar.path, destino_familiar)

            alerta = "SÍ" if evaluacion.alerta_critica else "No"
            self.stdout.write(f"  OK -- alerta_critica={alerta}")
            resumen.append((caso["clave"], destino_tecnico, destino_familiar, None))

        if not options["mantener_datos"]:
            self._limpiar_datos_prueba()
        else:
            self.stdout.write(self.style.WARNING("Datos de prueba conservados en la base de datos (--mantener-datos)."))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Listo. PDFs en: {salida}"))
        for clave, tecnico, familiar, error in resumen:
            if error:
                self.stdout.write(f"  - {clave}: FALLÓ ({error})")
            else:
                self.stdout.write(f"  - {clave}: {tecnico.name} / {familiar.name}")

    def _crear_evaluacion(self, caso: dict) -> Evaluacion:
        documento = f"{PREFIJO_PRUEBA}{caso['clave']}"
        # Evita acumular pacientes duplicados si el comando se corre varias
        # veces sin --mantener-datos entre corridas (o si una corrida previa
        # falló a mitad de camino). Evaluacion.paciente es PROTECT, así que
        # hay que borrar las evaluaciones de ese paciente antes que él.
        Evaluacion.objects.filter(paciente__documento_identidad=documento).delete()
        Paciente.objects.filter(documento_identidad=documento).delete()

        fecha_evaluacion = date.today()
        dias_aprox = round(float(caso["edad_meses"]) * 30.4375)
        datos = {
            "paciente": {
                "nombres": caso["nombres"],
                "apellidos": caso["apellidos"],
                "documento_identidad": documento,
                "fecha_nacimiento": fecha_evaluacion - timedelta(days=dias_aprox),
                "etnia": caso["etnia"],
            },
            "sexo": caso["sexo"],
            "fecha_evaluacion": fecha_evaluacion,
            "edad_meses": caso["edad_meses"],
            "peso_kg": caso["peso_kg"],
            "talla_cm": caso["talla_cm"],
            "tipo_medicion_talla": caso["tipo_medicion_talla"],
            "perimetro_cefalico_cm": caso["perimetro_cefalico_cm"],
            "perimetro_braquial_cm": caso["perimetro_braquial_cm"],
            "edema_bilateral": caso["edema_bilateral"],
        }
        return ejecutar_evaluacion(datos)

    def _limpiar_datos_prueba(self):
        pacientes = Paciente.objects.filter(documento_identidad__startswith=PREFIJO_PRUEBA)
        cantidad = pacientes.count()
        # Evaluacion.paciente es PROTECT -- hay que borrar las evaluaciones
        # (y con ellas, en cascada, resultados y reporte) antes que los
        # pacientes de prueba, o el delete de abajo falla.
        Evaluacion.objects.filter(paciente__in=pacientes).delete()
        pacientes.delete()
        self.stdout.write(f"Datos de prueba eliminados ({cantidad} paciente(s) de prueba).")
