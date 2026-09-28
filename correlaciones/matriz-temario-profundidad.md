---
tipo: vista_dataview
etiquetas: []
descripcion: Profundidad de los temarios — cuántas palabras, ecuaciones, tablas y figuras tiene cada sesión y cuántos pasajes de las fuentes cargadas se usaron para redactarla, según lo que escribe TEMARIO en `estadisticas`. No editar los datos aquí -- correr TEMARIO para refrescar.
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---

# Matriz Profundidad de los temarios

Vacía a propósito — se llena sola en cuanto TEMARIO (`python src/temario.py CODIGO --todas`) escriba el campo `estadisticas` en las páginas de `generacion/temarios/`. Las tablas leen en vivo ese frontmatter; no hace falta tocar esta nota a mano. Un temario sin `estadisticas` es de una versión anterior de TEMARIO: `--forzar` lo regenera con la estructura actual.

`palabras` cuenta la prosa (párrafos, listas, notas y pies); no cuenta el código, las ecuaciones ni las celdas de las tablas. `figuras` suma gráficas y diagramas. `pasajes` es cuántos pasajes de las fuentes cargadas (texto de `raw/` y páginas de `wiki/fuentes/`) se le entregaron al modelo: **0 significa que la sesión se redactó sin apoyo en la bibliografía** (el RA no tiene fuentes enlazadas, o de ellas solo hay un resumen que no coincide con el tema).

## Por asignatura

```dataview
TABLE WITHOUT ID
    asignatura AS "Asignatura",
    length(rows) AS "Temarios",
    round(sum(rows.estadisticas.palabras) / length(rows)) AS "Palabras (media)",
    sum(rows.estadisticas.ecuaciones) AS "Ecuaciones",
    sum(rows.estadisticas.tablas) AS "Tablas",
    sum(rows.estadisticas.figuras) AS "Figuras",
    sum(rows.estadisticas.pasajes) AS "Pasajes de fuentes"
FROM "generacion/temarios"
WHERE estadisticas
GROUP BY asignatura
SORT asignatura ASC
```

## 🟡 Sin apoyo en las fuentes

Sesiones redactadas sin ningún pasaje de las fuentes cargadas. Conviene revisar que el RA enlace sus fuentes en `bibliografia` y que estas tengan su original de texto en `raw/` (un PDF no se lee: convertirlo a Markdown).

```dataview
TABLE WITHOUT ID
    file.link AS "Temario",
    asignatura AS "Asignatura",
    semana AS "Semana",
    estadisticas.palabras AS "Palabras"
FROM "generacion/temarios"
WHERE estadisticas AND estadisticas.pasajes = 0
SORT asignatura ASC, semana ASC
```

## Todas las sesiones

```dataview
TABLE WITHOUT ID
    file.link AS "Temario",
    asignatura AS "Asignatura",
    semana AS "Semana",
    estadisticas.palabras AS "Palabras",
    estadisticas.ecuaciones AS "Ecuaciones",
    estadisticas.tablas AS "Tablas",
    estadisticas.figuras AS "Figuras",
    estadisticas.pasajes AS "Pasajes"
FROM "generacion/temarios"
WHERE estadisticas
SORT asignatura ASC, semana ASC
```
