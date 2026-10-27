---
tipo: guia_laboratorio
asignatura: '[[IEL04 - Circuitos Eléctricos I]]'
resultado_aprendizaje: '[[IEL04-RA4]]'
temario: '[[IEL04-semana12]]'
semana: 12
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
archivo_tex: generacion/guias-laboratorio/IEL04/IEL04-semana12.tex
temario_hash: 379688a119f6262f
huella: 9090718159c5591e
formato: 3
docente: Ing. Sergio Martinez Castilla
facultad: Facultad de Ingenierías
compilada: '2026-10-27'
fecha_creacion: '2026-10-25'
fecha_actualizacion: '2026-10-27'
---
# Guía de laboratorio: Circuito RLC en paralelo: corrientes de rama, corriente mínima en la resonancia y circuito tanque con bobina real

> **Facultad:** Facultad de Ingenierías · **Módulo:** IEL04 — Circuitos Eléctricos I · **Docente:** Ing. Sergio Martinez Castilla
> **Semana:** 12 de 14 · **Resultado de aprendizaje:** [[IEL04-RA4]] · **Sesión:** [[IEL04-semana12]] · **Práctica:** propuesta a partir de la bibliografía [1] [2] [3] · **Duración:** 240 minutos

La práctica corresponde a la sesión teórica de la semana 12, «El circuito RLC en paralelo: susceptancias opuestas, ley de corrientes de Kirchhoff, circuito tanque y corrección del factor de potencia», y reproduce su caso de estudio: con un resistor de 4,7 kΩ, la bobina L3 y el condensador C2 en paralelo, alimentados con 2,00 V eficaces, se miden las corrientes de rama y la corriente total a 3 kHz, en la resonancia y a 8 kHz, y se observa que en la resonancia la fuente entrega una corriente mínima mientras por la bobina y el condensador circula una corriente mucho mayor. No hay un manual de laboratorio asignado al RA IEL04-RA4, por lo que la práctica se propone a partir de la bibliografía cargada: Floyd trata el análisis y la resonancia en paralelo, incluido el tanque con bobina no ideal [1], Boylestad el circuito resonante en paralelo con la resistencia de la bobina [2] y Deorsola la ley de corrientes de Kirchhoff con fasores [3].

## 1. Objetivos

**Objetivo general:** Verificar experimentalmente la ley de corrientes de Kirchhoff y la resonancia en un circuito RLC en paralelo con bobina real.

**Objetivos específicos:**

- Identificar por su código de colores el resistor y verificar con instrumentos el resistor, la bobina y el condensador. *(CE1)*
- Medir las corrientes de las ramas resistiva, inductiva y capacitiva a tres frecuencias. *(CE2)*
- Medir la corriente total del circuito RLC en paralelo, localizar su mínimo en la resonancia y compararlo con el cálculo con la bobina real. *(CE3)*

## 2. Materiales y Equipos

**Tabla 1.** Materiales y equipos de la práctica

| # | Material o equipo | Especificación | Cantidad |
|---|---|---|---|
| 1 | Resistor | 4,7 kΩ ±5 % (amarillo-violeta-rojo-oro) | 1 |
| 2 | Bobina L3 del kit | 103K, 10,4 mH y 24,6 Ω medidos | 1 |
| 3 | Condensador C2 del kit | 104K, 97,8 nF medidos | 1 |
| 4 | Resistor sensor de corriente | 10 Ω | 1 |
| 5 | Generador de funciones | — | 1 |
| 6 | Osciloscopio de dos canales con puntas ×10 | — | 1 |
| 7 | Multímetro digital de verdadero valor eficaz | — | 2 |
| 8 | Medidor LCR | — | 1 |
| 9 | Protoboard | — | 1 |
| 10 | Cables de conexión | — | 12 |
| 11 | Resistencia de descarga | 1 kΩ | 1 |

## 3. Procedimiento

La práctica ocupa el bloque de 2 h de laboratorio de la sesión y se realiza en grupos de tres estudiantes, con tres roles que rotan entre etapas: quien monta y opera el circuito, quien mide y quien registra y verifica los cálculos. Antes de energizar cualquier montaje, el docente o el monitor revisa la conexión. Cada etapa abre con su diagrama de flujo, que muestra la secuencia y las comprobaciones de un vistazo, y sigue con sus pasos numerados; cada paso indica cuánto dura, qué debe observarse para saber que salió bien y qué hacer si no. Los valores numéricos de la sesión teórica sirven de referencia: las lecturas propias del grupo se registran en las tablas de la sección de análisis.

> Los diagramas de flujo, los circuitos y las gráficas son código LaTeX (TikZ, circuitikz y pgfplots), como en el .tex: Obsidian los dibuja con el plugin TikZJax; sin él, se ve el código (el PDF de la guía los trae dibujados).

### 3.1 Preparación y predicción (35 min)

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
  \node[dterminal, minimum width=2.214in, minimum height=0.470in] (n0) at (1.510,-0.340) {Inicio de la etapa};  % ini
  \node[dcaja, minimum width=1.921in, minimum height=0.680in] (n1) at (4.601,-0.340) {Identificar R por \\ colores};  % a0
  \node[dcaja, minimum width=1.363in, minimum height=0.680in] (n2) at (6.864,-0.340) {Descargar y \\ verificar};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n3) at (6.864,-1.629) {Calcular \\ corrientes};  % a2
  \node[dcaja, minimum width=1.735in, minimum height=0.680in] (n4) at (4.601,-1.629) {Montar las tres \\ ramas};  % a3
  \node[ddecision, minimum width=3.021in, minimum height=0.799in] (n5) at (1.510,-1.629) {\textquestiondown{}Montaje revisado?};  % dec
  \node[dterminal, minimum width=1.935in, minimum height=0.470in] (n6) at (1.510,-2.814) {Fin de la etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) to[bend right=24] (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n4);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.510,-2.222) {s\'{\i}};
  \node[drotulo] at (3.365,-2.075) {no};
\end{tikzpicture}
\end{document}
```

*Figura 1. Diagrama de flujo de la etapa 1: Preparación y predicción*

1. Identificar el resistor por su código de colores (amarillo-violeta-rojo-oro: 4,7 kΩ ±5 %) [1]. *(≈ 3 min)* **Comprobación:** Si no da 4,7 kΩ, revisar el sentido de lectura.
2. Descargar el condensador conectando entre sus terminales, durante unos segundos, una resistencia de 1 kΩ sujeta con pinzas aisladas, y medir con el voltímetro en cd la tensión entre terminales. *(≈ 3 min)* **Comprobación:** La tensión debe ser prácticamente nula (menos de 0,1 V); si no lo es, repetir la descarga antes de manipular el componente. **Seguridad:** No cortocircuitar los terminales con los dedos ni con una herramienta metálica: un condensador puede conservar carga después de desconectado.
3. Verificar el resistor con el ohmímetro, la bobina L3 con el medidor LCR y el ohmímetro (10,4 mH y 24,6 Ω esperados) y el condensador C2 con el medidor LCR (97,8 nF esperados). *(≈ 8 min)* **Comprobación:** Si algún valor difiere más que su tolerancia del registrado, anotar el nuevo valor y rehacer el cálculo previo con él.
4. Calcular con los valores medidos la corriente de cada rama y la corriente total a 3 kHz, en la resonancia y a 8 kHz, sumando las admitancias en forma rectangular con la bobina real. *(≈ 15 min)* **Comprobación:** En la resonancia la corriente total esperada es cercana a 0,89 mA, muy inferior a la de la bobina o el condensador (unos 6,1 mA).

**Ecuación (1).** Resistencia equivalente en paralelo de la bobina real:

$$
R_{p(eq)} = R_W \left(Q^2 + 1\right) \tag{1}
$$

donde $R_{p(eq)}$ y $R_W$ en ohmios (Ω); $Q = X_L / R_W$ adimensional.

5. Montar las tres ramas en paralelo y el resistor sensor en serie con la fuente del lado de tierra. *(≈ 6 min)* **Comprobación:** El docente revisa el montaje antes de energizar. **Seguridad:** Montar con el generador apagado.

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
\draw (0,0) to[sV, l=$v_s$] (0,3) to[ammeter, l=$I_T$] (3,3) to[R, l=$R$] (3,0) -- (0,0); \draw (3,3) -- (5.5,3) to[L, l=$L_3$] (5.5,0) -- (3,0); \draw (5.5,3) -- (8,3) to[C, l=$C_2$] (8,0) -- (5.5,0); \draw (0,0) node[ground]{};
\end{circuitikz}
\end{document}
```

*Figura 2. Circuito RLC en paralelo con el amperímetro en serie con la fuente*


### 3.2 Corrientes a 3 kHz y 8 kHz (33 min)

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
  \node[dcaja, minimum width=1.177in, minimum height=0.680in] (n1) at (2.685,-0.445) {Ajustar 3 \\ kHz y 2 V};  % a0
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n2) at (4.877,-0.445) {Medir \\ corrientes \\ de rama};  % a1
  \node[dcaja, minimum width=1.084in, minimum height=0.470in] (n3) at (7.061,-0.445) {Medir IT};  % a2
  \node[dcaja, minimum width=1.363in, minimum height=0.680in] (n4) at (7.061,-2.018) {Repetir a 8 \\ kHz};  % a3
  \node[ddecision, minimum width=1.766in, minimum height=1.156in] (n5) at (4.877,-2.018) {\textquestiondown{}Car\'{a}cter \\ esperado?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n6) at (2.685,-2.018) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (3.781,-2.018) {s\'{\i}};
  \node[drotulo] at (5.113,-1.232) {no};
\end{tikzpicture}
\end{document}
```

*Figura 3. Diagrama de flujo de la etapa 2: Corrientes a 3 kHz y 8 kHz*

6. Ajustar el generador a una onda sinusoidal de 3 kHz y medir con el osciloscopio y con el multímetro de verdadero valor eficaz que la tensión en los bornes del circuito, con el circuito conectado, sea de 2,00 V eficaces. *(≈ 6 min)* **Comprobación:** El multímetro debe indicar 2,00 V y el osciloscopio una sinusoide sin distorsión; si la tensión baja al conectar el circuito, reajustar la amplitud con el circuito conectado.
7. Con el circuito desenergizado, insertar el amperímetro en cada rama y en serie con la fuente, energizando para cada lectura, y anotar $I_R$, $I_{bob}$, $I_C$ e $I_T$. *(≈ 15 min)* **Comprobación:** A 3 kHz la corriente de la bobina debe superar a la del condensador (carácter inductivo). **Seguridad:** Insertar el amperímetro solo con el circuito desenergizado.
8. Repetir las cuatro lecturas a 8 kHz, reajustando la tensión de la fuente. *(≈ 12 min)* **Comprobación:** A 8 kHz la corriente del condensador debe superar a la de la bobina (carácter capacitivo).

### 3.3 Corriente mínima en la resonancia (20 min)

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
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n1) at (2.950,-0.340) {Barrer la \\ frecuencia};  % a0
  \node[dcaja, minimum width=1.177in, minimum height=0.680in] (n2) at (5.157,-0.340) {Localizar \\ IT m\'{\i}nima};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n3) at (5.157,-1.986) {Medir \\ corrientes \\ de rama};  % a2
  \node[ddecision, minimum width=1.905in, minimum height=1.513in] (n4) at (2.950,-1.986) {\textquestiondown{}IT m\'{\i}nima \\ cerca de 5 \\ kHz?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n5) at (0.689,-1.986) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n1);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.593,-1.986) {s\'{\i}};
  \node[drotulo] at (3.187,-0.999) {no};
\end{tikzpicture}
\end{document}
```

*Figura 4. Diagrama de flujo de la etapa 3: Corriente mínima en la resonancia*

9. Con el amperímetro en serie con la fuente, barrer la frecuencia entre 3 kHz y 8 kHz y localizar el mínimo de la corriente total, reajustando la fuente a 2,00 V eficaces. *(≈ 10 min)* **Comprobación:** El mínimo debe aparecer cerca de 5 kHz [1]; si la corriente no baja, revisar la rama del condensador.
10. Anotar la frecuencia del mínimo y medir en ella las corrientes de las tres ramas. *(≈ 10 min)* **Comprobación:** La corriente de la bobina y la del condensador deben ser varias veces la corriente total: es la corriente de circulación del tanque.

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

1. ¿Por qué en la resonancia la corriente total es menor que la corriente de la bobina o la del condensador?
2. ¿Cómo explica la resistencia de devanado que la corriente mínima medida sea mayor que la que predice el modelo ideal?
3. ¿Cómo se obtiene la resistencia equivalente en paralelo de la bobina real, $R_{p(eq)} = R_W(Q^2 + 1)$, y qué valor da con los datos medidos [1]?
4. ¿Cómo cambia el carácter del circuito al pasar por la resonancia, y cómo se observó en las corrientes?

## 5. Análisis de Resultados

Presentar en la tabla de registro las corrientes calculadas con la bobina real y las medidas a las tres frecuencias, con su diferencia porcentual y el carácter del circuito en cada una.

Dibujar el diagrama fasorial de corrientes en la resonancia y a 3 kHz, y comprobar que la suma fasorial de las corrientes de rama reproduce la corriente total medida, mientras su suma aritmética la supera ampliamente.

**Tabla 2.** RLC en paralelo con VS = 2,00 V eficaces

| Frecuencia (kHz) | IR (mA) | Ibob (mA) | IC (mA) | IT (mA) | Carácter |
|---|---|---|---|---|---|
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |
|   |   |   |   |   |   |

## 6. Conclusiones

Concluir si las corrientes medidas cumplen la ley de corrientes de Kirchhoff en forma fasorial y cómo se manifiesta la resonancia en paralelo, explicando el papel de la resistencia de devanado en la corriente mínima; relacionar la práctica con los criterios de medición en circuitos RLC del RA.

- ¿Qué tan cerca estuvo la frecuencia del mínimo de la calculada?
- ¿Qué aprendieron sobre la corriente de circulación del tanque?
- ¿Por qué el modelo con bobina ideal no basta para predecir la corriente mínima?

## 7. Recomendaciones de Seguridad

- Trabajar con el circuito desenergizado mientras se conecta o modifica el montaje; energizar solo después de la revisión del docente.
- Conectar las tierras de las dos puntas del osciloscopio a un mismo nodo de referencia: unirlas a nodos distintos cortocircuita el elemento que queda entre ellas.
- Insertar el amperímetro en serie con la rama solo con el circuito desenergizado y con el instrumento en la función y la escala de corriente; nunca conectarlo en paralelo con la fuente.
- Reajustar la tensión de la fuente después de cada cambio de frecuencia y no superar los 2,00 V eficaces previstos.

## 8. Bibliografía

[1] Floyd, Thomas L., *Principios de circuitos eléctricos*, 8.ª ed., Pearson Educación, 2007.

[2] Boylestad, Robert L., *Introducción al análisis de circuitos*, 10.ª ed., Pearson Educación, 2004.

[3] Deorsola, M. F. P., Morcelle del Valle, P., *Circuitos eléctricos. Parte 1*, 1.ª ed., Editorial de la Universidad de La Plata, 2017.
