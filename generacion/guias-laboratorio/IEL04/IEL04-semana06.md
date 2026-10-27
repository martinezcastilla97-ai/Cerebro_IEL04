---
tipo: guia_laboratorio
asignatura: '[[IEL04 - Circuitos Eléctricos I]]'
resultado_aprendizaje: '[[IEL04-RA2]]'
temario: '[[IEL04-semana06]]'
semana: 6
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
archivo_tex: generacion/guias-laboratorio/IEL04/IEL04-semana06.tex
temario_hash: 779ac30c85636f33
huella: 40f01f294d19e0a0
formato: 3
docente: Ing. Sergio Martinez Castilla
facultad: Facultad de Ingenierías
compilada: '2026-10-27'
fecha_creacion: '2026-10-25'
fecha_actualizacion: '2026-10-27'
---
# Guía de laboratorio: Circuito RC en paralelo: corrientes de rama, corriente total y ley de corrientes de Kirchhoff

> **Facultad:** Facultad de Ingenierías · **Módulo:** IEL04 — Circuitos Eléctricos I · **Docente:** Ing. Sergio Martinez Castilla
> **Semana:** 6 de 14 · **Resultado de aprendizaje:** [[IEL04-RA2]] · **Sesión:** [[IEL04-semana06]] · **Práctica:** propuesta a partir de la bibliografía [1] [2] [3] · **Duración:** 240 minutos

La práctica corresponde a la sesión teórica de la semana 6, «El circuito RC en paralelo: admitancia, reparto de corrientes y ley de corrientes de Kirchhoff», y reproduce su caso de estudio con los mismos componentes de la semana 4 conectados en paralelo: se miden a 1 kHz la corriente de cada rama y la corriente total, y se comprueba que la corriente total es la suma fasorial de las corrientes de rama. No hay un manual de laboratorio asignado al RA IEL04-RA2, por lo que la práctica se propone a partir de la bibliografía cargada: Floyd trata la admitancia y el análisis de circuitos RC en paralelo y la ley de corrientes de Kirchhoff [1], Boylestad las redes de ca en paralelo [2] y Deorsola las leyes de Kirchhoff con fasores [3].

## 1. Objetivos

**Objetivo general:** Verificar experimentalmente la ley de corrientes de Kirchhoff y el ángulo de fase en un circuito RC en paralelo.

**Objetivos específicos:**

- Identificar y verificar con instrumentos el resistor y el condensador del circuito. *(CE1)*
- Medir con el multímetro la corriente de la rama resistiva y la de la rama capacitiva a 1 kHz. *(CE2)*
- Medir la corriente total y su desfase respecto de la tensión, y comprobar la suma fasorial de las corrientes de rama en el circuito RC en paralelo. *(CE3)*

## 2. Materiales y Equipos

**Tabla 1.** Materiales y equipos de la práctica

| # | Material o equipo | Especificación | Cantidad |
|---|---|---|---|
| 1 | Resistor de película | 1,5 kΩ ±5 % | 1 |
| 2 | Condensador C2 del kit | 104K, 97,8 nF medidos | 1 |
| 3 | Resistor sensor de corriente | 10 Ω | 1 |
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

### 3.1 Preparación y montaje (16 min)

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
  \node[dcaja, minimum width=1.177in, minimum height=0.680in] (n1) at (2.880,-0.340) {Descargar \\ C2};  % a0
  \node[dcaja, minimum width=1.363in, minimum height=0.680in] (n2) at (5.064,-0.340) {Verificar R \\ y C};  % a1
  \node[dcaja, minimum width=1.270in, minimum height=0.890in] (n3) at (5.064,-1.808) {Montar \\ paralelo \\ con sensor};  % a2
  \node[ddecision, minimum width=1.766in, minimum height=1.156in] (n4) at (2.880,-1.808) {\textquestiondown{}Montaje \\ revisado?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n5) at (0.689,-1.808) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) to[bend right=24] (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n3);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.784,-1.808) {s\'{\i}};
  \node[drotulo] at (3.972,-2.136) {no};
\end{tikzpicture}
\end{document}
```

*Figura 1. Diagrama de flujo de la etapa 1: Preparación y montaje*

1. Descargar el condensador conectando entre sus terminales, durante unos segundos, una resistencia de 1 kΩ sujeta con pinzas aisladas, y medir con el voltímetro en cd la tensión entre terminales. *(≈ 3 min)* **Comprobación:** La tensión debe ser prácticamente nula (menos de 0,1 V); si no lo es, repetir la descarga antes de manipular el componente. **Seguridad:** No cortocircuitar los terminales con los dedos ni con una herramienta metálica: un condensador puede conservar carga después de desconectado.
2. Verificar el resistor con el ohmímetro y el condensador C2 con el medidor LCR, y anotar sus valores medidos. *(≈ 6 min)* **Comprobación:** El resistor debe leer cerca de 1492 Ω y C2 cerca de 97,8 nF; si alguno sale de su tolerancia, reemplazarlo y anotar el nuevo valor.
3. Montar el resistor y C2 en paralelo y dejar en serie con la fuente el resistor sensor de 10 Ω, del lado de tierra, para observar la forma de onda de la corriente total. *(≈ 7 min)* **Comprobación:** El docente revisa el montaje; el sensor debe quedar entre el paralelo y la tierra del generador. **Seguridad:** Montar con el generador apagado.

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
\draw (0,0) to[sV, l=$v_s$] (0,3) to[ammeter, l=$I_T$] (3,3) to[R, l=$R$] (3,0) -- (0,0); \draw (3,3) -- (6,3) to[C, l=$C_2$] (6,0) -- (3,0); \draw (0,0) node[ground]{};
\end{circuitikz}
\end{document}
```

*Figura 2. Circuito RC en paralelo con el amperímetro en serie con la fuente*


### 3.2 Medición de las corrientes (30 min)

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
  \node[dcaja, minimum width=1.177in, minimum height=0.680in] (n1) at (2.685,-0.340) {Ajustar 1 \\ kHz y 5 V};  % a0
  \node[dcaja, minimum width=1.084in, minimum height=0.470in] (n2) at (4.877,-0.340) {Medir IR};  % a1
  \node[dcaja, minimum width=1.084in, minimum height=0.470in] (n3) at (6.921,-0.340) {Medir IC};  % a2
  \node[dcaja, minimum width=1.084in, minimum height=0.470in] (n4) at (6.921,-1.986) {Medir IT};  % a3
  \node[ddecision, minimum width=1.766in, minimum height=1.513in] (n5) at (4.877,-1.986) {\textquestiondown{}IT menor \\ que IR + \\ IC?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n6) at (2.685,-1.986) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n5) -- (n6);
  \draw[dflecha] (n5) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (3.781,-1.986) {s\'{\i}};
  \node[drotulo] at (5.114,-0.999) {no};
\end{tikzpicture}
\end{document}
```

*Figura 3. Diagrama de flujo de la etapa 2: Medición de las corrientes*

4. Ajustar el generador a una onda sinusoidal de 1 kHz y medir con el osciloscopio y con el multímetro de verdadero valor eficaz que la tensión en los bornes del circuito, con el circuito conectado, sea de 5,00 V eficaces. *(≈ 6 min)* **Comprobación:** El multímetro debe indicar 5,00 V y el osciloscopio una sinusoide sin distorsión; si la tensión baja al conectar el circuito, reajustar la amplitud con el circuito conectado.
5. Con el circuito desenergizado, insertar el multímetro en serie con la rama del resistor, energizar y anotar la corriente $I_R$. *(≈ 8 min)* **Comprobación:** Debe leerse cerca de 3,35 mA; si la lectura es nula, revisar que el multímetro esté en la función de corriente alterna. **Seguridad:** Insertar el amperímetro solo con el circuito desenergizado.
6. Repetir en la rama del condensador y anotar $I_C$. *(≈ 8 min)* **Comprobación:** Debe leerse cerca de 3,07 mA.
7. Repetir en serie con la fuente y anotar la corriente total $I_T$. *(≈ 8 min)* **Comprobación:** Debe leerse cerca de 4,55 mA, menor que la suma aritmética de las ramas; si coincide con la suma, revisar las conexiones.

### 3.3 Ángulo de fase de la corriente total (19 min)

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
  \node[dcaja, minimum width=1.084in, minimum height=0.680in] (n1) at (3.019,-0.340) {Conectar \\ canales};  % a0
  \node[dcaja, minimum width=1.270in, minimum height=0.680in] (n2) at (5.296,-0.340) {Medir \\ desfase \ensuremath{\Delta}t};  % a1
  \node[dcaja, minimum width=1.084in, minimum height=0.890in] (n3) at (5.296,-1.808) {Calcular \\ suma \\ fasorial};  % a2
  \node[ddecision, minimum width=2.045in, minimum height=1.156in] (n4) at (3.019,-1.808) {\textquestiondown{}Coincide \\ con IT y \ensuremath{\theta}?};  % dec
  \node[dterminal, minimum width=1.377in, minimum height=0.680in] (n5) at (0.689,-1.808) {Fin de la \\ etapa};  % fin
  % flechas (las de retorno, curvas)
  \draw[dflecha] (n0) -- (n1);
  \draw[dflecha] (n1) -- (n2);
  \draw[dflecha] (n2) -- (n3);
  \draw[dflecha] (n3) -- (n4);
  \draw[dflecha] (n4) -- (n5);
  \draw[dflecha] (n4) to[bend right=31] (n2);
  % rotulos de las flechas (donde no caen sobre un nodo)
  \node[drotulo] at (1.621,-1.808) {s\'{\i}};
  \node[drotulo] at (4.378,-1.416) {no};
\end{tikzpicture}
\end{document}
```

*Figura 4. Diagrama de flujo de la etapa 3: Ángulo de fase de la corriente total*

8. Conectar el canal 1 a la tensión de la fuente y el canal 2 sobre el resistor sensor, con las tierras en el mismo nodo. *(≈ 5 min)* **Comprobación:** En el canal 2 debe verse una sinusoide pequeña (decenas de mV) en fase con la corriente total.
9. Medir el desfase $\Delta t$ entre los cruces por cero de las dos señales y calcular $\theta = 360^\circ \times f \times \Delta t$. *(≈ 8 min)* **Comprobación:** La corriente total debe adelantar a la tensión unos 42°; si se ve atrasada, revisar la polaridad de las puntas.
10. Calcular $\sqrt{I_R^2 + I_C^2}$ y $\arctan(I_C/I_R)$ con las lecturas y compararlos con $I_T$ y con el ángulo medido. *(≈ 6 min)* **Comprobación:** Los valores deben coincidir a menos del 2 % y de 1°; si no, repetir la medición de corriente correspondiente.

**Ecuación (1).** Ley de corrientes de Kirchhoff en forma fasorial y ángulo de la corriente total:

$$
I_T = \sqrt{I_R^2 + I_C^2}, \qquad \theta = \arctan\left(\frac{I_C}{I_R}\right) \tag{1}
$$

donde $I_T$, $I_R$ e $I_C$ son corrientes eficaces en mA y $\theta$ el ángulo de adelanto en grados (°).


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

1. ¿Por qué la corriente total es menor que la suma aritmética de las corrientes de rama?
2. ¿Cómo se compara la corriente total del circuito en paralelo con la del circuito en serie de la semana 4, con los mismos componentes y la misma fuente?
3. ¿Por qué los ángulos de los circuitos en serie y en paralelo son aproximadamente complementarios?
4. ¿Qué error introduce el resistor sensor de 10 Ω en la medición de la corriente total?

## 5. Análisis de Resultados

Calcular con los valores medidos de R y C las corrientes de rama, la corriente total y el ángulo esperados, y compararlos con las mediciones en la tabla de registro, con su diferencia porcentual.

Dibujar el diagrama fasorial de corrientes con $I_R$ en fase con la tensión e $I_C$ adelantada 90°, y comprobar que su suma vectorial reproduce $I_T$ medida.

**Tabla 2.** Corrientes y ángulo del circuito RC en paralelo a 1 kHz

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

Concluir si la ley de corrientes de Kirchhoff se cumple en forma fasorial en el circuito RC en paralelo, explicando las pequeñas diferencias con la resistencia interna del amperímetro y la resolución de los cursores; comparar con el circuito en serie de la semana 4 y relacionarlo con los criterios de medición del RA.

- ¿Qué demuestra la comparación entre la suma aritmética y la fasorial de las corrientes?
- ¿Por qué la corriente total se duplicó respecto del circuito en serie?
- ¿Qué medición resultó más delicada y por qué?

## 7. Recomendaciones de Seguridad

- Trabajar con el circuito desenergizado mientras se conecta o modifica el montaje; energizar solo después de la revisión del docente.
- Descargar los condensadores con una resistencia antes de manipularlos o medirlos, y respetar la polaridad de los electrolíticos: conectado con la polaridad invertida, un electrolítico puede explotar y provocar lesiones [1].
- Conectar las tierras de las dos puntas del osciloscopio a un mismo nodo de referencia: unirlas a nodos distintos cortocircuita el elemento que queda entre ellas.
- Insertar el amperímetro en serie con la rama solo con el circuito desenergizado y con el instrumento en la función y la escala de corriente; nunca conectarlo en paralelo con la fuente.

## 8. Bibliografía

[1] Floyd, Thomas L., *Principios de circuitos eléctricos*, 8.ª ed., Pearson Educación, 2007.

[2] Boylestad, Robert L., *Introducción al análisis de circuitos*, 10.ª ed., Pearson Educación, 2004.

[3] Deorsola, M. F. P., Morcelle del Valle, P., *Circuitos eléctricos. Parte 1*, 1.ª ed., Editorial de la Universidad de La Plata, 2017.
