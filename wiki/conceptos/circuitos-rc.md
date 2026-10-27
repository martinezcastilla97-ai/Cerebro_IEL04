---
tipo: concepto
etiquetas:
- circuitos-electricos
- IEL04
fecha_creacion: '2026-09-28'
fecha_actualizacion: '2026-09-28'
fuentes_count: 3
---

# Circuitos RC

**Definición:** Circuitos formados por resistores y capacitores, en serie, en paralelo o mixtos, analizados en régimen transitorio (τ = RC) y sinusoidal (impedancia).

## Explicación
Circuitos con resistores y capacitores. En serie, la impedancia es Z = R − jX_C y la corriente adelanta a la tensión; en paralelo, se trabaja con la admitancia. En cd, la respuesta transitoria es exponencial con τ = RC.

## Cómo aparece en mis fuentes
- [[floyd-principios-circuitos-electricos]]: cap. 15 — serie, paralelo, serie-paralelo, potencia y aplicaciones.
- [[boylestad-introduccion-analisis-circuitos]]: caps. 10 (transitorios) y 15 (ca en serie y en paralelo).
- [[deorsola-morcelle-circuitos-electricos-parte-1]]: §6.3 y §6.5 — régimen transitorio del circuito GC (capacitor con fuente de corriente real, dual del RL), también con alterna.

## Tensiones o matices
Deorsola no estudia el RC en serie con fuente de tensión: su circuito GC (§6.3) es un capacitor alimentado por una fuente de corriente real (conductancia G en paralelo con C), el dual del RL en serie. Su constante de tiempo, C/G, equivale a RC con G = 1/R, así que la forma exponencial de la respuesta es la misma, pero el circuito es otro.

## Ver también
[[IEL04-RA2]] | [[capacitancia]] | [[leyes-de-kirchhoff]] | [[impedancia-y-admitancia]] | [[constante-de-tiempo]]
