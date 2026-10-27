---
tipo: vista_dataview
etiquetas: []
descripcion: Auditoría del texto del planeador contra el RA que le tocaba a cada semana, generada por CORRELATE-PLANEADOR. No editar los datos aquí -- correr CORRELATE-PLANEADOR para refrescar.
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---

# Matriz RA ↔ Planeador

Vacía a propósito — se llena sola en cuanto CORRELATE-PLANEADOR (`python src/correlate_planeador.py`) escriba los campos `planeador_*` en las páginas de `wiki/resultados-aprendizaje/`. Las tablas leen en vivo ese frontmatter; no hace falta tocar esta nota a mano.

## 🔴 Desviados

Los temas de las semanas de estos RA incluyen temas ajenos o dejan sin cubrir una parte importante del RA. `planeador_semanas_con_problema` dice qué semanas revisar.

```dataview
TABLE WITHOUT ID
    file.link AS "RA",
    pertenece_a AS "Asignatura",
    planeador_semanas_con_problema AS "Semanas a revisar",
    round(planeador_confianza, 2) AS "Confianza",
    planeador_justificacion AS "Justificación"
FROM "wiki/resultados-aprendizaje"
WHERE planeador_estado = "desviado"
SORT file.name ASC
```

## 🟡 Por revisar

Los temas cubren el RA solo en parte, o el juez no pudo decidirlo con lo que tenía.

```dataview
TABLE WITHOUT ID
    file.link AS "RA",
    pertenece_a AS "Asignatura",
    planeador_semanas_con_problema AS "Semanas a revisar",
    round(planeador_confianza, 2) AS "Confianza",
    planeador_justificacion AS "Justificación"
FROM "wiki/resultados-aprendizaje"
WHERE planeador_estado = "revisar"
SORT file.name ASC
```

## ✅ Cubiertos

```dataview
TABLE WITHOUT ID
    file.link AS "RA",
    pertenece_a AS "Asignatura",
    planeador_semanas AS "Semanas",
    round(planeador_confianza, 2) AS "Confianza"
FROM "wiki/resultados-aprendizaje"
WHERE planeador_estado = "cubierto"
SORT file.name ASC
```
