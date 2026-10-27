---
tipo: guia_laboratorio
asignatura: '[[IEL04 - Circuitos Eléctricos I]]'
resultado_aprendizaje: '[[IEL04-RA3]]'
temario: '[[IEL04-semana09]]'
semana: 9
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
archivo_tex: generacion/guias-laboratorio/IEL04/IEL04-semana09.tex
temario_hash: dedf5cc222c6c89e
huella: d490291b6ea86673
formato: 3
docente: Ing. Sergio Martinez Castilla
facultad: Facultad de Ingenierías
compilada: '2026-10-27'
fecha_creacion: '2026-10-25'
fecha_actualizacion: '2026-10-27'
---
# Guía de laboratorio: Identificación de una bobina por su constante de tiempo y su impedancia, y medición de un circuito RL mixto

> **Facultad:** Facultad de Ingenierías · **Módulo:** IEL04 — Circuitos Eléctricos I · **Docente:** Ing. Sergio Martinez Castilla
> **Semana:** 9 de 14 · **Resultado de aprendizaje:** [[IEL04-RA3]] · **Sesión:** [[IEL04-semana09]] · **Práctica:** propuesta a partir de la bibliografía [1] [2] [3] · **Duración:** 240 minutos

La práctica cierra el RA IEL04-RA3 y corresponde a la sesión teórica de la semana 9, «Cálculo y medición de parámetros en circuitos RL según el conexionado». Reproduce su caso de estudio: determinar la inductancia de una bobina sin marcado por dos métodos independientes —su constante de tiempo con una onda cuadrada y su impedancia con una señal sinusoidal—, identificar a qué valor estándar corresponde y usarla en un circuito RL mixto, del que se miden la corriente, las tensiones y el factor de potencia. No hay un manual de laboratorio asignado, por lo que la práctica se propone a partir de la bibliografía cargada: Floyd trata la constante de tiempo L/R, la potencia en circuitos RL y los circuitos RL en serie-paralelo [1], Boylestad los transitorios R-L y los valores estándar de inductores [2] y Deorsola el régimen transitorio del circuito RL [3].

## 1. Objetivos

**Objetivo general:** Determinar experimentalmente la inductancia de una bobina por dos métodos y verificar el cálculo de un circuito RL mixto.

**Objetivos específicos:**

- Identificar el valor estándar de una bobina sin marcado a partir de sus mediciones. *(CE1)*
- Medir la constante de tiempo y la impedancia de la bobina en un circuito resistivo e inductivo. *(CE2)*
- Medir corrientes, tensiones, ángulo y factor de potencia en un circuito RL mixto y compararlos con el cálculo. *(CE3)*

## 2. Materiales y Equipos

**Tabla 1.** Materiales y equipos de la práctica

| # | Material o equipo | Especificación | Cantidad |
|---|---|---|---|
| 1 | Bobina toroidal sin marcado | — | 1 |
| 2 | Resistor | 1 kΩ (medido 996 Ω en la sesión) | 1 |
| 3 | Resistor R1 | 470 Ω | 1 |
| 4 | Resistor R2 | 680 Ω | 1 |
| 5 | Resistor sensor de corriente | 10 Ω | 1 |
| 6 | Generador de funciones | — | 1 |
| 7 | Osciloscopio de dos canales con puntas ×10 | — | 1 |
| 8 | Multímetro digital de verdadero valor eficaz | — | 2 |
| 9 | Medidor LCR | — | 1 |
| 10 | Protoboard | — | 1 |
| 11 | Cables de conexión | — | 12 |

## 3. Procedimiento

La práctica ocupa el bloque de 2 h de laboratorio de la sesión y se realiza en grupos de tres estudiantes, con tres roles que rotan entre etapas: quien monta y opera el circuito, quien mide y quien registra y verifica los cálculos. Antes de energizar cualquier montaje, el docente o el monitor revisa la conexión. Cada etapa abre con su diagrama de flujo, que muestra la secuencia y las comprobaciones de un vistazo, y sigue con sus pasos numerados; cada paso indica cuánto dura, qué debe observarse para saber que salió bien y qué hacer si no. Los valores numéricos de la sesión teórica sirven de referencia: las lecturas propias del grupo se registran en las tablas de la sección de análisis.

> Los diagramas de flujo, los circuitos y las gráficas son código LaTeX (TikZ, circuitikz y pgfplots), como en el .tex: Obsidian los dibuja con el plugin TikZJax; sin él, se ve el código (el PDF de la guía los trae dibujados).

### 3.1 Método 1: constante de tiempo (21 min)

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
  \node[dterminal, minimum width=1.656in, minimum height=0.680in] (n0) at (0.828,-0.445) {Inicio de la \\ etapa};  % ini
  \node[dcaja, minimum width=1.456in, minimum height=0.470in] (n1) at (3.159,-0.445) {Medir RW y R};  % a0
  \node[dcaja, minimum width=1.456in, minimum height=0.890in] (n2) at (5.389,-0.445) {Montar y \\ aplicar onda \\ cuadrada};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n3) at (5.389,-2.018) {Medir \ensuremath{\tau} y \\ calcular L};  % a2
  \node[ddecision, minimum width=1.766in, minimum height=1.156in] (n4) at (3.159,-2.018) {\textquestiondown{}Curva \\ completa?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n5) at (0.828,-2.018) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.993,-2.018) {s\'{\i}};
  \node[drotulo] at (4.510,-1.566) {no};
\end{tikzpicture}
\end{document}
```

*Figura 1. Diagrama de flujo de la etapa 1: Método 1: constante de tiempo*

1. Medir con el ohmímetro la resistencia de devanado de la bobina y la del resistor de 1 kΩ. *(≈ 5 min)* **Comprobación:** La resistencia de devanado debe ser de pocos ohmios; una lectura infinita indica devanado abierto.
2. Montar la bobina en serie con el resistor de 1 kΩ y aplicar una onda cuadrada de 0 V a 5 V y 10 kHz. *(≈ 6 min)* **Comprobación:** El docente revisa el montaje antes de energizar. **Seguridad:** Montar con el generador apagado.

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
\draw (0,0) to[V, l=$v_s$] (0,3) to[L, l=$L$] (4,3) to[R, l=$R$] (4,0) -- (0,0); \draw (4,3) -- (6,3) to[voltmeter, l=CH2] (6,0) -- (4,0); \draw (0,0) node[ground]{};
\end{circuitikz}
\end{document}
```

*Figura 2. Medición de la constante de tiempo: bobina en serie con el resistor y el canal 2 sobre el resistor*

3. Con la punta del canal 2 sobre el resistor, medir con los cursores el tiempo en que la tensión alcanza el 63 % de su valor final y calcular $L = \tau (R + R_W)$ [1]. *(≈ 10 min)* **Comprobación:** El semiperiodo de 50 µs debe superar con holgura cinco constantes de tiempo; si la curva no llega a la meseta, reducir la frecuencia.

**Ecuación (1).** Inductancia a partir de la constante de tiempo:

$$
L = \tau \,(R + R_W) \tag{1}
$$

donde $L$ en henrios (H), $\tau$ en segundos (s), $R$ y $R_W$ en ohmios (Ω).


### 3.2 Método 2: impedancia (26 min)

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
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n1) at (2.950,-0.340) {Ajustar 10 \\ kHz y 5 V};  % a0
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n2) at (5.157,-0.340) {Medir VR y \\ Vbob};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.470in] (n3) at (5.157,-1.808) {Calcular L};  % a2
  \node[ddecision, minimum width=1.905in, minimum height=1.156in] (n4) at (2.950,-1.808) {\textquestiondown{}M\'{e}todos \\ coinciden?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n5) at (0.689,-1.808) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.593,-1.808) {s\'{\i}};
  \node[drotulo] at (4.273,-1.405) {no};
\end{tikzpicture}
\end{document}
```

*Figura 3. Diagrama de flujo de la etapa 2: Método 2: impedancia*

4. Ajustar el generador a una onda sinusoidal de 10 kHz y medir con el osciloscopio y con el multímetro de verdadero valor eficaz que la tensión en los bornes del circuito, con el circuito conectado, sea de 5,00 V eficaces. *(≈ 6 min)* **Comprobación:** El multímetro debe indicar 5,00 V y el osciloscopio una sinusoide sin distorsión; si la tensión baja al conectar el circuito, reajustar la amplitud con el circuito conectado.
5. Medir la tensión en el resistor para obtener la corriente y la tensión en la bobina con la resta de canales del osciloscopio. *(≈ 10 min)* **Comprobación:** Debe obtenerse una corriente cercana a 4,86 mA; si la resta de canales da ruido, verificar que ambos canales tengan la misma escala.
6. Calcular $Z_{bob} = V_{bob}/I$, $X_L = \sqrt{Z_{bob}^2 - R_W^2}$ y $L = X_L/(2\pi f)$, y compararla con la del método 1; identificar el valor estándar más cercano [2]. *(≈ 10 min)* **Comprobación:** Los dos métodos deben coincidir a pocos por ciento; si no, repetir la medición de τ.

**Ecuación (2).** Inductancia a partir de la impedancia de la bobina:

$$
X_L = \sqrt{Z_{\mathrm{bob}}^2 - R_W^2}, \qquad L = \frac{X_L}{2\pi f} \tag{2}
$$

donde $Z_{bob}$, $X_L$ y $R_W$ en ohmios (Ω), $f$ en Hz y $L$ en H.


### 3.3 Circuito RL mixto (35 min)

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
  \node[dterminal, minimum width=1.656in, minimum height=0.680in] (n0) at (0.828,-0.445) {Inicio de la \\ etapa};  % ini
  \node[dcaja, minimum width=1.642in, minimum height=0.680in] (n1) at (3.508,-0.445) {Montar \\ circuito mixto};  % a0
  \node[dcaja, minimum width=1.363in, minimum height=0.890in] (n2) at (6.133,-0.445) {Medir \\ tensiones y \\ corrientes};  % a1
  \node[dcaja, minimum width=1.549in, minimum height=0.680in] (n3) at (6.133,-2.018) {Medir desfase \\ y calcular FP};  % a2
  \node[ddecision, minimum width=2.463in, minimum height=1.156in] (n4) at (3.508,-2.018) {\textquestiondown{}Coincide con \\ la predicci\'{o}n?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n5) at (0.828,-2.018) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.900,-2.018) {s\'{\i}};
  \node[drotulo] at (5.056,-1.625) {no};
\end{tikzpicture}
\end{document}
```

*Figura 4. Diagrama de flujo de la etapa 3: Circuito RL mixto*

7. Montar R1 en serie con el paralelo de R2 y la bobina identificada, con el resistor sensor en serie del lado de tierra, y predecir la corriente, las tensiones y el ángulo con los valores medidos. *(≈ 12 min)* **Comprobación:** La corriente esperada es de unos 8,8 mA con un factor de potencia cercano a 0,95. **Seguridad:** Montar con el generador apagado.
8. Medir la corriente total, $V_{R1}$, la tensión del paralelo y las corrientes de rama con el multímetro de verdadero valor eficaz. *(≈ 15 min)* **Comprobación:** Las lecturas deben estar a menos del 2 % de la predicción. **Seguridad:** Insertar el amperímetro solo con el circuito desenergizado.
9. Medir el desfase de la corriente total con el osciloscopio y calcular el factor de potencia $FP = \cos\theta$ y la potencia real $P = V I \cos\theta$ [1]. *(≈ 8 min)* **Comprobación:** El ángulo debe estar cerca de 19° de atraso.

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

1. ¿Por qué dos métodos independientes, uno en el dominio del tiempo y otro en el de la frecuencia, dan confianza en el valor de la inductancia?
2. ¿Qué error se cometería al calcular L con la constante de tiempo usando solo la resistencia del resistor y no la de devanado?
3. ¿A qué valor estándar corresponde la bobina y con qué criterio se eligió?
4. ¿Qué significa el factor de potencia medido del circuito mixto y cómo podría corregirse?

## 5. Análisis de Resultados

Calcular la inductancia por los dos métodos, con su diferencia porcentual, e identificar el valor estándar más cercano de la serie de inductores.

Presentar en la tabla del circuito mixto la predicción, la medición y la diferencia de cada magnitud, y calcular el factor de potencia y las potencias real, reactiva y aparente con las lecturas.

**Tabla 2.** Inductancia de la bobina sin marcado

| Método | Magnitud medida | Valor medido | L calculada (mH) | Diferencia entre métodos (%) |
|---|---|---|---|---|
|   |   |   |   |   |
|   |   |   |   |   |

**Tabla 3.** Circuito RL mixto a 10 kHz

| Magnitud | Calculado | Medido | Unidad | Diferencia (%) |
|---|---|---|---|---|
|   |   |   |   |   |
|   |   |   |   |   |
|   |   |   |   |   |
|   |   |   |   |   |
|   |   |   |   |   |
|   |   |   |   |   |
|   |   |   |   |   |

## 6. Conclusiones

Concluir qué inductancia tiene la bobina y a qué valor estándar corresponde, apoyándose en la concordancia de los dos métodos, y si el circuito mixto se comporta como predice el cálculo; relacionar la práctica con los criterios de medición en circuitos resistivos, inductivos y RL del RA.

- ¿Qué método resultó más preciso y por qué?
- ¿Qué aprendieron sobre la medición de inductancia sin un medidor LCR?
- ¿Hubo algún resultado inesperado en el circuito mixto?

## 7. Recomendaciones de Seguridad

- Conectar las tierras de las dos puntas del osciloscopio a un mismo nodo de referencia: unirlas a nodos distintos cortocircuita el elemento que queda entre ellas.
- Insertar el amperímetro en serie con la rama solo con el circuito desenergizado y con el instrumento en la función y la escala de corriente; nunca conectarlo en paralelo con la fuente.
- No interrumpir bruscamente la corriente de la bobina con el circuito energizado.
- Desenergizar antes de pasar del montaje de los métodos 1 y 2 al circuito mixto.

## 8. Bibliografía

[1] Floyd, Thomas L., *Principios de circuitos eléctricos*, 8.ª ed., Pearson Educación, 2007.

[2] Boylestad, Robert L., *Introducción al análisis de circuitos*, 10.ª ed., Pearson Educación, 2004.

[3] Deorsola, M. F. P., Morcelle del Valle, P., *Circuitos eléctricos. Parte 1*, 1.ª ed., Editorial de la Universidad de La Plata, 2017.
