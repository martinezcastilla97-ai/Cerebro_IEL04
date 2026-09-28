---
tipo: concepto
etiquetas:
- circuitos-electricos
- IEL04
fecha_creacion: '2026-09-28'
fecha_actualizacion: '2026-09-28'
fuentes_count: 3
---

# Impedancia y admitancia

**Definición:** La impedancia Z es la oposición total, en ohmios, que un circuito presenta a la corriente sinusoidal (resistencia más reactancia, como número complejo); la admitancia Y = 1/Z, en siemens, es su inverso.

## Explicación
En forma rectangular, Z = R ± jX: la parte real es la resistencia y la imaginaria la reactancia neta (positiva si domina la inductiva, negativa si domina la capacitiva). En forma polar, Z = |Z|∠θ, con |Z| = √(R² + X²) y θ = arctan(X/R), el ángulo de fase entre la tensión y la corriente. En serie las impedancias se suman; en paralelo conviene sumar admitancias: Y = G + jB, con la conductancia G = 1/R y la susceptancia B = 1/X (capacitiva positiva, inductiva negativa), y luego Z = 1/Y. La ley de Ohm se escribe con fasores: **V** = **I**Z.

## Cómo aparece en mis fuentes
- [[floyd-principios-circuitos-electricos]]: impedancia de los RC, RL y RLC en serie (§15–3, §16–2, §17–1) e impedancia y admitancia en paralelo (§15–5, §16–4, §17–4).
- [[boylestad-introduccion-analisis-circuitos]]: impedancia y diagrama fasorial (§15.2), admitancia y susceptancia (§15.7), redes de ca en paralelo (§15.8).
- [[deorsola-morcelle-circuitos-electricos-parte-1]]: §4.3 — la impedancia compleja como cociente de fasores, con la resistencia como parte real y la reactancia como parte imaginaria.

## Tensiones o matices
El signo de la susceptancia cambia entre textos (la capacitiva y la inductiva se escriben con signos opuestos, pero no todos incluyen el signo en B): al comparar resultados, revisar la convención de cada fuente. En serie conviene trabajar con Z y en paralelo con Y; un circuito mixto se reduce combinando ambas.

## Ver también
[[reactancia]] | [[fasores]] | [[circuitos-rc]] | [[circuitos-rl]] | [[circuitos-rlc]] | [[resonancia]]
