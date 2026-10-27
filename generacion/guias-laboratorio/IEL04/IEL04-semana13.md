---
tipo: guia_laboratorio
asignatura: '[[IEL04 - Circuitos Eléctricos I]]'
resultado_aprendizaje: '[[IEL04-RA4]]'
temario: '[[IEL04-semana13]]'
semana: 13
total_semanas: 14
origen_practica: bibliografia
practica: null
practica_experimento: null
base_bibliografica:
- '[[floyd-principios-circuitos-electricos]]'
- '[[boylestad-introduccion-analisis-circuitos]]'
- '[[deorsola-morcelle-circuitos-electricos-parte-1]]'
practica_correlacion_estado: sin_candidato
practica_revisada_por_docente: false
desde_bibliografia: false
estado: revisar
avisos:
- 'práctica propuesta a partir de la bibliografía cargada ([1] floyd-principios-circuitos-electricos, [2] boylestad-introduccion-analisis-circuitos, [3] deorsola-morcelle-circuitos-electricos-parte-1), no de un manual de laboratorio: el docente valida que el montaje, los equipos y las medidas de seguridad sean los del laboratorio antes de usar la guía'
archivo_tex: generacion/guias-laboratorio/IEL04/IEL04-semana13.tex
temario_hash: c118b5b149f5d329
huella: c924d604cf87cfb7
formato: 3
docente: Ing. Sergio Martinez Castilla
facultad: Facultad de Ingenierías
compilada: '2026-10-27'
fecha_creacion: '2026-10-25'
fecha_actualizacion: '2026-10-27'
---
# Guía de laboratorio: Caracterización de un filtro pasabanda RLC en serie: frecuencia de resonancia, frecuencias de corte, ancho de banda y factor de calidad

> **Facultad:** Facultad de Ingenierías · **Módulo:** IEL04 — Circuitos Eléctricos I · **Docente:** Ing. Sergio Martinez Castilla
> **Semana:** 13 de 14 · **Resultado de aprendizaje:** [[IEL04-RA4]] · **Sesión:** [[IEL04-semana13]] · **Práctica:** propuesta a partir de la bibliografía [1] [2] [3] · **Duración:** 240 minutos

La práctica cierra el RA IEL04-RA4 y corresponde a la sesión teórica de la semana 13, «Cálculo y medición de parámetros en circuitos RLC en serie, en paralelo y mixtos: filtros resonantes, frecuencia de resonancia, ancho de banda y nomenclatura». Reproduce su caso de estudio: un filtro pasabanda formado por el resistor de 100 Ω, la bobina L3 y el condensador C2 en serie, con la salida en el resistor, del que se miden la frecuencia de resonancia, las frecuencias de corte, el ancho de banda y el factor de calidad. No hay un manual de laboratorio asignado, por lo que la práctica se propone a partir de la bibliografía cargada: Floyd define el ancho de banda de los circuitos resonantes entre las frecuencias en que la respuesta cae al 70,7 % y trata los filtros pasabanda [1], Boylestad el factor de calidad y la selectividad [2] y Deorsola la nomenclatura y la simbología de los circuitos [3].

## 1. Objetivos

**Objetivo general:** Caracterizar experimentalmente un filtro pasabanda RLC en serie y contrastar sus parámetros con el cálculo.

**Objetivos específicos:**

- Identificar y verificar con instrumentos los componentes del filtro, con su simbología y sus unidades. *(CE1)*
- Medir la tensión de salida del filtro en función de la frecuencia con el multímetro y el osciloscopio. *(CE2)*
- Determinar experimentalmente la frecuencia de resonancia, las frecuencias de corte, el ancho de banda y el factor de calidad del circuito RLC en serie. *(CE3)*

## 2. Materiales y Equipos

**Tabla 1.** Materiales y equipos de la práctica

| # | Material o equipo | Especificación | Cantidad |
|---|---|---|---|
| 1 | Resistor | 100 Ω (medido 99,5 Ω en la sesión) | 1 |
| 2 | Bobina L3 del kit | 103K, 10,4 mH y 24,6 Ω medidos | 1 |
| 3 | Condensador C2 del kit | 104K, 97,8 nF medidos | 1 |
| 4 | Generador de funciones | — | 1 |
| 5 | Osciloscopio de dos canales con puntas ×10 | — | 1 |
| 6 | Multímetro digital de verdadero valor eficaz | — | 2 |
| 7 | Medidor LCR | — | 1 |
| 8 | Protoboard | — | 1 |
| 9 | Cables de conexión | — | 12 |
| 10 | Resistencia de descarga | 1 kΩ | 1 |

## 3. Procedimiento

La práctica ocupa el bloque de 2 h de laboratorio de la sesión y se realiza en grupos de tres estudiantes, con tres roles que rotan entre etapas: quien monta y opera el circuito, quien mide y quien registra y verifica los cálculos. Antes de energizar cualquier montaje, el docente o el monitor revisa la conexión. Cada etapa abre con su diagrama de flujo, que muestra la secuencia y las comprobaciones de un vistazo, y sigue con sus pasos numerados; cada paso indica cuánto dura, qué debe observarse para saber que salió bien y qué hacer si no. Los valores numéricos de la sesión teórica sirven de referencia: las lecturas propias del grupo se registran en las tablas de la sección de análisis.

> Los diagramas de flujo, los circuitos y las gráficas son código LaTeX (TikZ, circuitikz y pgfplots), como en el .tex: Obsidian los dibuja con el plugin TikZJax; sin él, se ve el código (el PDF de la guía los trae dibujados).

### 3.1 Preparación y predicción (29 min)

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
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n0) at (0.689,-0.340) {Inicio de \\ la etapa};  % ini
  \node[dcaja, minimum width=1.177in, minimum height=0.680in] (n1) at (2.685,-0.340) {Descargar \\ C2};  % a0
  \node[dcaja, minimum width=1.363in, minimum height=0.680in] (n2) at (4.877,-0.340) {Verificar \\ componentes};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n3) at (7.014,-0.340) {Calcular \\ fr, Q y AB};  % a2
  \node[dcaja, minimum width=1.177in, minimum height=0.680in] (n4) at (7.014,-1.808) {Montar el \\ filtro};  % a3
  \node[ddecision, minimum width=1.766in, minimum height=1.156in] (n5) at (4.877,-1.808) {\textquestiondown{}Montaje \\ revisado?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n6) at (2.685,-1.808) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) to[bend right=24] (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n4);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (3.781,-1.808) {s\'{\i}};
  \node[drotulo] at (6.159,-2.116) {no};
\end{tikzpicture}
\end{document}
```

*Figura 1. Diagrama de flujo de la etapa 1: Preparación y predicción*

1. Descargar el condensador conectando entre sus terminales, durante unos segundos, una resistencia de 1 kΩ sujeta con pinzas aisladas, y medir con el voltímetro en cd la tensión entre terminales. *(≈ 3 min)* **Comprobación:** La tensión debe ser prácticamente nula (menos de 0,1 V); si no lo es, repetir la descarga antes de manipular el componente. **Seguridad:** No cortocircuitar los terminales con los dedos ni con una herramienta metálica: un condensador puede conservar carga después de desconectado.
2. Verificar el resistor con el ohmímetro, la bobina L3 con el medidor LCR y el ohmímetro (10,4 mH y 24,6 Ω esperados) y el condensador C2 con el medidor LCR (97,8 nF esperados). *(≈ 8 min)* **Comprobación:** Si algún valor difiere más que su tolerancia del registrado, anotar el nuevo valor y rehacer el cálculo previo con él.
3. Calcular con los valores medidos la frecuencia de resonancia, el factor de calidad con la resistencia total del lazo $R + R_W$, las frecuencias de corte y el ancho de banda $AB = f_r/Q$. *(≈ 12 min)* **Comprobación:** Deben obtenerse $f_r$ cerca de 4990 Hz, Q cerca de 2,6 y un ancho de banda cercano a 1900 Hz.
4. Montar en serie el resistor, L3 y C2, con el resistor del lado de tierra para medir en él la salida. *(≈ 6 min)* **Comprobación:** El docente revisa el montaje antes de energizar. **Seguridad:** Montar con el generador apagado.

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
\draw (0,0) to[sV, l=$v_{ent}$] (0,3) to[L, l=$L_3$] (3,3) to[C, l=$C_2$] (6,3) to[R, l_=$R$, v^=$v_{sal}$] (6,0) -- (0,0); \draw (0,0) node[ground]{};
\end{circuitikz}
\end{document}
```

*Figura 2. Filtro pasabanda RLC en serie con la salida en el resistor*


### 3.2 Resonancia del filtro (22 min)

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
  \node[dcaja, minimum width=1.177in, minimum height=0.680in] (n1) at (3.019,-0.445) {Ajustar 5 \\ kHz y 2 V};  % a0
  \node[dcaja, minimum width=1.363in, minimum height=0.890in] (n2) at (5.343,-0.445) {Barrer \\ buscando el \\ m\'{a}ximo};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n3) at (5.343,-2.018) {Afinar por \\ fase};  % a2
  \node[ddecision, minimum width=2.045in, minimum height=1.156in] (n4) at (3.019,-2.018) {\textquestiondown{}M\'{a}ximo \\ localizado?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n5) at (0.689,-2.018) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.621,-2.018) {s\'{\i}};
  \node[drotulo] at (4.417,-1.580) {no};
\end{tikzpicture}
\end{document}
```

*Figura 3. Diagrama de flujo de la etapa 2: Resonancia del filtro*

5. Ajustar el generador a una onda sinusoidal de 5 kHz y medir con el osciloscopio y con el multímetro de verdadero valor eficaz que la tensión en los bornes del circuito, con el circuito conectado, sea de 2,00 V eficaces. *(≈ 6 min)* **Comprobación:** El multímetro debe indicar 2,00 V y el osciloscopio una sinusoide sin distorsión; si la tensión baja al conectar el circuito, reajustar la amplitud con el circuito conectado.
6. Barrer la frecuencia buscando el máximo de la tensión en el resistor, reajustando la entrada a 2,00 V eficaces a cada frecuencia. *(≈ 8 min)* **Comprobación:** El máximo debe estar cerca de 5 kHz y por debajo de 2,00 V por la resistencia de devanado.
7. Afinar la resonancia por fase con el osciloscopio (tensión del resistor en fase con la de la fuente) y anotar $f_r$ y la tensión de salida máxima. *(≈ 8 min)* **Comprobación:** La tensión de salida máxima esperada es cercana a 1,60 V.

### 3.3 Frecuencias de corte y ancho de banda (28 min)

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
  \node[dterminal, minimum width=2.214in, minimum height=0.470in] (n0) at (1.301,-0.340) {Inicio de la etapa};  % ini
  \node[dcaja, minimum width=2.014in, minimum height=0.680in] (n1) at (4.229,-0.340) {Calcular nivel del \\ 70,7 \%};  % a0
  \node[dcaja, minimum width=1.084in, minimum height=0.470in] (n2) at (6.399,-0.340) {Medir f1};  % a1
  \node[dcaja, minimum width=1.084in, minimum height=0.470in] (n3) at (6.399,-1.629) {Medir f2};  % a2
  \node[dcaja, minimum width=1.735in, minimum height=0.470in] (n4) at (4.229,-1.629) {Calcular AB y Q};  % a3
  \node[ddecision, minimum width=2.603in, minimum height=0.799in] (n5) at (1.301,-1.629) {\textquestiondown{}\ensuremath{\surd}(f1\textperiodcentered{}f2) \ensuremath{\approx} fr?};  % dec
  \node[dterminal, minimum width=1.935in, minimum height=0.470in] (n6) at (1.301,-2.814) {Fin de la etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.301,-2.222) {s\'{\i}};
  \node[drotulo] at (2.993,-1.885) {no};
\end{tikzpicture}
\end{document}
```

*Figura 4. Diagrama de flujo de la etapa 3: Frecuencias de corte y ancho de banda*

8. Calcular el 70,7 % de la tensión de salida máxima [1]. *(≈ 2 min)* **Comprobación:** Con 1,60 V de máximo, el nivel de corte es de unos 1,13 V.

```tikz
\usepackage{pgfplots}
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
\pgfplotsset{compat=1.16}
\pgfplotsset{cycle list={{iubblue, mark=*},{iuborange, mark=square*},{iubgreen, mark=triangle*},{iubnavy, mark=diamond*},{iubyellow, mark=pentagon*}}}
\pgfplotsset{iubejes/.style={width=12cm, height=6.2cm, grid=major, grid style={iubgris}, axis lines*=left, axis line style={iubnavy}, tick label style={font=\small}, label style={font=\small}, title style={font=\bfseries\small}, legend cell align=left, legend style={draw=none, fill=none, font=\small, anchor=north, legend columns=-1, /tikz/every even column/.append style={column sep=8pt}}, unbounded coords=jump}}
\begin{tikzpicture}
  \begin{axis}[
      iubejes,
      xlabel={Frecuencia f (Hz)},
      ylabel={Tensi\'{o}n de salida (V)},
      title={Respuesta del filtro pasabanda},
      legend style={at={(0.5,-0.30)}},
      xmin=2000,
      xmax=10000]
    % serie 1: Vsal(f) (<<2*R/sqrt(Rt**2+(2*pi*f*L-1/(2*pi*f*C))**2)>> en 300 puntos)
    \addplot[color=iubblue, line width=1.4pt, no markers] coordinates {
      (2000,0.286674) (2026.76,0.291839) (2053.51,0.297068) (2080.27,0.302363) (2107.02,0.307725) (2133.78,0.313157)
      (2160.54,0.318659) (2187.29,0.324235) (2214.05,0.329886) (2240.8,0.335614) (2267.56,0.341421) (2294.31,0.34731)
      (2321.07,0.353281) (2347.83,0.359338) (2374.58,0.365483) (2401.34,0.371718) (2428.09,0.378046) (2454.85,0.384468)
      (2481.61,0.390989) (2508.36,0.397609) (2535.12,0.404333) (2561.87,0.411162) (2588.63,0.4181) (2615.38,0.425149)
      (2642.14,0.432313) (2668.9,0.439594) (2695.65,0.446997) (2722.41,0.454523) (2749.16,0.462177) (2775.92,0.469961)
      (2802.68,0.47788) (2829.43,0.485937) (2856.19,0.494136) (2882.94,0.50248) (2909.7,0.510974) (2936.45,0.519622)
      (2963.21,0.528428) (2989.97,0.537395) (3016.72,0.546529) (3043.48,0.555833) (3070.23,0.565313) (3096.99,0.574973)
      (3123.75,0.584818) (3150.5,0.594852) (3177.26,0.605081) (3204.01,0.615509) (3230.77,0.626142) (3257.53,0.636985)
      (3284.28,0.648042) (3311.04,0.659321) (3337.79,0.670824) (3364.55,0.682559) (3391.3,0.69453) (3418.06,0.706744)
      (3444.82,0.719204) (3471.57,0.731917) (3498.33,0.744888) (3525.08,0.758122) (3551.84,0.771624) (3578.6,0.785399)
      (3605.35,0.799452) (3632.11,0.813788) (3658.86,0.828409) (3685.62,0.843321) (3712.37,0.858526) (3739.13,0.874027)
      (3765.89,0.889827) (3792.64,0.905927) (3819.4,0.922327) (3846.15,0.939029) (3872.91,0.956031) (3899.67,0.97333)
      (3926.42,0.990923) (3953.18,1.00881) (3979.93,1.02697) (4006.69,1.04541) (4033.44,1.06412) (4060.2,1.08308)
      (4086.96,1.10228) (4113.71,1.1217) (4140.47,1.14132) (4167.22,1.16112) (4193.98,1.18108) (4220.74,1.20117)
      (4247.49,1.22135) (4274.25,1.24158) (4301,1.26184) (4327.76,1.28208) (4354.52,1.30224) (4381.27,1.32228)
      (4408.03,1.34215) (4434.78,1.36178) (4461.54,1.38112) (4488.29,1.4001) (4515.05,1.41865) (4541.81,1.4367)
      (4568.56,1.45418) (4595.32,1.47102) (4622.07,1.48714) (4648.83,1.50248) (4675.59,1.51695) (4702.34,1.5305)
      (4729.1,1.54304) (4755.85,1.55454) (4782.61,1.56491) (4809.36,1.57413) (4836.12,1.58214) (4862.88,1.58891)
      (4889.63,1.59441) (4916.39,1.59863) (4943.14,1.60155) (4969.9,1.60317) (4996.66,1.60351) (5023.41,1.60258)
      (5050.17,1.60041) (5076.92,1.59704) (5103.68,1.5925) (5130.43,1.58684) (5157.19,1.58012) (5183.95,1.5724)
      (5210.7,1.56372) (5237.46,1.55417) (5264.21,1.54381) (5290.97,1.53269) (5317.73,1.5209) (5344.48,1.50849)
      (5371.24,1.49554) (5397.99,1.48209) (5424.75,1.46823) (5451.51,1.45399) (5478.26,1.43945) (5505.02,1.42465)
      (5531.77,1.40965) (5558.53,1.39448) (5585.28,1.37919) (5612.04,1.36383) (5638.8,1.34842) (5665.55,1.33301)
      (5692.31,1.31761) (5719.06,1.30227) (5745.82,1.28699) (5772.58,1.27181) (5799.33,1.25675) (5826.09,1.24182)
      (5852.84,1.22703) (5879.6,1.21241) (5906.35,1.19795) (5933.11,1.18368) (5959.87,1.1696) (5986.62,1.15571)
      (6013.38,1.14202) (6040.13,1.12854) (6066.89,1.11527) (6093.65,1.10222) (6120.4,1.08937) (6147.16,1.07674)
      (6173.91,1.06433) (6200.67,1.05213) (6227.42,1.04014) (6254.18,1.02836) (6280.94,1.0168) (6307.69,1.00545)
      (6334.45,0.994302) (6361.2,0.983359) (6387.96,0.972619) (6414.72,0.962077) (6441.47,0.951731) (6468.23,0.941578)
      (6494.98,0.931614) (6521.74,0.921837) (6548.49,0.912241) (6575.25,0.902825) (6602.01,0.893585) (6628.76,0.884517)
      (6655.52,0.875618) (6682.27,0.866884) (6709.03,0.858313) (6735.79,0.849899) (6762.54,0.841641) (6789.3,0.833534)
      (6816.05,0.825575) (6842.81,0.817762) (6869.57,0.81009) (6896.32,0.802558) (6923.08,0.79516) (6949.83,0.787896)
      (6976.59,0.78076) (7003.34,0.773752) (7030.1,0.766867) (7056.86,0.760102) (7083.61,0.753456) (7110.37,0.746926)
      (7137.12,0.740508) (7163.88,0.7342) (7190.64,0.728) (7217.39,0.721905) (7244.15,0.715913) (7270.9,0.710021)
      (7297.66,0.704228) (7324.41,0.698531) (7351.17,0.692927) (7377.93,0.687415) (7404.68,0.681993) (7431.44,0.676658)
      (7458.19,0.671409) (7484.95,0.666243) (7511.71,0.66116) (7538.46,0.656157) (7565.22,0.651231) (7591.97,0.646383)
      (7618.73,0.641609) (7645.48,0.636909) (7672.24,0.63228) (7699,0.627722) (7725.75,0.623232) (7752.51,0.618809)
      (7779.26,0.614452) (7806.02,0.610159) (7832.78,0.605929) (7859.53,0.601761) (7886.29,0.597653) (7913.04,0.593604)
      (7939.8,0.589613) (7966.56,0.585679) (7993.31,0.5818) (8020.07,0.577976) (8046.82,0.574204) (8073.58,0.570485)
      (8100.33,0.566818) (8127.09,0.5632) (8153.85,0.559631) (8180.6,0.556111) (8207.36,0.552637) (8234.11,0.54921)
      (8260.87,0.545828) (8287.63,0.542491) (8314.38,0.539197) (8341.14,0.535946) (8367.89,0.532737) (8394.65,0.529569)
      (8421.4,0.526442) (8448.16,0.523354) (8474.92,0.520305) (8501.67,0.517294) (8528.43,0.514321) (8555.18,0.511384)
      (8581.94,0.508483) (8608.7,0.505618) (8635.45,0.502787) (8662.21,0.499991) (8688.96,0.497228) (8715.72,0.494498)
      (8742.47,0.491801) (8769.23,0.489135) (8795.99,0.4865) (8822.74,0.483896) (8849.5,0.481322) (8876.25,0.478778)
      (8903.01,0.476263) (8929.77,0.473776) (8956.52,0.471318) (8983.28,0.468887) (9010.03,0.466483) (9036.79,0.464106)
      (9063.55,0.461756) (9090.3,0.459431) (9117.06,0.457131) (9143.81,0.454856) (9170.57,0.452606) (9197.32,0.450381)
      (9224.08,0.448178) (9250.84,0.446) (9277.59,0.443844) (9304.35,0.441711) (9331.1,0.4396) (9357.86,0.437511)
      (9384.62,0.435444) (9411.37,0.433398) (9438.13,0.431373) (9464.88,0.429368) (9491.64,0.427384) (9518.39,0.425419)
      (9545.15,0.423475) (9571.91,0.421549) (9598.66,0.419643) (9625.42,0.417755) (9652.17,0.415886) (9678.93,0.414035)
      (9705.69,0.412203) (9732.44,0.410387) (9759.2,0.40859) (9785.95,0.406809) (9812.71,0.405045) (9839.46,0.403298)
      (9866.22,0.401567) (9892.98,0.399853) (9919.73,0.398154) (9946.49,0.396472) (9973.24,0.394804) (10000,0.393152)
    };
    \addlegendentry{Vsal(f)}
    % l\'{\i}nea de referencia en y = 1.13
    \draw[iubgrisoscuro, dashed, line width=0.9pt] ({rel axis cs:0,0}|-{axis cs:0,1.13}) -- ({rel axis cs:1,0}|-{axis cs:0,1.13}) node[drotulo, pos=1, anchor=south east] {70,7 \% del m\'{a}ximo};
  \end{axis}
\end{tikzpicture}
\end{document}
```

*Figura 5. Respuesta esperada del filtro con R = 99,5 Ω, RW = 24,6 Ω, L = 10,4 mH y C = 97,8 nF (2,00 V a la entrada)*

9. Bajar la frecuencia desde $f_r$ hasta que la salida caiga a ese nivel, reajustando la entrada, y anotar $f_1$. *(≈ 10 min)* **Comprobación:** $f_1$ debe estar cerca de 4,1 kHz.
10. Subir la frecuencia desde $f_r$ hasta el mismo nivel y anotar $f_2$. *(≈ 10 min)* **Comprobación:** $f_2$ debe estar cerca de 6,0 kHz.
11. Calcular $AB = f_2 - f_1$, $Q = f_r/AB$ y la comprobación $\sqrt{f_1 f_2}$, que debe coincidir con $f_r$. *(≈ 6 min)* **Comprobación:** Si $\sqrt{f_1 f_2}$ se aparta más del 2 % de $f_r$, repetir la medición de la frecuencia de corte más dudosa.

**Ecuación (1).** Ancho de banda y factor de calidad del filtro:

$$
AB = f_2 - f_1, \qquad Q = \frac{f_r}{AB} \tag{1}
$$

donde $AB$, $f_1$, $f_2$ y $f_r$ en hercios (Hz); $Q$ adimensional.


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

*Figura 6. Diagrama de flujo de la etapa 4: Desmontaje y cierre*

12. Apagar el generador de funciones y la fuente, desconectar las puntas del osciloscopio y retirar la alimentación del protoboard. *(≈ 3 min)* **Comprobación:** Ningún indicador de salida debe quedar encendido en el generador ni en la fuente. **Seguridad:** Desenergizar siempre antes de retirar componentes.
13. Descargar los condensadores del montaje con la resistencia de descarga, retirar los componentes y devolverlos al kit del grupo con su rótulo. *(≈ 4 min)* **Comprobación:** El kit debe quedar completo, con cada componente en su lugar y con su valor medido anotado.
14. Revisar con el docente las tablas de registro antes de abandonar el banco. *(≈ 3 min)* **Comprobación:** Las tablas deben estar completas y con unidades; si falta un dato, repetir esa medición antes de desmontar el instrumento.

## 4. Cuestiones a Resolver

1. ¿Por qué la tensión de salida en la resonancia no alcanza la tensión de la fuente?
2. ¿Qué diferencia hay entre el factor de calidad medido y el que predice el cálculo ideal con valores nominales, y a qué se debe?
3. ¿Qué ocurriría con el ancho de banda si la tensión se fijara en el dial del generador y no en los bornes del circuito?
4. ¿Qué componente habría que cambiar para hacer el filtro más selectivo, y en qué sentido?
5. ¿Por qué $\sqrt{f_1 f_2}$ sirve para comprobar la coherencia de las tres frecuencias medidas?

## 5. Análisis de Resultados

Presentar en la tabla de registro los parámetros del filtro calculados de forma ideal con valores nominales, calculados con valores medidos y resistencia de devanado, y medidos, con la diferencia porcentual respecto del cálculo con valores medidos.

Registrar la tensión de salida a unas diez frecuencias entre 2 kHz y 10 kHz y graficarla contra la frecuencia en escala logarítmica, marcando $f_r$, $f_1$, $f_2$ y el nivel del 70,7 %.

**Tabla 2.** Parámetros del filtro pasabanda RLC en serie

| Parámetro | Ideal nominal | Cálculo con medidos | Medido | Unidad | Diferencia (%) |
|---|---|---|---|---|---|
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |

**Tabla 3.** Respuesta en frecuencia del filtro

| Frecuencia (kHz) | Vent (V) | Vsal (V) | Vsal/Vent |
|---|---|---|---|
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |
|   |   |   |   |

## 6. Conclusiones

Concluir si los parámetros medidos del filtro coinciden con el cálculo que usa los valores medidos y la resistencia de devanado, y por qué el cálculo ideal se aparta; relacionar la práctica con los criterios de medición en circuitos RLC del RA y con la selección de componentes de un filtro.

- ¿Qué parámetro del filtro fue más sensible a la resistencia de devanado?
- ¿Qué tan coherentes resultaron las tres frecuencias medidas?
- ¿Qué cambio de componentes propondrían para estrechar el ancho de banda?

## 7. Recomendaciones de Seguridad

- Trabajar con el circuito desenergizado mientras se conecta o modifica el montaje; energizar solo después de la revisión del docente.
- Mantener la tensión de la fuente en 2,00 V eficaces: en la resonancia en serie la tensión en la bobina y en el condensador supera varias veces la de la fuente [1].
- Conectar las tierras de las dos puntas del osciloscopio a un mismo nodo de referencia: unirlas a nodos distintos cortocircuita el elemento que queda entre ellas.

## 8. Bibliografía

[1] Floyd, Thomas L., *Principios de circuitos eléctricos*, 8.ª ed., Pearson Educación, 2007.

[2] Boylestad, Robert L., *Introducción al análisis de circuitos*, 10.ª ed., Pearson Educación, 2004.

[3] Deorsola, M. F. P., Morcelle del Valle, P., *Circuitos eléctricos. Parte 1*, 1.ª ed., Editorial de la Universidad de La Plata, 2017.
