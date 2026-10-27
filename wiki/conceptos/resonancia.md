---
tipo: concepto
etiquetas:
- circuitos-electricos
- IEL04
fecha_creacion: '2026-09-28'
fecha_actualizacion: '2026-09-28'
fuentes_count: 2
---

# Resonancia

**Definición:** Condición de un circuito con inductancia y capacitancia en la que la reactancia inductiva iguala a la capacitiva (X_L = X_C), a la frecuencia f_r = 1/(2π√(LC)).

## Explicación
En la resonancia en serie las reactancias se cancelan: la impedancia es mínima (igual a R), la corriente es máxima y está en fase con la tensión, y las tensiones en L y en C pueden ser Q veces la tensión aplicada. En la resonancia en paralelo (circuito tanque) la impedancia es máxima y la corriente de línea mínima. El factor de calidad Q = X_L/R mide la selectividad, y el ancho de banda BW = f_r/Q es el intervalo entre las frecuencias de media potencia (donde la respuesta cae al 70.7 %). Con una bobina real de resistencia R_W, el tanque equivale a un paralelo con R_p(eq) = R_W(Q² + 1) y su resonancia se desplaza ligeramente. Los circuitos resonantes forman filtros pasabanda y rechazabanda.

## Cómo aparece en mis fuentes
- [[floyd-principios-circuitos-electricos]]: resonancia en serie (§17–3), resonancia en paralelo con tanque no ideal (§17–6), ancho de banda (§17–8), aplicaciones (§17–9) y filtros pasabanda y rechazabanda (§18–3, §18–4).
- [[boylestad-introduccion-analisis-circuitos]]: circuito resonante en serie (§20.2), factor de calidad (§20.3), selectividad (§20.5), circuito resonante en paralelo (§20.8) y filtros pasa-banda y rechaza-banda (§23.7, §23.8).

## Tensiones o matices
El currículo de IEL04 no nombra la resonancia; los temarios la desarrollan (semanas 3, 11, 12 y 13) porque las fuentes la tratan como parte del análisis LC y RLC. [[deorsola-morcelle-circuitos-electricos-parte-1]] estudia el RLC en régimen transitorio (§6.6) pero no la resonancia.

## Ver también
[[circuitos-rlc]] | [[reactancia]] | [[impedancia-y-admitancia]] | [[inductancia]] | [[capacitancia]]
