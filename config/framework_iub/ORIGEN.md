# Logos institucionales IUB (copia local)

Los logos de la institución, según el Manual de Identidad Visual IUB 2025 (`manualdeidentidadiub2025_IUB.pdf`, carpeta `Manual_Ident_IUB` del docente).

Desde el diseño 6 de las presentaciones (2026-10-23) **las presentaciones los usan**: `src/presentaciones.py` copia a `logos/`, junto a cada `.tex`, los que nombra `LOGOS` en `src/diseno_iub.py`, y el preámbulo los pone con macros (`\logoIUBsimbolo`, `\logoIUBhorizontal`, `\logoIUBamarillo`; si falta uno, la marca sale como texto).

- `logos/logo_iub_blanco.png` — el símbolo en negativo (letras blancas y el punto amarillo), sobre el fondo #121023: la franja del título;
- `logos/logo_iub_horizontal.png` — el logo horizontal a color, sobre fondo blanco: los separadores de bloque. Es el `LOGOPORTADA.png` del docente, recortado a su contenido;
- `logos/logo_iub_horizontal_amarillo.png` — el horizontal a una tinta en #FFDF2D, sobre #121023: la portada y el cierre (manual 3.1 y 3.3.1). Generado a partir de `logo_iub_horizontal.png` (cada píxel, en amarillo, con su transparencia);
- `logos/logo_iub_azul.png`, `logos/logo_iub_azul_puro.png` y `logos/logo_iub_blanco_puro.png` — otras versiones del símbolo (del repositorio del framework institucional, https://github.com/vcudris/framework_presentaciones_iub), que las presentaciones no usan.

Si la institución cambia sus logos, se reemplazan estos PNG con los mismos nombres. ACTUALIZAR-ESTRUCTURA nunca los pisa en una copia.
