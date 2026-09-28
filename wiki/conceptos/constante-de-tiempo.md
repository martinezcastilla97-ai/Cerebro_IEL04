---
tipo: concepto
etiquetas:
- circuitos-electricos
- IEL04
fecha_creacion: '2026-09-28'
fecha_actualizacion: '2026-09-28'
fuentes_count: 3
---

# Constante de tiempo

**Definición:** Tiempo característico τ de la respuesta transitoria de un circuito de primer orden: τ = RC con un capacitor y τ = L/R con un inductor.

## Explicación
Al conmutar una fuente de cd, la tensión de un capacitor (o la corriente de un inductor) evoluciona de forma exponencial hacia su valor final: en un tiempo τ recorre el 63.2 % del cambio, y tras 5τ se considera en régimen permanente (más del 99 %). En la carga, v_C(t) = V_F(1 − e^(−t/τ)); en la descarga, v_C(t) = V_i e^(−t/τ). Con una onda cuadrada de semiperiodo mayor que 5τ se observan en el osciloscopio la carga y la descarga completas, lo que permite medir τ y, de ella, C o L.

## Cómo aparece en mis fuentes
- [[floyd-principios-circuitos-electricos]]: capacitores en circuitos de cd (§12–5) e inductores en circuitos de cd (§13–4).
- [[boylestad-introduccion-analisis-circuitos]]: transitorios en redes capacitivas (cap. 10) y transitorios R-L (§12.7).
- [[deorsola-morcelle-circuitos-electricos-parte-1]]: régimen transitorio del circuito RL (§6.2) y de su dual GC (§6.3), donde τ se define para ambos.

## Tensiones o matices
En el GC de Deorsola la constante se escribe C/G, que es el mismo RC con G = 1/R. Con una bobina real, la resistencia de devanado se suma a R en τ = L/R.

## Ver también
[[capacitancia]] | [[inductancia]] | [[circuitos-rc]] | [[circuitos-rl]]
