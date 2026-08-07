# Procedencia: patrones locales de crecimiento Kogui/Arhuaco

**Fuente:** `patrones_locales_kogui_arhuaco.pdf` — "Patrones Locales de Crecimiento,
Etnias Kogui y Arhuaca, Sierra Nevada de Santa Marta (vertientes norte y
occidental)". Camilo Arbeláez Albornoz M.D. M.S.P., Fernando Arbeláez
Escalante. Gonawindúa Institución Pública de Salud Indígena. Documento
suministrado directamente por el usuario del proyecto el 2026-08-07.

**Muestra:** 13,835 valoraciones antropométricas a 5,899 niños y niñas
menores de 5 años (Arhuaco: 4,260 valoraciones, M 2,105 / F 2,155; Kogui:
9,575 valoraciones, M 5,831 / F 3,744), recolectadas 2015-2023 por el
Sistema Automatizado de Salud Indígena (SAISI). Depuradas por rango
intercuartílico (IQR) y desviación absoluta mediana (MAD).

**Hallazgo central del estudio:** Talla-para-edad y Peso-para-edad de
niños Kogui/Arhuaco están sistemáticamente desplazados por debajo de la
mediana OMS (p<0.0001), pero IMC, Peso-para-talla y Perímetro Braquial son
comparables (o superiores) a la referencia OMS — es decir, la masa
corporal relativa de estos niños es normal pese a su menor talla/peso
absolutos. El estudio concluye que aplicar T/E y P/E de forma aislada
sobre-diagnostica desnutrición crónica/global en esta población (sesgo
epidemiológico documentado), y que IMC/P-T/PB tienen mejor valor
predictivo positivo para esta población específica.

## Qué datos se usaron en `local_patterns.py` y cuáles NO

El documento es un informe narrativo con estadísticas agregadas y
gráficas — **no incluye tablas LMS mes a mes** como las oficiales de la
OMS (`apps/who_standards/data/*.csv`, descargadas de who.int con
trazabilidad exacta). Por eso el ajuste comunitario implementado aquí es
una **aproximación estadística**, no una curva de referencia con el mismo
rigor que la OMS:

- **Talla-para-edad**: se usó el "desfase promedio" narrado en el texto
  (talla observada − talla media OMS) por etnia×sexo: Arhuaco F −7.18cm,
  Arhuaco M −7.62cm, Kogui F −10.77cm, Kogui M −11.10cm. Es un promedio
  general 0-60 meses; el propio documento describe (en texto y gráficas
  de "brecha") que este desfase es ~0 al nacer y se estabiliza en ese
  valor recién hacia los 18-24 meses. `local_patterns.py` aplica una
  rampa lineal de 0 a ese desfase entre 0 y 24 meses (decisión de
  implementación nuestra, no un dato tabulado por el estudio -- ver
  comentario en el código). La desviación estándar usada
  (8.60cm) es la "DE de la diferencia" GLOBAL reportada en el resumen
  final del estudio (no está desagregada por etnia/sexo en el documento).
- **Peso-para-edad**: se usó la tabla con diferencia promedio y DE por
  etnia×sexo (la más precisa del documento): Arhuaco F −1.11kg (DE 0.91),
  Arhuaco M −1.24kg (DE 0.79), Kogui F −2.39kg (DE 1.11), Kogui M −2.55kg
  (DE 1.02). Mismo supuesto de rampa lineal 0-24 meses aplicado por
  consistencia (el documento no lo tabula así explícitamente para peso,
  pero sus gráficas de "brecha de peso" muestran una forma similar).
- **IMC, Peso-para-talla, Perímetro Braquial**: el estudio concluye que
  estos SON comparables a la OMS para esta población -- por eso
  `local_patterns.py` NO calcula un ajuste separado para ellos; se usa
  únicamente el z-score OMS estándar, y el reporte cita esta conclusión
  explícitamente.
- **Perímetro cefálico**: no evaluado por el estudio -- sin ajuste.

**Esto NO reemplaza un estudio con datos crudos por mes de edad.** Antes
de usar el ajuste comunitario para decisiones clínicas reales, sería
deseable obtener del equipo de Gonawindúa las tablas LMS o los datos
crudos subyacentes para construir una curva con el mismo rigor que la de
la OMS.
