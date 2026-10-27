---
tipo: guia_laboratorio
asignatura: '[[IEL04 - Circuitos Eléctricos I]]'
resultado_aprendizaje: '[[IEL04-RA3]]'
temario: '[[IEL04-semana08]]'
semana: 8
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
archivo_tex: generacion/guias-laboratorio/IEL04/IEL04-semana08.tex
temario_hash: efd5d71cab75822d
huella: 4ec300fdabe61126
formato: 3
docente: Ing. Sergio Martinez Castilla
facultad: Facultad de Ingenierías
compilada: '2026-10-27'
fecha_creacion: '2026-10-25'
fecha_actualizacion: '2026-10-27'
---
# Guía de laboratorio: Circuitos RL en serie y en paralelo con la bobina real: tensiones, corrientes y ángulos a 10 kHz

> **Facultad:** Facultad de Ingenierías · **Módulo:** IEL04 — Circuitos Eléctricos I · **Docente:** Ing. Sergio Martinez Castilla
> **Semana:** 8 de 14 · **Resultado de aprendizaje:** [[IEL04-RA3]] · **Sesión:** [[IEL04-semana08]] · **Práctica:** propuesta a partir de la bibliografía [1] [2] [3] · **Duración:** 240 minutos

La práctica corresponde a la sesión teórica de la semana 8, «Circuitos RL en serie y en paralelo: reactancia inductiva, impedancia y leyes de Kirchhoff con la bobina real», y reproduce su caso de estudio: con la bobina L3 del kit y un resistor de 680 Ω se miden, a 10 kHz y 5,00 V eficaces, las tensiones y el ángulo del circuito en serie y las corrientes y el ángulo del circuito en paralelo, y se comparan con el cálculo que incluye la resistencia de devanado y con el cálculo ideal. No hay un manual de laboratorio asignado al RA IEL04-RA3, por lo que la práctica se propone a partir de la bibliografía cargada: Floyd trata la reactancia inductiva y el análisis de circuitos RL en serie y en paralelo [1], Boylestad los circuitos de ca R-L [2] y Deorsola el circuito RL y las leyes de Kirchhoff con fasores [3].

## 1. Objetivos

**Objetivo general:** Verificar experimentalmente las leyes de Kirchhoff en circuitos RL en serie y en paralelo con una bobina real.

**Objetivos específicos:**

- Identificar y verificar con instrumentos la bobina y el resistor del circuito, incluida la resistencia de devanado. *(CE1)*
- Medir las tensiones en el resistor y en la bobina, y las corrientes de rama, con el multímetro de verdadero valor eficaz. *(CE2)*
- Medir el ángulo de fase de los circuitos RL en serie y en paralelo, y compararlo con el cálculo con resistencia de devanado y con el cálculo ideal. *(CE3)*

## 2. Materiales y Equipos

**Tabla 1.** Materiales y equipos de la práctica

| # | Material o equipo | Especificación | Cantidad |
|---|---|---|---|
| 1 | Bobina L3 del kit | 103K, 10,4 mH y 24,6 Ω medidos | 1 |
| 2 | Resistor | 680 Ω | 1 |
| 3 | Resistor sensor de corriente | 10 Ω | 1 |
| 4 | Generador de funciones | — | 1 |
| 5 | Osciloscopio de dos canales con puntas ×10 | — | 1 |
| 6 | Multímetro digital de verdadero valor eficaz | — | 2 |
| 7 | Medidor LCR | — | 1 |
| 8 | Protoboard | — | 1 |
| 9 | Cables de conexión | — | 12 |

## 3. Procedimiento

La práctica ocupa el bloque de 2 h de laboratorio de la sesión y se realiza en grupos de tres estudiantes, con tres roles que rotan entre etapas: quien monta y opera el circuito, quien mide y quien registra y verifica los cálculos. Antes de energizar cualquier montaje, el docente o el monitor revisa la conexión. Cada etapa abre con su diagrama de flujo, que muestra la secuencia y las comprobaciones de un vistazo, y sigue con sus pasos numerados; cada paso indica cuánto dura, qué debe observarse para saber que salió bien y qué hacer si no. Los valores numéricos de la sesión teórica sirven de referencia: las lecturas propias del grupo se registran en las tablas de la sección de análisis.

> Los diagramas de flujo, los circuitos y las gráficas son código LaTeX (TikZ, circuitikz y pgfplots), como en el .tex: Obsidian los dibuja con el plugin TikZJax; sin él, se ve el código (el PDF de la guía los trae dibujados).

### 3.1 Preparación y cálculo previo (18 min)

1. Verificar la bobina L3 con el medidor LCR (inductancia) y el ohmímetro (resistencia de devanado), y el resistor de 680 Ω con el ohmímetro. *(≈ 6 min)* **Comprobación:** L3 debe leer cerca de 10,4 mH y 24,6 Ω, y el resistor cerca de 676 Ω; si no, anotar los valores nuevos para los cálculos.
2. Calcular a 10 kHz la reactancia $X_L = 2\pi f L$, la impedancia del circuito en serie con y sin la resistencia de devanado, y las corrientes del circuito en paralelo. *(≈ 12 min)* **Comprobación:** Debe obtenerse $X_L$ cerca de 653 Ω y una corriente en serie cerca de 5,2 mA.

**Ecuación (1).** Reactancia inductiva e impedancia del RL en serie con la bobina real:

$$
X_L = 2\pi f L, \qquad Z = \sqrt{(R + R_W)^2 + X_L^2} \tag{1}
$$

donde $X_L$ y $Z$ en ohmios (Ω), $f$ en Hz, $L$ en H, $R$ y $R_W$ en Ω.


### 3.2 Circuito RL en serie (27 min)

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
  \node[dcaja, minimum width=1.363in, minimum height=0.890in] (n1) at (2.685,-0.445) {Montar R en \\ serie con \\ L3};  % a0
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n2) at (4.877,-0.445) {Ajustar 10 \\ kHz y 5 V};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n3) at (7.014,-0.445) {Medir VR y \\ Vbob};  % a2
  \node[dcaja, minimum width=0.991in, minimum height=0.680in] (n4) at (7.014,-2.196) {Medir \\ desfase};  % a3
  \node[ddecision, minimum width=1.766in, minimum height=1.513in] (n5) at (4.877,-2.196) {\textquestiondown{}Coincide \\ con el \\ c\'{a}lculo?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n6) at (2.685,-2.196) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n3);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (3.781,-2.196) {s\'{\i}};
  \node[drotulo] at (6.208,-1.641) {no};
\end{tikzpicture}
\end{document}
```

*Figura 1. Diagrama de flujo de la etapa 2: Circuito RL en serie*

3. Montar el resistor en serie con L3, con la bobina del lado de tierra. *(≈ 5 min)* **Comprobación:** El docente revisa el montaje antes de energizar. **Seguridad:** Montar con el generador apagado.

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
\draw (0,0) to[sV, l=$v_s$] (0,3) to[R, l_=$R$, v^=$v_R$] (4,3) to[L, l=$L_3$] (4,1.5) to[R, l=$R_W$] (4,0) -- (0,0); \draw (0,0) node[ground]{};
\end{circuitikz}
\end{document}
```

*Figura 2. Circuito RL en serie con la bobina real (inductancia y resistencia de devanado)*

4. Ajustar el generador a una onda sinusoidal de 10 kHz y medir con el osciloscopio y con el multímetro de verdadero valor eficaz que la tensión en los bornes del circuito, con el circuito conectado, sea de 5,00 V eficaces. *(≈ 6 min)* **Comprobación:** El multímetro debe indicar 5,00 V y el osciloscopio una sinusoide sin distorsión; si la tensión baja al conectar el circuito, reajustar la amplitud con el circuito conectado.
5. Medir con el multímetro de verdadero valor eficaz la tensión en el resistor y la tensión entre los terminales de la bobina. *(≈ 8 min)* **Comprobación:** Las lecturas deben estar cerca de 3,53 V y 3,41 V; su suma aritmética supera 5 V.
6. Medir con el osciloscopio el desfase entre la tensión de la fuente y la del resistor y calcular el ángulo. *(≈ 8 min)* **Comprobación:** La corriente debe atrasar a la tensión unos 43°; si el ángulo se acerca a 44°, comprobar si se omitió la resistencia de devanado en el cálculo.

### 3.3 Circuito RL en paralelo (28 min)

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
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n1) at (2.685,-0.445) {Montar \\ paralelo \\ con sensor};  % a0
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n2) at (4.877,-0.445) {Medir \\ corrientes \\ de rama};  % a1
  \node[dcaja, minimum width=1.084in, minimum height=0.470in] (n3) at (6.921,-0.445) {Medir IT};  % a2
  \node[dcaja, minimum width=0.991in, minimum height=0.680in] (n4) at (6.921,-2.196) {Medir \\ desfase};  % a3
  \node[ddecision, minimum width=1.766in, minimum height=1.513in] (n5) at (4.877,-2.196) {\textquestiondown{}IT menor \\ que la \\ suma?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n6) at (2.685,-2.196) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (3.781,-2.196) {s\'{\i}};
  \node[drotulo] at (5.129,-1.146) {no};
\end{tikzpicture}
\end{document}
```

*Figura 3. Diagrama de flujo de la etapa 3: Circuito RL en paralelo*

7. Desenergizar y montar el resistor y L3 en paralelo, con el resistor sensor en serie con la fuente del lado de tierra. *(≈ 6 min)* **Comprobación:** El docente revisa el montaje. **Seguridad:** Desenergizar antes de modificar el montaje.

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
\draw (0,0) to[sV, l=$v_s$] (0,3) to[ammeter, l=$I_T$] (3,3) to[R, l=$R$] (3,0) -- (0,0); \draw (3,3) -- (6,3) to[L, l=$L_3$] (6,0) -- (3,0); \draw (0,0) node[ground]{};
\end{circuitikz}
\end{document}
```

*Figura 4. Circuito RL en paralelo con el amperímetro en serie con la fuente*

8. Con el circuito desenergizado, insertar el amperímetro en cada rama y en serie con la fuente, energizando para cada lectura, y anotar $I_R$, $I_{bob}$ e $I_T$. *(≈ 15 min)* **Comprobación:** Las lecturas deben estar cerca de 7,40 mA, 7,65 mA y 10,8 mA; $I_T$ debe ser menor que la suma aritmética.
9. Medir con el osciloscopio el desfase entre la tensión de la fuente y la del resistor sensor. *(≈ 7 min)* **Comprobación:** La corriente total debe atrasar a la tensión unos 45°.

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

10. Apagar el generador de funciones y la fuente, desconectar las puntas del osciloscopio y retirar la alimentación del protoboard. *(≈ 3 min)* **Comprobación:** Ningún indicador de salida debe quedar encendido en el generador ni en la fuente. **Seguridad:** Desenergizar siempre antes de retirar componentes.
11. Descargar los condensadores del montaje con la resistencia de descarga, retirar los componentes y devolverlos al kit del grupo con su rótulo. *(≈ 4 min)* **Comprobación:** El kit debe quedar completo, con cada componente en su lugar y con su valor medido anotado.
12. Revisar con el docente las tablas de registro antes de abandonar el banco. *(≈ 3 min)* **Comprobación:** Las tablas deben estar completas y con unidades; si falta un dato, repetir esa medición antes de desmontar el instrumento.

## 4. Cuestiones a Resolver

1. ¿En qué circuito, serie o paralelo, pesa más la resistencia de devanado de la bobina, y por qué?
2. ¿Cuánto se apartan las mediciones del cálculo ideal y cuánto del cálculo con resistencia de devanado?
3. ¿Por qué la tensión medida en la bobina no está adelantada exactamente 90° respecto de la corriente?
4. ¿Cómo cambiaría el efecto de la resistencia de devanado si la práctica se hiciera a 1 kHz en lugar de 10 kHz?

## 5. Análisis de Resultados

Presentar en la tabla de registro, para cada magnitud de los dos circuitos, el cálculo con resistencia de devanado, el cálculo ideal, la medición y la diferencia porcentual con el primero.

Dibujar el diagrama fasorial de tensiones del circuito en serie, con la tensión de la bobina real formada por su caída resistiva y su caída reactiva, y el de corrientes del circuito en paralelo; comprobar ambas sumas con las lecturas.

**Tabla 2.** Circuito RL en serie a 10 kHz

| Magnitud | Cálculo con RW | Cálculo ideal | Medido | Unidad | Diferencia (%) |
|---|---|---|---|---|---|
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |

**Tabla 3.** Circuito RL en paralelo a 10 kHz

| Magnitud | Cálculo con RW | Cálculo ideal | Medido | Unidad | Diferencia (%) |
|---|---|---|---|---|---|
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |

## 6. Conclusiones

Concluir si las leyes de Kirchhoff se cumplen en forma fasorial en los dos circuitos y cuál de los dos modelos de la bobina (real o ideal) reproduce mejor las mediciones, explicando el papel de la resistencia de devanado; relacionar la práctica con los criterios de medición en circuitos resistivos, inductivos y RL del RA.

- ¿Qué modelo de la bobina explicó mejor los ángulos medidos?
- ¿Qué diferencia hubo entre el comportamiento en serie y en paralelo?
- ¿Qué precaución del montaje fue determinante?

## 7. Recomendaciones de Seguridad

- Conectar las tierras de las dos puntas del osciloscopio a un mismo nodo de referencia: unirlas a nodos distintos cortocircuita el elemento que queda entre ellas.
- Insertar el amperímetro en serie con la rama solo con el circuito desenergizado y con el instrumento en la función y la escala de corriente; nunca conectarlo en paralelo con la fuente.
- Desenergizar antes de cambiar del montaje en serie al montaje en paralelo.
- No interrumpir bruscamente la corriente de la bobina con el circuito energizado.

## 8. Bibliografía

[1] Floyd, Thomas L., *Principios de circuitos eléctricos*, 8.ª ed., Pearson Educación, 2007.

[2] Boylestad, Robert L., *Introducción al análisis de circuitos*, 10.ª ed., Pearson Educación, 2004.

[3] Deorsola, M. F. P., Morcelle del Valle, P., *Circuitos eléctricos. Parte 1*, 1.ª ed., Editorial de la Universidad de La Plata, 2017.
