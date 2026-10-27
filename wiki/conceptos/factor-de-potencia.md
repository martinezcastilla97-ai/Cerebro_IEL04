---
tipo: concepto
etiquetas:
- circuitos-electricos
- IEL04
fecha_creacion: '2026-09-28'
fecha_actualizacion: '2026-09-28'
fuentes_count: 2
---

# Factor de potencia

**Definición:** Cociente entre la potencia real P y la potencia aparente S de una carga de ca, FP = P/S = cos θ, donde θ es el ángulo de su impedancia.

## Explicación
En ca la potencia se descompone en real P (W, la que se disipa), reactiva Q (VAR, la que intercambian inductores y capacitores) y aparente S = V·I (VA), relacionadas por el triángulo de potencia S² = P² + Q². Un FP cercano a 1 significa que casi toda la corriente produce trabajo útil; un FP bajo exige más corriente para la misma potencia. Como la mayoría de las cargas son inductivas (FP en atraso), el FP se corrige conectando un capacitor en paralelo que aporte potencia reactiva capacitiva: Q_C = P(tan θ₁ − tan θ₂).

## Cómo aparece en mis fuentes
- [[floyd-principios-circuitos-electricos]]: potencia en circuitos RC (§15–8) y RL (§16–7), con la corrección del factor de potencia.
- [[boylestad-introduccion-analisis-circuitos]]: potencia promedio y factor de potencia (§14.5), triángulo de potencia (§19.6), corrección del factor de potencia (§19.8) y medidores (§19.9).

## Tensiones o matices
[[deorsola-morcelle-circuitos-electricos-parte-1]] trata potencia y energía (§2.5) pero no el factor de potencia en ca. En IEL04 el tema aparece en los temarios de las semanas 9, 11 y 12, aunque el currículo no lo nombra.

## Ver también
[[circuitos-rl]] | [[circuitos-rlc]] | [[impedancia-y-admitancia]] | [[fasores]]
