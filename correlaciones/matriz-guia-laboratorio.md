---
tipo: vista_dataview
etiquetas: []
descripcion: Guías de laboratorio — qué semana tiene su guía, de dónde sale su práctica (un manual de laboratorio o la bibliografía ingerida), con qué RA y fuentes se correlaciona y en qué estado está, según el frontmatter que escribe GUIA-LABORATORIO. No editar los datos aquí -- correr GUIA-LABORATORIO para refrescar.
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---

# Matriz RA ↔ Práctica ↔ Guía de laboratorio

Vacía a propósito — se llena sola en cuanto GUIA-LABORATORIO (`python src/guia_laboratorio.py CODIGO`) escriba las guías en `generacion/guias-laboratorio/`. Las tablas leen en vivo su frontmatter.

Cada guía correlaciona una semana de clase con su RA y con la práctica que lo desarrolla: la del **manual de laboratorio** que CORRELATE le asignó al RA (`requiere_practica`), o, si no hay manuales o ninguno le corresponde, una **propuesta a partir de la bibliografía ingerida** (`base_bibliografica`: las fuentes cargadas en que se basa), que el docente valida antes de usarla. `python src/lint.py` (regla L17) avisa de las guías que faltan o quedaron desactualizadas, y `python src/analizar_cambios.py` las pone en su plan mínimo.

## 🟡 Por validar: propuestas a partir de la bibliografía

Sin práctica de un manual: el modelo propuso la práctica con las fuentes cargadas y el tema del temario. Validar que el montaje, los equipos y las medidas de seguridad sean los del laboratorio.

```dataview
TABLE WITHOUT ID
    file.link AS "Guía",
    asignatura AS "Asignatura",
    semana AS "Semana",
    resultado_aprendizaje AS "RA",
    base_bibliografica AS "Basada en",
    temario AS "Sesión"
FROM "generacion/guias-laboratorio"
WHERE origen_practica = "bibliografia"
SORT asignatura ASC, semana ASC
```

## 🟡 Por revisar

Guías con avisos (una práctica que el RA aún no tiene aceptada, sin facultad, un carácter sin equivalente LaTeX, un fallo al compilar…): leer `avisos` antes de usarla.

```dataview
TABLE WITHOUT ID
    file.link AS "Guía",
    asignatura AS "Asignatura",
    semana AS "Semana",
    origen_practica AS "Origen",
    avisos AS "Avisos"
FROM "generacion/guias-laboratorio"
WHERE estado = "revisar"
SORT asignatura ASC, semana ASC
```

## Desde los manuales de laboratorio

```dataview
TABLE WITHOUT ID
    file.link AS "Guía",
    asignatura AS "Asignatura",
    semana AS "Semana",
    resultado_aprendizaje AS "RA",
    practica AS "Manual",
    practica_experimento AS "Experimento",
    practica_correlacion_estado AS "Correlación"
FROM "generacion/guias-laboratorio"
WHERE origen_practica = "manual"
SORT asignatura ASC, semana ASC
```

## RA con práctica asignada (CORRELATE)

Los RA que tienen una práctica de un manual: cada semana de clase de esos RA con temario lleva su guía.

```dataview
TABLE WITHOUT ID
    file.link AS "RA",
    pertenece_a AS "Asignatura",
    requiere_practica AS "Manual",
    practica_experimentos AS "Experimento",
    correlacion_estado AS "Correlación"
FROM "wiki/resultados-aprendizaje"
WHERE requiere_practica
SORT file.name ASC
```

## Todas

```dataview
TABLE WITHOUT ID
    file.link AS "Guía",
    asignatura AS "Asignatura",
    semana AS "Semana",
    origen_practica AS "Origen",
    estado AS "Estado",
    docente AS "Docente",
    facultad AS "Facultad",
    compilada AS "Compilada",
    fecha_actualizacion AS "Fecha"
FROM "generacion/guias-laboratorio"
WHERE tipo = "guia_laboratorio"
SORT asignatura ASC, semana ASC
```
