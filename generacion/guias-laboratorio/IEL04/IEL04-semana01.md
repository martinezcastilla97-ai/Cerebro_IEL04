---
tipo: guia_laboratorio
asignatura: '[[IEL04 - Circuitos Eléctricos I]]'
resultado_aprendizaje: '[[IEL04-RA1]]'
temario: '[[IEL04-semana01]]'
semana: 1
total_semanas: 14
origen_practica: bibliografia
practica: null
practica_experimento: null
base_bibliografica:
- '[[floyd-principios-circuitos-electricos]]'
- '[[boylestad-introduccion-analisis-circuitos]]'
practica_correlacion_estado: sin_candidato
practica_revisada_por_docente: false
desde_bibliografia: false
estado: revisar
avisos:
- 'práctica propuesta a partir de la bibliografía cargada ([1] floyd-principios-circuitos-electricos, [2] boylestad-introduccion-analisis-circuitos), no de un manual de laboratorio: el docente valida que el montaje, los equipos y las medidas de seguridad sean los del laboratorio antes de usar la guía'
archivo_tex: generacion/guias-laboratorio/IEL04/IEL04-semana01.tex
temario_hash: 4aa40113fc2d922d
huella: 5899d06855da8f91
formato: 3
docente: Ing. Sergio Martinez Castilla
facultad: Facultad de Ingenierías
compilada: '2026-10-27'
fecha_creacion: '2026-10-25'
fecha_actualizacion: '2026-10-27'
---
# Guía de laboratorio: Identificación y medición de la capacitancia de condensadores comerciales

> **Facultad:** Facultad de Ingenierías · **Módulo:** IEL04 — Circuitos Eléctricos I · **Docente:** Ing. Sergio Martinez Castilla
> **Semana:** 1 de 14 · **Resultado de aprendizaje:** [[IEL04-RA1]] · **Sesión:** [[IEL04-semana01]] · **Práctica:** propuesta a partir de la bibliografía [1] [2] · **Duración:** 240 minutos

Esta práctica lleva al banco el contenido de la sesión teórica de la semana 1, «El condensador: estructura, capacitancia, tipos e identificación de componentes comerciales», y reproduce su caso de estudio: identificar por su marcado los cinco condensadores del kit del grupo, calcular el intervalo que admite su tolerancia, medir su capacitancia real y decidir si cada uno puede usarse en las prácticas siguientes. No hay un manual de laboratorio asignado a este resultado de aprendizaje, por lo que la práctica se propone a partir de la bibliografía cargada: el texto de Floyd describe la verificación de un condensador con un medidor LCR o con la función de capacitancia del multímetro [1], y Boylestad, los esquemas de rotulado de los condensadores pequeños y las letras de tolerancia [2]. La práctica desarrolla los criterios de medición del RA IEL04-RA1 en circuitos capacitivos y deja registradas las capacitancias reales de los condensadores que formarán, con las bobinas de la semana 2, los circuitos LC de la semana 3.

## 1. Objetivos

**Objetivo general:** Verificar experimentalmente la capacitancia de condensadores comerciales a partir de su marcado y de la medición con instrumentos.

**Objetivos específicos:**

- Identificar el tipo, el valor nominal, la tolerancia y la tensión de trabajo de cinco condensadores a partir de su marcado. *(CE1)*
- Medir la capacitancia de cada condensador con el medidor LCR y con el multímetro, y calcular su desviación respecto del valor nominal. *(CE2)*
- Registrar la capacitancia real de los condensadores C2 y C3, que formarán el circuito LC de la semana 3, y estimar con ella su frecuencia de resonancia. *(CE3)*

## 2. Materiales y Equipos

**Tabla 1.** Materiales y equipos de la práctica

| # | Material o equipo | Especificación | Cantidad |
|---|---|---|---|
| 1 | Kit de condensadores del grupo | C1 223J, C2 104K 100V, C3 472K, C4 470 µF 25 V, C5 100 µF 16 V | 1 |
| 2 | Medidor LCR | — | 1 |
| 3 | Multímetro digital con función de capacitancia | — | 1 |
| 4 | Resistencia de descarga | 1 kΩ | 1 |
| 5 | Cables con pinzas de cocodrilo aisladas | — | 4 |
| 6 | Lupa o lente de aumento para leer el marcado | — | 1 |
| 7 | Gafas de seguridad | — | 3 |

## 3. Procedimiento

La práctica ocupa el bloque de 2 h de laboratorio de la sesión y se realiza en grupos de tres estudiantes, con tres roles que rotan entre etapas: quien monta y opera el circuito, quien mide y quien registra y verifica los cálculos. Antes de energizar cualquier montaje, el docente o el monitor revisa la conexión. Cada etapa abre con su diagrama de flujo, que muestra la secuencia y las comprobaciones de un vistazo, y sigue con sus pasos numerados; cada paso indica cuánto dura, qué debe observarse para saber que salió bien y qué hacer si no. Los valores numéricos de la sesión teórica sirven de referencia: las lecturas propias del grupo se registran en las tablas de la sección de análisis.

> Los diagramas de flujo, los circuitos y las gráficas son código LaTeX (TikZ, circuitikz y pgfplots), como en el .tex: Obsidian los dibuja con el plugin TikZJax; sin él, se ve el código (el PDF de la guía los trae dibujados).

### 3.1 Preparación e identificación (33 min)

```tikz
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shapes.misc}
\begin{document}
\definecolor{iubnavy}{HTML}{121023}
\definecolor{iubyellow}{HTML}{FFDF2D}
\definecolor{iubwhite}{HTML}{FFFFFF}
\definecolor{iubblue}{HTML}{00ADE7}
\definecolor{iuborange}{HTML}{E39037}
\definecolor{iubgreen}{HTML}{3B9C6D}
\colorlet{iubgris}{iubnavy!18}
\colorlet{iubgrisoscuro}{iubnavy!60}
\colorlet{iubfondoazul}{iubblue!8}
\colorlet{iubfondonaranja}{iuborange!10}
\colorlet{iubfondoverde}{iubgreen!9}
\colorlet{iubfondogris}{iubnavy!5}
\colorlet{iubpurple}{iubnavy!45}
\tikzset{
  dcaja/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=1pt, align=center, inner sep=2pt, text=iubnavy},
  destado/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=6pt, align=center, inner sep=2pt, text=iubnavy},
  ddecision/.style={draw=iuborange, fill=iubfondonaranja, line width=1pt, diamond, aspect=1.6, align=center, inner sep=1pt, text=iubnavy},
  dterminal/.style={draw=iubgreen, fill=iubfondoverde, line width=1pt, rounded rectangle, align=center, inner sep=2pt, text=iubnavy},
  dflecha/.style={-{Stealth[length=2.4mm]}, line width=0.9pt, draw=iubnavy},
  drotulo/.style={font=\footnotesize, text=iubgrisoscuro, fill=white, fill opacity=0.92, text opacity=1, inner sep=1.5pt},
}
\begin{tikzpicture}[x=1in, y=1in, font=\small]
  % nodos (centro en pulgadas, con el tamano que calcula figuras.py)
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n0) at (0.689,-0.445) {Inicio de \\ la etapa};  % ini
  \node[dcaja, minimum width=1.456in, minimum height=0.890in] (n1) at (2.725,-0.445) {Revisar kit \\ e \\ instrumentos};  % a0
  \node[dcaja, minimum width=1.549in, minimum height=0.680in] (n2) at (5.095,-0.445) {Descargar \\ condensadores};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n3) at (7.373,-0.445) {Leer \\ marcado y \\ tolerancia};  % a2
  \node[dcaja, minimum width=1.177in, minimum height=0.890in] (n4) at (7.373,-2.018) {Calcular \\ intervalo \\ admisible};  % a3
  \node[ddecision, minimum width=2.045in, minimum height=1.156in] (n5) at (5.095,-2.018) {\textquestiondown{}Valores \\ coherentes?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n6) at (2.725,-2.018) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n3);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (3.673,-2.018) {s\'{\i}};
  \node[drotulo] at (6.470,-1.573) {no};
\end{tikzpicture}
\end{document}
```

*Figura 1. Diagrama de flujo de la etapa 1: Preparación e identificación*

1. Revisar que el kit contenga los cinco condensadores y que el medidor LCR y el multímetro enciendan y tengan batería suficiente. *(≈ 5 min)* **Comprobación:** Los dos instrumentos deben mostrar lectura estable con las puntas abiertas; si no, solicitar otro instrumento.
2. Descargar el condensador conectando entre sus terminales, durante unos segundos, una resistencia de 1 kΩ sujeta con pinzas aisladas, y medir con el voltímetro en cd la tensión entre terminales. *(≈ 3 min)* **Comprobación:** La tensión debe ser prácticamente nula (menos de 0,1 V); si no lo es, repetir la descarga antes de manipular el componente. **Seguridad:** No cortocircuitar los terminales con los dedos ni con una herramienta metálica: un condensador puede conservar carga después de desconectado.

```tikz
\usepackage{circuitikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shapes.misc}
\begin{document}
\definecolor{iubnavy}{HTML}{121023}
\definecolor{iubyellow}{HTML}{FFDF2D}
\definecolor{iubwhite}{HTML}{FFFFFF}
\definecolor{iubblue}{HTML}{00ADE7}
\definecolor{iuborange}{HTML}{E39037}
\definecolor{iubgreen}{HTML}{3B9C6D}
\colorlet{iubgris}{iubnavy!18}
\colorlet{iubgrisoscuro}{iubnavy!60}
\colorlet{iubfondoazul}{iubblue!8}
\colorlet{iubfondonaranja}{iuborange!10}
\colorlet{iubfondoverde}{iubgreen!9}
\colorlet{iubfondogris}{iubnavy!5}
\colorlet{iubpurple}{iubnavy!45}
\tikzset{
  dcaja/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=1pt, align=center, inner sep=2pt, text=iubnavy},
  destado/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=6pt, align=center, inner sep=2pt, text=iubnavy},
  ddecision/.style={draw=iuborange, fill=iubfondonaranja, line width=1pt, diamond, aspect=1.6, align=center, inner sep=1pt, text=iubnavy},
  dterminal/.style={draw=iubgreen, fill=iubfondoverde, line width=1pt, rounded rectangle, align=center, inner sep=2pt, text=iubnavy},
  dflecha/.style={-{Stealth[length=2.4mm]}, line width=0.9pt, draw=iubnavy},
  drotulo/.style={font=\footnotesize, text=iubgrisoscuro, fill=white, fill opacity=0.92, text opacity=1, inner sep=1.5pt},
}
\begin{circuitikz}[color=iubnavy]
\draw (0,0) to[C, l=$C$] (0,3) -- (3,3) to[R, l=$1~\text{k}\Omega$] (3,0) -- (0,0); \draw (3,3) -- (5,3) to[voltmeter] (5,0) -- (3,0);
\end{circuitikz}
\end{document}
```

*Figura 2. Descarga del condensador a través de una resistencia, con el voltímetro en paralelo*

3. Leer el marcado de cada condensador y anotar en la tabla de registro su tipo, su valor nominal (convertido a nF o µF), su tolerancia y su tensión de trabajo, usando el código de tres dígitos y las letras J (±5 %) y K (±10 %) [2]. *(≈ 15 min)* **Comprobación:** Para C1 debe obtenerse 22 nF ±5 %; si el valor no coincide, repasar la regla del tercer dígito como número de ceros en pF.
4. Calcular para cada condensador el intervalo admisible $C_{\min} = C_n(1-t)$ a $C_{\max} = C_n(1+t)$. *(≈ 10 min)* **Comprobación:** Para C1 el intervalo es de 20,9 nF a 23,1 nF; si el resultado difiere, revisar la conversión de unidades.

### 3.2 Medición de la capacitancia (40 min)

```tikz
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shapes.misc}
\begin{document}
\definecolor{iubnavy}{HTML}{121023}
\definecolor{iubyellow}{HTML}{FFDF2D}
\definecolor{iubwhite}{HTML}{FFFFFF}
\definecolor{iubblue}{HTML}{00ADE7}
\definecolor{iuborange}{HTML}{E39037}
\definecolor{iubgreen}{HTML}{3B9C6D}
\colorlet{iubgris}{iubnavy!18}
\colorlet{iubgrisoscuro}{iubnavy!60}
\colorlet{iubfondoazul}{iubblue!8}
\colorlet{iubfondonaranja}{iuborange!10}
\colorlet{iubfondoverde}{iubgreen!9}
\colorlet{iubfondogris}{iubnavy!5}
\colorlet{iubpurple}{iubnavy!45}
\tikzset{
  dcaja/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=1pt, align=center, inner sep=2pt, text=iubnavy},
  destado/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=6pt, align=center, inner sep=2pt, text=iubnavy},
  ddecision/.style={draw=iuborange, fill=iubfondonaranja, line width=1pt, diamond, aspect=1.6, align=center, inner sep=1pt, text=iubnavy},
  dterminal/.style={draw=iubgreen, fill=iubfondoverde, line width=1pt, rounded rectangle, align=center, inner sep=2pt, text=iubnavy},
  dflecha/.style={-{Stealth[length=2.4mm]}, line width=0.9pt, draw=iubnavy},
  drotulo/.style={font=\footnotesize, text=iubgrisoscuro, fill=white, fill opacity=0.92, text opacity=1, inner sep=1.5pt},
}
\begin{tikzpicture}[x=1in, y=1in, font=\small]
  % nodos (centro en pulgadas, con el tamano que calcula figuras.py)
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n0) at (0.689,-0.445) {Inicio de \\ la etapa};  % ini
  \node[dcaja, minimum width=1.456in, minimum height=0.890in] (n1) at (2.725,-0.445) {Configurar \\ LCR en \\ capacitancia};  % a0
  \node[dcaja, minimum width=1.177in, minimum height=0.680in] (n2) at (4.956,-0.445) {Medir C1, \\ C2 y C3};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n3) at (7.140,-0.445) {Medir C4 y \\ C5 con \\ polaridad};  % a2
  \node[dcaja, minimum width=1.363in, minimum height=0.890in] (n4) at (7.140,-2.018) {Repetir con \\ el \\ mult\'{\i}metro};  % a3
  \node[ddecision, minimum width=1.766in, minimum height=1.156in] (n5) at (4.956,-2.018) {\textquestiondown{}Lecturas \\ estables?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n6) at (2.725,-2.018) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (3.840,-2.018) {s\'{\i}};
  \node[drotulo] at (5.192,-1.232) {no};
\end{tikzpicture}
\end{document}
```

*Figura 3. Diagrama de flujo de la etapa 2: Medición de la capacitancia*

5. Ajustar el medidor LCR en la función de capacitancia y conectar C1 entre sus terminales; anotar la lectura en la misma unidad del valor nominal [1]. *(≈ 8 min)* **Comprobación:** La lectura debe estabilizarse en pocos segundos; si oscila, revisar el contacto de las pinzas.
6. Repetir la medición con C2 y C3 y anotar las lecturas. *(≈ 10 min)* **Comprobación:** Las lecturas deben estar en el orden de magnitud del nominal (nF); una lectura nula o en pF indica un contacto abierto.
7. Medir C4 y C5 conectando el terminal positivo del electrolítico al terminal positivo del instrumento [2]. *(≈ 10 min)* **Comprobación:** Comprobar la marca de polaridad antes de conectar; si el instrumento indica sobrecarga, revisar la escala. **Seguridad:** Respetar la polaridad de los electrolíticos y no superar su tensión de trabajo.
8. Medir de nuevo los cinco condensadores con la función de capacitancia del multímetro y anotar ambas lecturas. *(≈ 12 min)* **Comprobación:** Las dos lecturas de un mismo condensador deben diferir menos que la tolerancia; si no, repetir la medición con el LCR.

### 3.3 Decisión y registro para el circuito LC (22 min)

```tikz
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shapes.misc}
\begin{document}
\definecolor{iubnavy}{HTML}{121023}
\definecolor{iubyellow}{HTML}{FFDF2D}
\definecolor{iubwhite}{HTML}{FFFFFF}
\definecolor{iubblue}{HTML}{00ADE7}
\definecolor{iuborange}{HTML}{E39037}
\definecolor{iubgreen}{HTML}{3B9C6D}
\colorlet{iubgris}{iubnavy!18}
\colorlet{iubgrisoscuro}{iubnavy!60}
\colorlet{iubfondoazul}{iubblue!8}
\colorlet{iubfondonaranja}{iuborange!10}
\colorlet{iubfondoverde}{iubgreen!9}
\colorlet{iubfondogris}{iubnavy!5}
\colorlet{iubpurple}{iubnavy!45}
\tikzset{
  dcaja/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=1pt, align=center, inner sep=2pt, text=iubnavy},
  destado/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=6pt, align=center, inner sep=2pt, text=iubnavy},
  ddecision/.style={draw=iuborange, fill=iubfondonaranja, line width=1pt, diamond, aspect=1.6, align=center, inner sep=1pt, text=iubnavy},
  dterminal/.style={draw=iubgreen, fill=iubfondoverde, line width=1pt, rounded rectangle, align=center, inner sep=2pt, text=iubnavy},
  dflecha/.style={-{Stealth[length=2.4mm]}, line width=0.9pt, draw=iubnavy},
  drotulo/.style={font=\footnotesize, text=iubgrisoscuro, fill=white, fill opacity=0.92, text opacity=1, inner sep=1.5pt},
}
\begin{tikzpicture}[x=1in, y=1in, font=\small]
  % nodos (centro en pulgadas, con el tamano que calcula figuras.py)
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n0) at (0.735,-0.445) {Inicio de \\ la etapa};  % ini
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n1) at (3.112,-0.445) {Calcular \\ desviaci\'{o}n \\ porcentual};  % a0
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n2) at (5.389,-0.445) {Decidir \\ aceptaci\'{o}n};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n3) at (5.389,-2.018) {Rotular C2 \\ y C3};  % a2
  \node[ddecision, minimum width=2.045in, minimum height=1.156in] (n4) at (3.112,-2.018) {\textquestiondown{}Dentro de \\ tolerancia?};  % dec
  \node[dterminal, minimum width=1.470in, minimum height=0.680in] (n5) at (0.735,-2.018) {Componente \\ al kit};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n1);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.686,-2.018) {s\'{\i}};
  \node[drotulo] at (3.348,-1.232) {no};
\end{tikzpicture}
\end{document}
```

*Figura 4. Diagrama de flujo de la etapa 3: Decisión y registro para el circuito LC*

9. Calcular la desviación $e_{\%} = (C_m - C_n)/C_n \times 100$ de cada condensador y decidir si se acepta (|e| no supera la tolerancia). *(≈ 12 min)* **Comprobación:** Un condensador fuera de su intervalo se rechaza y se marca; se informa al docente para reponerlo.

**Ecuación (1).** Desviación relativa del valor medido respecto del nominal:

$$
e_{\%} = \frac{C_m - C_n}{C_n} \times 100 \tag{1}
$$

donde $e_{\%}$ es la desviación en porcentaje, $C_m$ la capacitancia medida y $C_n$ la nominal, en la misma unidad (nF o µF).

10. Rotular C2 y C3 con su capacitancia medida y calcular con ella y con L = 10 mH la frecuencia de resonancia $f_r = 1/(2\pi\sqrt{LC})$ que se medirá en la semana 3. *(≈ 10 min)* **Comprobación:** Con los valores nominales se obtiene unos 5,03 kHz para C2; un resultado muy distinto indica un error de unidades.

**Ecuación (2).** Frecuencia de resonancia del circuito LC:

$$
f_r = \frac{1}{2\pi\sqrt{L C}} \tag{2}
$$

donde $f_r$ en hercios (Hz), $L$ en henrios (H) y $C$ en faradios (F).


### 3.4 Desmontaje y cierre (10 min)

```tikz
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,shapes.misc}
\begin{document}
\definecolor{iubnavy}{HTML}{121023}
\definecolor{iubyellow}{HTML}{FFDF2D}
\definecolor{iubwhite}{HTML}{FFFFFF}
\definecolor{iubblue}{HTML}{00ADE7}
\definecolor{iuborange}{HTML}{E39037}
\definecolor{iubgreen}{HTML}{3B9C6D}
\colorlet{iubgris}{iubnavy!18}
\colorlet{iubgrisoscuro}{iubnavy!60}
\colorlet{iubfondoazul}{iubblue!8}
\colorlet{iubfondonaranja}{iuborange!10}
\colorlet{iubfondoverde}{iubgreen!9}
\colorlet{iubfondogris}{iubnavy!5}
\colorlet{iubpurple}{iubnavy!45}
\tikzset{
  dcaja/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=1pt, align=center, inner sep=2pt, text=iubnavy},
  destado/.style={draw=iubblue, fill=iubfondoazul, line width=1pt, rounded corners=6pt, align=center, inner sep=2pt, text=iubnavy},
  ddecision/.style={draw=iuborange, fill=iubfondonaranja, line width=1pt, diamond, aspect=1.6, align=center, inner sep=1pt, text=iubnavy},
  dterminal/.style={draw=iubgreen, fill=iubfondoverde, line width=1pt, rounded rectangle, align=center, inner sep=2pt, text=iubnavy},
  dflecha/.style={-{Stealth[length=2.4mm]}, line width=0.9pt, draw=iubnavy},
  drotulo/.style={font=\footnotesize, text=iubgrisoscuro, fill=white, fill opacity=0.92, text opacity=1, inner sep=1.5pt},
}
\begin{tikzpicture}[x=1in, y=1in, font=\small]
  % nodos (centro en pulgadas, con el tamano que calcula figuras.py)
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n0) at (0.689,-0.445) {Inicio de \\ la etapa};  % ini
  \node[dcaja, minimum width=1.456in, minimum height=0.680in] (n1) at (2.950,-0.445) {Desenergizar \\ el montaje};  % a0
  \node[dcaja, minimum width=1.363in, minimum height=0.890in] (n2) at (5.204,-0.445) {Descargar y \\ retirar \\ componentes};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n3) at (5.204,-2.018) {Revisar \\ tablas con \\ el docente};  % a2
  \node[ddecision, minimum width=1.905in, minimum height=1.156in] (n4) at (2.950,-2.018) {\textquestiondown{}Tablas \\ completas?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n5) at (0.689,-2.018) {Fin de la \\ pr\'{a}ctica};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) to[bend right=24] (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n3);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.593,-2.018) {s\'{\i}};
  \node[drotulo] at (4.302,-2.343) {no};
\end{tikzpicture}
\end{document}
```

*Figura 5. Diagrama de flujo de la etapa 4: Desmontaje y cierre*

11. Apagar el generador de funciones y la fuente, desconectar las puntas del osciloscopio y retirar la alimentación del protoboard. *(≈ 3 min)* **Comprobación:** Ningún indicador de salida debe quedar encendido en el generador ni en la fuente. **Seguridad:** Desenergizar siempre antes de retirar componentes.
12. Descargar los condensadores del montaje con la resistencia de descarga, retirar los componentes y devolverlos al kit del grupo con su rótulo. *(≈ 4 min)* **Comprobación:** El kit debe quedar completo, con cada componente en su lugar y con su valor medido anotado.
13. Revisar con el docente las tablas de registro antes de abandonar el banco. *(≈ 3 min)* **Comprobación:** Las tablas deben estar completas y con unidades; si falta un dato, repetir esa medición antes de desmontar el instrumento.

## 4. Cuestiones a Resolver

1. ¿Qué condensadores quedaron fuera de su intervalo de tolerancia y qué explicación física ofrece la sesión teórica para cada caso?
2. ¿En cuánto difieren las lecturas del medidor LCR y del multímetro para un mismo condensador, y cuál de los dos instrumentos es más adecuado para valores de pocos nanofaradios?
3. ¿Por qué el rótulo «104» corresponde a 100 nF y no a 104 pF?
4. Con la capacitancia medida de C2, ¿cuánto cambia la frecuencia de resonancia prevista respecto de la calculada con el valor nominal?

## 5. Análisis de Resultados

Completar la tabla de identificación con el valor nominal, la tolerancia, el intervalo admisible, las dos lecturas y la desviación porcentual de cada condensador, usando la misma unidad del valor nominal en cada fila.

Representar en un gráfico de barras la desviación porcentual de cada condensador junto con su tolerancia, de modo que se vea de un vistazo cuáles se aceptan; discutir si las desviaciones observadas son coherentes con el tipo de dieléctrico, como describe la sesión teórica.

**Tabla 2.** Identificación y medición de los condensadores del kit

| Ref. | Marcado | Cn (nF o µF) | Tolerancia (%) | Cm LCR (nF o µF) | Cm multímetro (nF o µF) | e (%) |
|---|---|---|---|---|---|---|
|   |   |   |   |   |   |   |
|   |   |   |   |   |   |   |
|   |   |   |   |   |   |   |
|   |   |   |   |   |   |   |
|   |   |   |   |   |   |   |

**Tabla 3.** Frecuencia de resonancia prevista para la semana 3

| Condensador | C medida (nF) | L supuesta (mH) | fr con nominales (kHz) | fr con medida (kHz) |
|---|---|---|---|---|
|   |   |   |   |   |
|   |   |   |   |   |

## 6. Conclusiones

Contrastar el valor medido de cada condensador con su intervalo de tolerancia y justificar la decisión de aceptarlo o rechazarlo; explicar las desviaciones con los mecanismos vistos en la sesión (envejecimiento del dieléctrico, secado del electrolito, rotulado incorrecto) y relacionar la práctica con el criterio de medición en circuitos capacitivos del RA.

- ¿Qué condensador mostró la mayor desviación y qué la explica?
- ¿Por qué conviene usar en los cálculos de las semanas siguientes los valores medidos y no los nominales?
- ¿Qué precaución resultó indispensable al medir los electrolíticos?

## 7. Recomendaciones de Seguridad

- Trabajar con el circuito desenergizado mientras se conecta o modifica el montaje; energizar solo después de la revisión del docente.
- Descargar los condensadores con una resistencia antes de manipularlos o medirlos, y respetar la polaridad de los electrolíticos: conectado con la polaridad invertida, un electrolítico puede explotar y provocar lesiones [1].
- Usar gafas de seguridad al medir y manipular los electrolíticos C4 y C5.
- Sujetar los condensadores con pinzas aisladas al descargarlos y no doblar en exceso sus terminales.

## 8. Bibliografía

[1] Floyd, Thomas L., *Principios de circuitos eléctricos*, 8.ª ed., Pearson Educación, 2007.

[2] Boylestad, Robert L., *Introducción al análisis de circuitos*, 10.ª ed., Pearson Educación, 2004.
