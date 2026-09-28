---
tipo: vista_dataview
etiquetas: []
descripcion: Presentaciones de los temarios — qué temario tiene su presentación Beamer, cuántas diapositivas, si hay que revisarla y con qué docente y versión del diseño se hizo, según los campos `presentacion_*` que escribe PRESENTACIONES. No editar los datos aquí -- correr PRESENTACIONES para refrescar.
fecha_creacion: YYYY-MM-DD
fecha_actualizacion: YYYY-MM-DD
---

# Matriz Temario ↔ Presentación

Vacía a propósito — se llena sola en cuanto PRESENTACIONES (`python src/presentaciones.py CODIGO`) escriba los campos `presentacion_*` en las páginas de `generacion/temarios/`. Las tablas leen en vivo ese frontmatter.

Cada presentación sale de las diapositivas en LaTeX que el modelo escribe por cada parte del temario (la apertura y cada bloque: una llamada por parte), verificadas con una lista de comandos permitidos y guardadas junto al `.tex` (`{codigo}-semanaNN.plan.json`): mientras el temario no cambie, rehacerla (otro docente, otro programa, otra versión del diseño) no vuelve a llamar al modelo, y si cambia un bloque solo se vuelve a pedir ese. `python src/lint.py` (regla L14) avisa de las que quedaron desactualizadas y de cuánto cuesta rehacerlas.

## 🟡 Por revisar

Presentaciones con avisos (una parte que el modelo no logró escribir con LaTeX admitido y quedó provisional, un carácter sin equivalente en LaTeX, algo que la verificación estática detectó): abrir el `.tex` o compilarlo y leer `presentacion_avisos`.

```dataview
TABLE WITHOUT ID
    file.link AS "Temario",
    asignatura AS "Asignatura",
    semana AS "Semana",
    presentacion_avisos AS "Avisos"
FROM "generacion/temarios"
WHERE presentacion_estado = "revisar"
SORT asignatura ASC, semana ASC
```

## Sin presentación

```dataview
TABLE WITHOUT ID
    file.link AS "Temario",
    asignatura AS "Asignatura",
    semana AS "Semana"
FROM "generacion/temarios"
WHERE tipo = "temario" AND !presentacion_estado
SORT asignatura ASC, semana ASC
```

## Todas

```dataview
TABLE WITHOUT ID
    file.link AS "Temario",
    asignatura AS "Asignatura",
    semana AS "Semana",
    presentacion_estado AS "Estado",
    presentacion_diapositivas AS "Diapositivas",
    presentacion_docente AS "Docente",
    presentacion_diseno AS "Diseño",
    presentacion_fecha AS "Fecha"
FROM "generacion/temarios"
WHERE presentacion_estado
SORT asignatura ASC, semana ASC
```
