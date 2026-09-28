---
tipo: vista_dataview
etiquetas: []
descripcion: Matriz RA <-> fuente de laboratorio, generada por CORRELATE. No editar los datos aquí -- correr CORRELATE para refrescar.
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---

# Matriz RA ↔ Práctica

Vacía a propósito — se llena sola en cuanto existan páginas en `wiki/resultados-aprendizaje/`. Generada por el protocolo **CORRELATE** (ver `CLAUDE.md`); las tablas leen en vivo el frontmatter de cada RA, no hace falta tocar esta nota a mano.

## 🟡 Pendientes de revisión

RA con una fuente candidata pero sin confianza suficiente para aceptarla sola (`correlacion_confianza` entre 0.35 y 0.70). Para resolverlo, cambia `correlacion_estado` a `aceptado` (si la práctica es correcta) o a `sin_candidato` (si no lo es) **y marca `correlacion_revisado_por_docente: true`** — sin esa marca, la próxima corrida de CORRELATE sobrescribe tu decisión.

```dataview
TABLE WITHOUT ID
    file.link AS "RA",
    requiere_practica AS "Fuente candidata",
    practica_experimentos AS "Experimento(s)",
    round(correlacion_score_ra, 2) AS "Score (gate)",
    round(correlacion_confianza, 2) AS "Confianza final",
    correlacion_justificacion AS "Por qué la propuso el juez",
    correlacion_alternativas AS "Alternativas"
FROM "wiki/resultados-aprendizaje"
WHERE correlacion_estado = "pendiente_revision"
SORT correlacion_confianza DESC
```

## ✅ Aceptadas

```dataview
TABLE WITHOUT ID
    file.link AS "RA",
    requiere_practica AS "Fuente",
    practica_experimentos AS "Experimento(s)",
    round(correlacion_confianza, 2) AS "Confianza",
    choice(correlacion_revisado_por_docente, "👤 docente", "🤖 automático") AS "Confirmado por"
FROM "wiki/resultados-aprendizaje"
WHERE correlacion_estado = "aceptado"
SORT correlacion_revisado_por_docente DESC, correlacion_confianza DESC
```

## ⚪ Sin candidato

RA teórico-prácticos (`hp_totales > 0`, pasan el gate) sin fuente de laboratorio asociada. `correlacion_revisado_por_docente` distingue "aún sin revisar" de "revisado y descartado".

```dataview
TABLE WITHOUT ID
    file.link AS "RA",
    pertenece_a AS "Asignatura",
    round(correlacion_score_ra, 2) AS "Score (gate)",
    choice(correlacion_revisado_por_docente, "👤 revisado, descartado", "⏳ sin revisar") AS "Estado de revisión",
    correlacion_nota_docente AS "Nota"
FROM "wiki/resultados-aprendizaje"
WHERE correlacion_estado = "sin_candidato" AND tipo_abordaje = "teórico-práctica"
SORT correlacion_revisado_por_docente DESC, correlacion_score_ra DESC
```

## 📘 RA teóricos (compuerta cerrada por diseño — `hp_totales = 0`)

RA de módulos estrictamente teóricos: por la regla central (`hp_totales == 0`) no se les asocia una práctica obligatoria de laboratorio; a lo sumo una `aplicacion_potencial`, que no cuenta como cobertura. No son un pendiente: están aquí para que se vea que quedaron fuera a propósito.

```dataview
TABLE WITHOUT ID
    file.link AS "RA",
    pertenece_a AS "Asignatura",
    horas AS "Horas",
    "Compuerta cerrada (hp_totales = 0)" AS "Estado"
FROM "wiki/resultados-aprendizaje"
WHERE tipo_abordaje = "teórica"
SORT file.name ASC
```
