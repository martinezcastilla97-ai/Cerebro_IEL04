---
tipo: concepto
etiquetas:
- circuitos-electricos
- IEL04
fecha_creacion: '2026-09-28'
fecha_actualizacion: '2026-09-28'
fuentes_count: 3
---

# Fasores

**Definición:** Número complejo que representa la amplitud (o el valor eficaz) y el ángulo de fase de una magnitud sinusoidal de frecuencia conocida.

## Explicación
Una tensión v(t) = V_p sen(ωt + θ) se representa con el fasor **V** = V∠θ, un vector que gira a la velocidad angular ω y cuya proyección da el valor instantáneo. Con fasores, las derivadas e integrales del régimen sinusoidal se vuelven multiplicaciones por jω, de modo que un circuito de ca se resuelve con álgebra compleja (formas rectangular y polar) igual que uno de cd: ley de Ohm con [[impedancia-y-admitancia|impedancias]] y [[leyes-de-kirchhoff]] con suma vectorial. El diagrama fasorial muestra de un vistazo los desfases entre tensiones y corrientes.

## Cómo aparece en mis fuentes
- [[floyd-principios-circuitos-electricos]]: introducción a los fasores (§11–6) y el sistema de números complejos (§15–1), aplicados en los caps. 15 a 17.
- [[boylestad-introduccion-analisis-circuitos]]: números complejos, conversión entre formas (§14.9) y fasores (§14.12).
- [[deorsola-morcelle-circuitos-electricos-parte-1]]: §4.3 — el fasor como herramienta del régimen senoidal permanente.

## Tensiones o matices
La magnitud del fasor puede tomarse como valor pico o como valor eficaz: hay que fijar la convención antes de comparar resultados numéricos o de leerlos contra un multímetro, que mide valores eficaces. Los fasores solo valen en régimen sinusoidal permanente a una única frecuencia; el transitorio se analiza aparte (ver [[constante-de-tiempo]]).

## Ver también
[[impedancia-y-admitancia]] | [[reactancia]] | [[leyes-de-kirchhoff]] | [[factor-de-potencia]]
