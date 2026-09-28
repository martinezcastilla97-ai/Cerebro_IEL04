---
tipo: vista_dataview
etiquetas: []
descripcion: Auditoría de cobertura bibliográfica de cada temario, generada por CORRELATE-BIBLIOGRAFIA. No editar los datos aquí -- correr CORRELATE-BIBLIOGRAFIA para refrescar.
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---

# Matriz Temario ↔ Bibliografía

Vacía a propósito — se llena sola en cuanto CORRELATE-BIBLIOGRAFIA (`python src/correlate_bibliografia.py`) escriba los campos `bibliografia_*` en las páginas de `generacion/temarios/`. Las tablas leen en vivo ese frontmatter; no hace falta tocar esta nota a mano.

## 🔴 Vacío detectado

Temarios que citan una fuente que no está cargada en `raw/` (marcador `[FUENTE NO CARGADA EN raw/]`, o juicio de respaldo). Es la cola accionable: probablemente falta cargar un libro o una norma. `bibliografia_faltantes` trae las líneas marcadas.

```dataview
TABLE WITHOUT ID
    file.link AS "Temario",
    asignatura AS "Asignatura",
    resultado_aprendizaje AS "RA",
    semana AS "Semana",
    bibliografia_faltantes AS "Fuentes que faltan"
FROM "generacion/temarios"
WHERE bibliografia_estado = "vacio_detectado"
SORT asignatura ASC, semana ASC
```

## 🟡 Por revisar

Sin marcador, pero el juez de respaldo no pudo confirmar que las fuentes cargadas sostengan lo escrito — o el RA no tiene fuentes cargadas (`bibliografia_via: sin_bibliografia`).

```dataview
TABLE WITHOUT ID
    file.link AS "Temario",
    asignatura AS "Asignatura",
    resultado_aprendizaje AS "RA",
    semana AS "Semana",
    bibliografia_via AS "Vía",
    bibliografia_justificacion AS "Justificación"
FROM "generacion/temarios"
WHERE bibliografia_estado = "revisar"
SORT asignatura ASC, semana ASC
```

## ✅ Cubiertas

```dataview
TABLE WITHOUT ID
    file.link AS "Temario",
    asignatura AS "Asignatura",
    resultado_aprendizaje AS "RA",
    semana AS "Semana"
FROM "generacion/temarios"
WHERE bibliografia_estado = "cubierta"
SORT asignatura ASC, semana ASC
```
