r"""Capa de seguridad LaTeX de src/: convierte texto (Markdown en linea) y formulas a LaTeX que pdfLaTeX compila, revisa el LaTeX
que escribe el modelo y comprueba un .tex sin compilarlo. La usan PRESENTACIONES (los datos del wiki se escapan; el LaTeX del modelo
pasa por la lista de permitidos antes de llegar al .tex) y TEMARIO (que pide corregir las formulas con comandos que no son
matematicos conocidos).

    Conversor.escapar / inline / titulo   texto -> LaTeX: los especiales se escapan, los simbolos Unicode salen como comando
                                          (el .tex no depende de inputenc) y lo que no tiene equivalente queda como [U+XXXX] con aviso
    Conversor.matematicas                 una formula: solo comandos matematicos conocidos (lista de PERMITIDOS: lo demas, incluido
                                          todo lo que lee o escribe archivos, sale como texto), sintaxis a medias completada y las
                                          unidades de siunitx fuera de \SI{}{} convertidas a su simbolo; todo con aviso
    comandos_no_permitidos                los comandos de una formula que no estan en la lista
    verificar_cuerpo                      el LaTeX de una diapositiva que escribio el modelo: lista de PERMITIDOS para todo el cuerpo
                                          (texto, matematicas, tablas, TikZ, pgfplots, circuitikz, las cajas del diseno), claves que
                                          leen o escriben archivos, balance; normaliza el codigo (ASCII, \end{frame} neutralizado)
    verificar_latex, graves               comprobacion ESTATICA del .tex completo (la misma lista en todo el documento, [fragile],
                                          codigo, caracteres, balance) y cuales de sus problemas impiden escribirlo o compilarlo
    ascii_codigo, dimensiones_png         lo que necesitan el codigo (listings) y las figuras del temario

Las reglas salen de compilar muestras con Tectonic (XeTeX): `100\,\%` no compila con babel espanol, una formula a medias
detiene TeX y se pierde el documento entero, `lstlisting` no admite Unicode con pdfLaTeX. Con pdfLaTeX real no se ha comprobado.
"""

from __future__ import annotations

import re
import struct
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Caracteres Unicode -> LaTeX
# ---------------------------------------------------------------------------

_GRIEGAS_MIN = dict(zip(
    "αβγδεζηθικλμνξοπρστυφχψω",
    ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu",
     "nu", "xi", "o", "pi", "rho", "sigma", "tau", "upsilon", "varphi", "chi", "psi", "omega"],
))
_GRIEGAS_MAY = dict(zip("ΓΔΘΛΞΠΣΥΦΨΩ", ["Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega"]))
_GRIEGAS_COMO_LATINAS = dict(zip("ΑΒΕΖΗΙΚΜΝΟΡΤΧ", "ABEZHIKMNOPTX"))

_SIMBOLOS = {
    "→": r"\rightarrow", "←": r"\leftarrow", "↔": r"\leftrightarrow", "⇒": r"\Rightarrow", "⇐": r"\Leftarrow",
    "⇔": r"\Leftrightarrow", "↑": r"\uparrow", "↓": r"\downarrow", "↦": r"\mapsto", "⟶": r"\longrightarrow",
    "➔": r"\rightarrow", "➜": r"\rightarrow", "➡": r"\rightarrow", "⇨": r"\Rightarrow",
    "≥": r"\geq", "≤": r"\leq", "≠": r"\neq", "≈": r"\approx", "≡": r"\equiv", "≅": r"\cong", "∼": r"\sim",
    "≪": r"\ll", "≫": r"\gg", "∝": r"\propto", "∞": r"\infty", "∑": r"\sum", "∏": r"\prod", "∫": r"\int",
    "∂": r"\partial", "∇": r"\nabla", "√": r"\surd", "∈": r"\in", "∉": r"\notin", "⊂": r"\subset",
    "⊆": r"\subseteq", "∪": r"\cup", "∩": r"\cap", "∅": r"\emptyset", "∧": r"\wedge", "∨": r"\vee",
    "¬": r"\neg", "∀": r"\forall", "∃": r"\exists", "⊥": r"\perp", "∥": r"\parallel", "∠": r"\angle",
    "△": r"\triangle", "⊕": r"\oplus", "⊗": r"\otimes", "∘": r"\circ", "∙": r"\cdot", "⋅": r"\cdot",
    "·": r"\cdot", "×": r"\times", "÷": r"\div", "±": r"\pm", "∓": r"\mp", "−": "-", "∗": "*", "′": "'",
    "″": "''", "°": r"^{\circ}", "℃": r"^{\circ}\mathrm{C}", "\u2126": r"\Omega", "ℓ": r"\ell", "ℏ": r"\hbar",
    "\u00b5": r"\mu", "■": r"\blacksquare", "□": r"\square", "▶": r"\blacktriangleright", "◀": r"\blacktriangleleft",
    "▲": r"\blacktriangle", "▼": r"\blacktriangledown", "▸": r"\triangleright", "●": r"\bullet",
    "○": r"\circ", "◦": r"\circ", "★": r"\star", "☆": r"\star", "✓": r"\checkmark", "✔": r"\checkmark",
    "✅": r"\checkmark", "☑": r"\checkmark", "✗": r"\times", "✘": r"\times", "❌": r"\times", "✖": r"\times",
    "⚠": r"\triangle", "²": "^{2}", "³": "^{3}", "¹": "^{1}", "⁰": "^{0}", "⁴": "^{4}", "⁵": "^{5}",
    "⁶": "^{6}", "⁷": "^{7}", "⁸": "^{8}", "⁹": "^{9}", "⁺": "^{+}", "⁻": "^{-}", "ⁿ": "^{n}",
    "₀": "_{0}", "₁": "_{1}", "₂": "_{2}", "₃": "_{3}", "₄": "_{4}", "₅": "_{5}", "₆": "_{6}", "₇": "_{7}",
    "₈": "_{8}", "₉": "_{9}", "₊": "_{+}", "₋": "_{-}", "ϕ": r"\phi", "ς": r"\varsigma",
    "½": r"\frac{1}{2}", "¼": r"\frac{1}{4}", "¾": r"\frac{3}{4}",
}
_SIMBOLOS.update({k: "\\" + v for k, v in _GRIEGAS_MIN.items() if len(v) > 1})
_SIMBOLOS.update({k: v for k, v in _GRIEGAS_MIN.items() if len(v) == 1})
_SIMBOLOS.update({k: "\\" + v for k, v in _GRIEGAS_MAY.items()})
_SIMBOLOS.update(_GRIEGAS_COMO_LATINAS)

# Puntuacion y simbolos latinos en modo TEXTO: se escriben como COMANDO y no como Unicode literal, para que el .tex
# no dependa de las tablas de inputenc (que solo existen en pdfLaTeX) y compile igual con XeLaTeX, LuaLaTeX o Tectonic.
# Con pdfLaTeX el resultado es el mismo que daria inputenc. Las letras acentuadas (a e i o u n u con tilde...) van literales.
_TEXTO_COMO_COMANDO = {
    "\u00bf": r"\textquestiondown{}", "\u00a1": r"\textexclamdown{}", "\u00ab": r"\guillemotleft{}",
    "\u00bb": r"\guillemotright{}", "\u2013": "--", "\u2014": "---", "\u2018": "`", "\u2019": "'", "\u201a": ",",
    "\u201c": "``", "\u201d": "''", "\u201e": ",,", "\u2026": r"\ldots{}", "\u2022": r"\textbullet{}",
    "\u00b7": r"\textperiodcentered{}", "\u2020": r"\dag{}", "\u2021": r"\ddag{}", "\u2030": r"\textperthousand{}",
    "\u20ac": r"\texteuro{}", "\u2122": r"\texttrademark{}", "\u00a9": r"\textcopyright{}",
    "\u00ae": r"\textregistered{}", "\u00a7": r"\S{}", "\u00b6": r"\P{}", "\u00b0": r"\textdegree{}",
    "\u00b1": r"\textpm{}", "\u00d7": r"\texttimes{}", "\u00f7": r"\textdiv{}", "\u00ac": r"\textlnot{}",
    "\u00aa": r"\textordfeminine{}", "\u00ba": r"\textordmasculine{}", "\u00b2": r"\texttwosuperior{}",
    "\u00b3": r"\textthreesuperior{}", "\u00b9": r"\textonesuperior{}", "\u00b5": r"\textmu{}",
    "\u00bd": r"\textonehalf{}", "\u00bc": r"\textonequarter{}", "\u00be": r"\textthreequarters{}", "\u00a0": "~",
}

# Espacios y marcas invisibles.
_IGNORAR = {"\ufe0f", "\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad"}
_ESPACIOS = {"\u2009": "\\,", "\u202f": "\\,", "\u2002": " ", "\u2003": " ", "\u2007": " ", "\u2008": " ", "\u200a": " "}

_SOPORTADOS_EXTRA = {0x2013, 0x2014, 0x2018, 0x2019, 0x201A, 0x201C, 0x201D, 0x201E, 0x2020, 0x2021,
                     0x2022, 0x2026, 0x2030, 0x20AC, 0x2122}


def soportado_por_inputenc(ch: str) -> bool:
    """Caracteres no ASCII que pdfLaTeX (inputenc utf8 + T1) compila sin definiciones extra."""
    o = ord(ch)
    return 0x00A1 <= o <= 0x017F or o in _SOPORTADOS_EXTRA or o == 0x00A0


_ESPECIALES = {
    "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "&": r"\&", "%": r"\%", "#": r"\#",
    "_": r"\_", "^": r"\^{}", "~": r"\textasciitilde{}",
}
_MARCA_ESCAPE = "\ue010"     # un \ que el autor ya escribio ante $ % & _ # { }
_MARCA_DOLAR = "\ue011"      # un \$ del autor (para que no se confunda con un delimitador de matematicas)
_MARCA_INI, _MARCA_FIN = "\ue000", "\ue001"

_MATH_DISPLAY = re.compile(r"\$\$(.+?)\$\$", re.S)
_MATH_INLINE = re.compile(r"(?<![\\$\w])\$(?![\s$])((?:\\.|[^$\\\n])+?)(?<![\s\\])\$(?![\d$\w])")
_PARENS_MATH = re.compile(r"\\\((.+?)\\\)", re.S)
_ENLACE_WIKI_ALIAS = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]")
_ENLACE_WIKI = re.compile(r"\[\[([^\]]+)\]\]")
_IMAGEN = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_ENLACE_MD = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_NEGRITA = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_CURSIVA = re.compile(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])")


# Segunda capa (la primera es la lista de permitidos de las formulas, mas abajo): primitivas de TeX que leen o escriben
# archivos, ejecutan programas o redefinen TeX, y que `verificar_latex` busca en TODO el .tex final, fuera del codigo.
_PRIMITIVAS_PELIGROSAS = frozenset({
    "input", "include", "includegraphics", "openin", "openout", "closein", "closeout", "read", "readline", "write", "immediate",
    "newread", "newwrite", "scantokens", "catcode", "def", "edef", "gdef", "xdef", "let", "futurelet", "csname", "newcommand",
    "renewcommand", "providecommand", "newenvironment", "renewenvironment", "usepackage", "RequirePackage", "special",
})
_TOKEN_TEX = re.compile(r"\\\\|\\([A-Za-z]+)")     # `\\` (salto de linea) se consume aparte: en `\\input`, "input" es solo texto


def primitivas_peligrosas(tex: str) -> list[str]:
    """Las primitivas peligrosas (ver _PRIMITIVAS_PELIGROSAS) que aparecen como comando en `tex`."""
    return sorted({m.group(1) for m in _TOKEN_TEX.finditer(tex) if m.group(1) in _PRIMITIVAS_PELIGROSAS})


# Una FORMULA sale del temario (texto de un LLM o editado a mano) y llega al .tex sin escapar: dentro de ella solo se
# admiten comandos matematicos conocidos, y todo lo demas se neutraliza (sale como texto) y deja un aviso. Una lista de
# prohibidos siempre deja fuera algun comando que lee archivos (\InputIfFileExists, \pdffiledump, \lstinputlisting,
# \verbatiminput...); una lista de permitidos, no.
_GRIEGAS_Y_LETRAS = """
    alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa varkappa lambda mu nu xi pi varpi rho varrho
    sigma varsigma tau upsilon phi varphi chi psi omega  Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega
    varGamma varDelta varTheta varLambda varXi varPi varSigma varUpsilon varPhi varPsi varOmega digamma
    aleph beth gimel daleth hbar hslash ell Re Im wp mho imath jmath
"""
_SIMBOLOS_VARIOS = """
    partial nabla infty emptyset varnothing forall exists nexists neg lnot angle measuredangle sphericalangle prime backprime
    surd top bot triangle blacktriangle square blacksquare Box diamond Diamond clubsuit diamondsuit heartsuit spadesuit flat
    natural sharp checkmark dag ddag dagger ddagger S P complement degree
"""
_OPERADORES = """
    times cdot cdotp pm mp div ast star circ bullet oplus ominus otimes oslash odot bigoplus bigotimes bigodot cup cap setminus
    smallsetminus uplus sqcup sqcap bigcup bigcap bigsqcup biguplus bigvee bigwedge vee wedge land lor barwedge veebar
    dotplus ltimes rtimes amalg wr triangleleft triangleright bigtriangleup bigtriangledown
"""
_RELACIONES = """
    in ni notin subset supset subseteq supseteq nsubseteq nsupseteq subsetneq supsetneq equiv sim simeq approx approxeq cong
    ncong propto neq ne leq le geq ge ll gg lll ggg leqslant geqslant lessgtr gtrless prec succ preceq succeq perp parallel
    nparallel mid nmid vdash dashv models Vdash asymp doteq triangleq coloneqq eqqcolon coloneq lt gt not nless ngtr nleq ngeq
    lesssim gtrsim thicksim thickapprox bowtie smile frown therefore because
"""
_FLECHAS = """
    to gets leftarrow rightarrow leftrightarrow Leftarrow Rightarrow Leftrightarrow longleftarrow longrightarrow
    longleftrightarrow Longleftarrow Longrightarrow Longleftrightarrow mapsto longmapsto uparrow downarrow updownarrow Uparrow
    Downarrow Updownarrow nearrow searrow swarrow nwarrow hookrightarrow hookleftarrow rightleftharpoons leftrightharpoons
    rightharpoonup rightharpoondown leftharpoonup leftharpoondown implies impliedby iff xrightarrow xleftarrow xLeftarrow
    xRightarrow xleftrightarrow leadsto rightsquigarrow twoheadrightarrow nrightarrow nleftarrow nLeftarrow nRightarrow
    circlearrowleft circlearrowright curvearrowleft curvearrowright
"""
_ESTRUCTURAS = """
    frac dfrac tfrac cfrac binom dbinom tbinom sqrt sum prod coprod int iint iiint iiiint idotsint oint lim limsup liminf
    varlimsup varliminf varinjlim varprojlim injlim projlim sup inf max min arg det dim exp gcd hom ker lg ln log Pr sin cos tan
    cot sec csc sinh cosh tanh coth arcsin arccos arctan deg mod bmod pmod pod limits nolimits displaylimits displaystyle
    textstyle scriptstyle scriptscriptstyle over atop choose substack sideset prescript smash phantom hphantom vphantom
    mathstrut stackrel overset underset boxed tag notag nonumber ensuremath color textcolor mathbin mathrel mathop mathord
    mathopen mathclose mathpunct mathinner mbox
"""
_DELIMITADORES = """
    left right middle big Big bigg Bigg bigl bigr bigm Bigl Bigr Bigm biggl biggr biggm Biggl Biggr Biggm lbrace rbrace langle
    rangle lfloor rfloor lceil rceil lvert rvert lVert rVert vert Vert lbrack rbrack backslash lgroup rgroup ulcorner urcorner
    llcorner lrcorner
"""
_TIPOGRAFIA = """
    text textbf textit textrm textsf texttt textnormal textup textmd textsl textsc textbackslash textasciicircum
    textasciitilde textunderscore mathrm mathbf mathit mathsf mathtt mathcal mathbb mathfrak mathnormal boldsymbol pmb
    operatorname
"""
_ACENTOS = """
    hat widehat check widecheck bar overline underline overbrace underbrace vec dot ddot dddot ddddot tilde widetilde acute grave
    breve mathring overrightarrow overleftarrow overleftrightarrow underrightarrow underleftarrow underleftrightarrow
"""
_ESPACIOS_Y_PUNTOS = """
    quad qquad enspace thinspace medspace thickspace negthinspace negmedspace negthickspace hspace
    ldots cdots vdots ddots dots dotsb dotsc dotsi dotsm dotso mathellipsis hline
"""
_SIUNITX = """
    SI si num ang SIrange numrange qty qtyrange unit numlist SIlist per squared cubed square cubic of raiseto tothe
    yocto zepto atto femto pico nano micro milli centi deci deca hecto kilo mega giga tera peta exa zetta yotta
    meter metre gram kilogram second ampere kelvin mole candela hertz newton pascal joule watt coulomb volt farad ohm siemens
    weber tesla henry degreeCelsius celsius radian steradian lumen lux becquerel gray sievert katal minute hour day litre liter
    tonne electronvolt dalton atomicmassunit neper bel decibel percent angstrom arcminute arcsecond hectare astronomicalunit
"""
# Las unidades y prefijos de siunitx solo estan definidos dentro de sus comandos (\SI{10}{\ohm}); sueltos en una formula
# (`10\,\ohm`) detienen TeX. Fuera de esos argumentos se escriben con su simbolo.
_ARGUMENTOS_SIUNITX = re.compile(r"\\(?:SIrange|SIlist|SI|si|qtyrange|qty|unit|numrange|numlist|num|ang)(?![A-Za-z])\s*(?:\[[^\]]*\])?"
                                 r"(?:\s*\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})+")
_UNIDADES_SIUNITX = {
    **{n: rf"\mathrm{{{s}}}" for n, s in (
        ("meter", "m"), ("metre", "m"), ("gram", "g"), ("kilogram", "kg"), ("second", "s"), ("ampere", "A"), ("kelvin", "K"),
        ("mole", "mol"), ("candela", "cd"), ("hertz", "Hz"), ("newton", "N"), ("pascal", "Pa"), ("joule", "J"), ("watt", "W"),
        ("coulomb", "C"), ("volt", "V"), ("farad", "F"), ("siemens", "S"), ("weber", "Wb"), ("tesla", "T"), ("henry", "H"),
        ("radian", "rad"), ("steradian", "sr"), ("lumen", "lm"), ("lux", "lx"), ("becquerel", "Bq"), ("gray", "Gy"), ("sievert", "Sv"),
        ("katal", "kat"), ("minute", "min"), ("hour", "h"), ("day", "d"), ("litre", "L"), ("liter", "L"), ("tonne", "t"),
        ("electronvolt", "eV"), ("dalton", "Da"), ("atomicmassunit", "u"), ("neper", "Np"), ("bel", "B"), ("decibel", "dB"),
        ("hectare", "ha"), ("astronomicalunit", "au"),
        ("yocto", "y"), ("zepto", "z"), ("atto", "a"), ("femto", "f"), ("pico", "p"), ("nano", "n"), ("milli", "m"), ("centi", "c"),
        ("deci", "d"), ("deca", "da"), ("hecto", "h"), ("kilo", "k"), ("mega", "M"), ("giga", "G"), ("tera", "T"), ("peta", "P"),
        ("exa", "E"), ("zetta", "Z"), ("yotta", "Y"))},
    "ohm": r"\Omega", "micro": r"\mu", "degree": r"^{\circ}", "degreeCelsius": r"{}^{\circ}\mathrm{C}", "celsius": r"{}^{\circ}\mathrm{C}",
    "percent": r"\%", "angstrom": r"\text{\AA}", "arcminute": "'", "arcsecond": "''", "per": "/", "squared": "^{2}", "cubed": "^{3}",
    "cubic": "", "of": "", "raiseto": "^", "tothe": "^",
}

# Lo que el propio conversor emite dentro de una formula: los comandos de _SIMBOLOS y los que compone.
_EMITIDOS = {n for v in _SIMBOLOS.values() for n in re.findall(r"\\([A-Za-z]+)", v)} | {"text", "textbackslash", "textasciicircum", "mathrm"}
_COMANDOS_MATEMATICOS = frozenset(
    "".join((_GRIEGAS_Y_LETRAS, _SIMBOLOS_VARIOS, _OPERADORES, _RELACIONES, _FLECHAS, _ESTRUCTURAS, _DELIMITADORES,
             _TIPOGRAFIA, _ACENTOS, _ESPACIOS_Y_PUNTOS, _SIUNITX)).split()) | _EMITIDOS
_ENTORNOS_MATEMATICOS = frozenset("aligned alignedat gathered split cases dcases rcases array matrix pmatrix bmatrix Bmatrix vmatrix Vmatrix smallmatrix".split())
_SIMBOLOS_DE_CONTROL = frozenset(",;:!{}%$&_#| /\\")        # \, \; \: \! \{ \} \% \$ \& \_ \# \| \<espacio> \/ y \\ (salto de linea)
# Aunque alguien lo agregue a la lista, un comando con estos rasgos nunca se admite en una formula.
_SOSPECHOSO = re.compile(r"input|file|read|write|(?<!math)open|shell|@|^pdf|^lst|^verb", re.I)      # `\mathopen` es matematico
_ESTRUCTURA_MATE = re.compile(r"\\begin\{([A-Za-z*]+)\}|\\end\{([A-Za-z*]+)\}|\\left(?![A-Za-z])|\\right(?![A-Za-z])|\\\\|\\.|&", re.S)
_ARGUMENTO = r"(?:\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}|\\[A-Za-z]+|\\.|[^\s{}\\^_])"       # un argumento de subindice: {..}, \comando o un caracter
_SCRIPT = re.compile(r"\s*([\^_])\s*" + _ARGUMENTO)
_SECUENCIA_SCRIPTS = re.compile(r"(?:\s*(?<!\\)[\^_]\s*" + _ARGUMENTO + r")+")
_COMANDOS_TEXTO = re.compile(r"\\(?:text|textrm|textit|textbf|textsf|texttt|textnormal|textup|textmd|textsl|textsc|mbox)\s*\{")
_UN_ARGUMENTO = frozenset("""
    sqrt text textrm textit textbf textsf texttt textnormal mbox mathrm mathbf mathit mathsf mathtt mathcal mathbb mathfrak boldsymbol operatorname
    hat bar vec dot ddot dddot tilde acute grave breve check overline underline widehat widetilde overbrace underbrace overrightarrow overleftarrow
""".split())
_DOS_ARGUMENTOS = frozenset("frac dfrac tfrac cfrac binom dbinom tbinom overset underset stackrel".split())
_COMANDO_CON_ARGUMENTOS = re.compile(r"\\([A-Za-z]+)")
_SIGUIENTE_ARGUMENTO = re.compile(r"\s*" + _ARGUMENTO)
_ARGUMENTO_OPCIONAL = re.compile(r"\s*\[[^\]]*\]")


def _escapar_en_texto(tex: str) -> tuple[str, list[str]]:
    """(formula, problemas). Dentro de `\\text{...}` (modo texto) un `_` o un `^` da «Missing $ inserted» (`\\text{una_variable}`): se
    escapan, y las formulas `$...$` anidadas en el texto se respetan. Fuera de `\\text{}`, un `$` suelto (una formula no puede llevar el
    delimitador que la cierra) se escapa."""
    salida: list[str] = []
    problemas: list[str] = []
    nivel, finales, en_formula, i = 0, [], False, 0       # `finales`: el nivel de llaves al que vuelve cada \text{} abierto
    while i < len(tex):
        ch = tex[i]
        if ch == "\\":
            m = _COMANDOS_TEXTO.match(tex, i)
            if m:
                finales.append(nivel)
                nivel += 1
                en_formula = False
                salida.append(m.group(0))
                i = m.end()
                continue
            salida.append(tex[i:i + 2])
            i += 2
            continue
        if ch == "{":
            nivel += 1
        elif ch == "}":
            nivel -= 1
            if finales and nivel == finales[-1]:
                finales.pop()
                en_formula = False
        elif ch == "$":
            if not finales:
                salida.append("\\$")
                problemas.append("`$` suelto dentro de la fórmula")
                i += 1
                continue
            en_formula = not en_formula
        elif ch in "_^" and finales and not en_formula:
            salida.append("\\_" if ch == "_" else "\\^{}")
            problemas.append("`_` o `^` dentro de `\\text{}`")
            i += 1
            continue
        salida.append(ch)
        i += 1
    return "".join(salida), problemas


def _completar_argumentos(tex: str) -> tuple[str, bool]:
    """`\\frac{a}` sin su segundo argumento, `\\vec` al final: TeX se detiene. Los argumentos que faltan se rellenan con `{}`."""
    partes: list[str] = []
    pos, cambio = 0, False
    for m in _COMANDO_CON_ARGUMENTOS.finditer(tex):
        if m.start() < pos:
            continue
        n = 2 if m.group(1) in _DOS_ARGUMENTOS else 1 if m.group(1) in _UN_ARGUMENTO else 0
        if not n:
            continue
        k = m.end()
        if m.group(1) == "sqrt" and (opcional := _ARGUMENTO_OPCIONAL.match(tex, k)):
            k = opcional.end()
        faltan = 0
        for _ in range(n):
            siguiente = _SIGUIENTE_ARGUMENTO.match(tex, k)
            if siguiente:
                k = siguiente.end()
            else:
                faltan += 1
        if faltan:
            partes.append(tex[pos:k])
            partes.append("{}" * faltan)
            pos, cambio = k, True
    partes.append(tex[pos:])
    return "".join(partes), cambio


_TOKEN_MATE = re.compile(r"\\(?:([A-Za-z@]+)|(.))", re.S)      # \nombre, o \<un caracter> (`\\` incluido)


def _permitido(m: re.Match) -> bool:
    nombre, simbolo = m.group(1), m.group(2)
    if simbolo is not None:
        return simbolo in _SIMBOLOS_DE_CONTROL
    if nombre in ("begin", "end"):                       # solo los entornos matematicos de amsmath/mathtools
        entorno = re.match(r"\s*\{\s*([A-Za-z*]+)\s*\}", m.string[m.end():])
        return bool(entorno) and entorno.group(1) in _ENTORNOS_MATEMATICOS
    return nombre in _COMANDOS_MATEMATICOS and not _SOSPECHOSO.search(nombre)


def _como_se_muestra(m: re.Match) -> str:
    if m.group(2) is not None:
        return "\\" + m.group(2)
    entorno = re.match(r"\s*\{\s*([A-Za-z*]+)\s*\}", m.string[m.end():]) if m.group(1) in ("begin", "end") else None
    return f"\\{m.group(1)}{{{entorno.group(1)}}}" if entorno else "\\" + m.group(1)


def saltos_sueltos(formula: str) -> bool:
    """True si la formula tiene un `\\\\` (salto de linea) fuera de todo entorno con columnas (`aligned`, `cases`, `matrix`...): ahi TeX
    no lo admite, y hay que envolverla en un entorno (`gathered`) para que compile."""
    profundidad = 0
    for m in _ESTRUCTURA_MATE.finditer(formula):
        if m.group(1):
            profundidad += 1
        elif m.group(2):
            profundidad = max(0, profundidad - 1)
        elif m.group(0) == "\\\\" and profundidad == 0:
            return True
    return False


def comandos_no_permitidos(formula: str) -> list[str]:
    """Los comandos de `formula` que no son matematicos conocidos (ver _COMANDOS_MATEMATICOS)."""
    return sorted({_como_se_muestra(m) for m in _TOKEN_MATE.finditer(formula) if not _permitido(m)})


def _necesita_llaves(cmd: str) -> bool:
    """Un comando que termina en letra se pega al texto siguiente (\\geqx): se cierra con {}."""
    return cmd.startswith("\\") and cmd[-1].isalpha()


class Conversor:
    """Convierte Markdown en linea a LaTeX seguro y acumula los avisos (caracteres sin mapeo)."""

    def __init__(self) -> None:
        self.avisos: list[str] = []

    def _aviso(self, mensaje: str) -> None:
        if mensaje not in self.avisos:
            self.avisos.append(mensaje)

    # --- caracteres -----------------------------------------------------------------------------

    def _no_soportado(self, ch: str, modo_matematico: bool) -> str:
        marcador = f"[U+{ord(ch):04X}]"
        self._aviso(f"carácter sin equivalente LaTeX ({marcador} «{ch}»): se sustituyó por el marcador")
        return rf"\text{{{marcador}}}" if modo_matematico else rf"\textbf{{{marcador}}}"

    def _caracter_texto(self, ch: str) -> str:
        if ch in _ESPECIALES:
            return _ESPECIALES[ch]
        if ch in (_MARCA_INI, _MARCA_FIN):
            return ch                                  # marcadores internos de inline(): se restauran despues
        if ch in _IGNORAR:
            return ""
        if ch in _ESPACIOS:
            return _ESPACIOS[ch]
        if ord(ch) < 128:
            return ch if ch in "\n\t" or ord(ch) >= 32 else ""
        if ch in _TEXTO_COMO_COMANDO:
            return _TEXTO_COMO_COMANDO[ch]
        if soportado_por_inputenc(ch):
            return ch                                  # letra acentuada
        if ch in _SIMBOLOS:
            return rf"\ensuremath{{{_SIMBOLOS[ch]}}}"
        return self._no_soportado(ch, False)

    def escapar(self, texto: str) -> str:
        """Escapa texto plano para LaTeX (modo texto). Un \\$ \\% \\& \\_ \\# \\{ \\} ya escrito por el autor se respeta."""
        texto = texto.replace(_MARCA_DOLAR, _MARCA_ESCAPE + "$")
        salida: list[str] = []
        i = 0
        while i < len(texto):
            ch = texto[i]
            if ch == _MARCA_ESCAPE and i + 1 < len(texto):
                salida.append("\\" + texto[i + 1])
                i += 2
                continue
            salida.append(self._caracter_texto(ch))
            i += 1
        return "".join(salida)

    def _neutralizar(self, tex: str) -> str:
        """Dentro de una formula solo se admiten comandos matematicos conocidos: cualquier otro (y la notacion `^^`, que puede
        esconder cualquiera) se muestra como texto en lugar de ejecutarse, y queda un aviso."""
        hallados: list[str] = []
        if "^^" in tex:
            hallados.append("^^")
            tex = tex.replace("^^", r"\text{\textasciicircum{}\textasciicircum{}}")

        def sustituir(m: re.Match) -> str:
            if _permitido(m):
                return m.group(0)
            hallados.append(_como_se_muestra(m))
            if m.group(2) is not None:                       # `\<caracter>`: se muestra la barra y el caracter sigue
                return r"\text{\textbackslash{}}" + m.group(2)
            return rf"\text{{\textbackslash{{}}{m.group(1)}}}"

        tex = _TOKEN_MATE.sub(sustituir, tex)
        if hallados:
            self._aviso("fórmula con comandos que no son matemáticos conocidos (" + ", ".join(sorted(set(hallados)))
                        + "): lo que puede leer o escribir archivos o redefinir TeX no se ejecuta; se neutralizaron (salen como texto) "
                        "y hay que revisar la fórmula")
        return tex

    def _completar(self, tex: str, saltos: bool = False) -> str:
        """Una formula con la sintaxis a medias no compila: TeX se detiene con un error y el documento entero se pierde. Se completa lo
        minimo para que compile y queda un aviso, porque la formula hay que revisarla. Lo que se repara: una barra invertida suelta al
        final (escaparia el `$` que cierra), `%` y `#` sin escapar (un comentario se comeria el cierre; `#` es un parametro de macro), llaves
        sin cerrar o de mas, un `_` o un `^` dentro de `\\text{}`, un argumento que falta (`\\frac{a}`), un subindice o exponente sin argumento
        (`A_`) o repetido (`x_1_2`), un `&` o un `\\\\` fuera de un entorno con columnas (con `saltos` se conservan los `\\\\`: quien llama envuelve
        la formula en un entorno), un `\\begin` sin `\\end` (o un `\\end` que no corresponde) y un `\\left` sin `\\right` (o al reves)."""
        problemas: list[str] = []
        final = re.search(r"\\+$", tex)
        if final and len(final.group(0)) % 2:                              # una barra invertida suelta al final escaparia el `$` que cierra la formula
            tex = tex[:-1].rstrip()
            problemas.append("una barra invertida al final")
        sin_escapar = re.sub(r"(?<!\\)((?:\\\\)*)([%#])", r"\1\\\2", tex)
        if sin_escapar != tex:
            problemas.append("`%` o `#` sin escapar")
            tex = sin_escapar
        nivel, salida, i = 0, [], 0
        while i < len(tex):
            ch = tex[i]
            if ch == "\\" and i + 1 < len(tex):                            # `\{`, `\}` y `\\` no abren ni cierran nada
                salida.append(tex[i:i + 2])
                i += 2
                continue
            i += 1
            if ch == "{":
                nivel += 1
            elif ch == "}":
                if nivel == 0:
                    problemas.append("llaves `}` de mas")
                    continue                                                # una llave que nada abrio se omite
                nivel -= 1
            salida.append(ch)
        tex = "".join(salida)
        if nivel:
            problemas.append("llaves `{` sin cerrar")
            tex += "}" * nivel
        tex, extra = _escapar_en_texto(tex)
        problemas.extend(extra)
        tex, cambio = _completar_argumentos(tex)
        if cambio:
            problemas.append("falta un argumento (`\\frac{a}`, `\\vec`...)")

        entornos: list[str] = []
        izquierdas = 0
        partes: list[str] = []
        pos = 0
        for m in _ESTRUCTURA_MATE.finditer(tex):
            partes.append(tex[pos:m.start()])
            pos = m.end()
            token = m.group(0)
            if m.group(1):                                                  # \begin{x}
                entornos.append(m.group(1))
                partes.append(token)
            elif m.group(2):                                                # \end{x}
                if m.group(2) not in entornos:
                    problemas.append("`\\end` sin su `\\begin`")             # se omite
                    continue
                while entornos[-1] != m.group(2):
                    problemas.append("`\\begin` sin su `\\end`")
                    partes.append("\\end{" + entornos.pop() + "}")
                entornos.pop()
                partes.append(token)
            elif token == "\\left":
                izquierdas += 1
                partes.append(token)
            elif token == "\\right":
                if not izquierdas:
                    problemas.append("`\\right` sin su `\\left`")
                    partes.append("\\left.")
                else:
                    izquierdas -= 1
                partes.append(token)
            elif token == "&" and not entornos:
                problemas.append("`&` fuera de un entorno con columnas")
                partes.append("\\&")
            elif token == "\\\\" and not entornos and not saltos:
                problemas.append("salto de línea `\\\\` fuera de un entorno")
                partes.append("\\quad{}")
            else:
                partes.append(token)
        partes.append(tex[pos:])
        tex = "".join(partes)
        if entornos:
            problemas.append("`\\begin` sin su `\\end`")
            tex += "".join("\\end{" + e + "}" for e in reversed(entornos))
        if izquierdas:
            problemas.append("`\\left` sin su `\\right`")
            tex += "\\right." * izquierdas

        completa = re.sub(r"(?<!\\)([\^_])(\s*)(?=$|[}&]|\\\\|\\end\b|\\right\b)", r"\1{}\2", tex)
        if completa != tex:
            problemas.append("subindice o exponente sin argumento")
            tex = completa

        def sin_repetidos(m: re.Match) -> str:
            vistos: set[str] = set()
            resultado = []
            for g in _SCRIPT.finditer(m.group(0)):
                if g.group(1) in vistos:
                    resultado.append("{}")                                  # `x_1_2` -> `x_1{}_2`: cada uno lleva su propia base
                    vistos.clear()
                    problemas.append("subindice o exponente repetido")
                vistos.add(g.group(1))
                resultado.append(g.group(0))
            return "".join(resultado)

        tex = _SECUENCIA_SCRIPTS.sub(sin_repetidos, tex)
        if problemas:
            self._aviso("fórmula con sintaxis incompleta (" + ", ".join(dict.fromkeys(problemas)) + "): se completó lo mínimo para que compile; hay que revisarla")
        return tex

    def _unidades_sueltas(self, tex: str) -> str:
        """Las unidades de siunitx (`\\ohm`, `\\volt`, `\\milli`...) solo existen DENTRO de `\\SI{}{}`, `\\si{}`, `\\qty{}{}` o `\\unit{}`:
        sueltas en una formula son una secuencia indefinida y TeX se detiene. Fuera de esos argumentos se cambian por su simbolo."""
        protegidos: list[str] = []

        def proteger(m: re.Match) -> str:
            protegidos.append(m.group(0))
            return f"{len(protegidos) - 1}"

        tex = _ARGUMENTOS_SIUNITX.sub(proteger, tex)
        cambiadas: list[str] = []

        def cambiar(m: re.Match) -> str:
            if m.group(1) not in _UNIDADES_SIUNITX:
                return m.group(0)
            cambiadas.append("\\" + m.group(1))
            return _UNIDADES_SIUNITX[m.group(1)]

        tex = re.sub(r"\\([A-Za-z]+)(?![A-Za-z])", cambiar, tex)
        if cambiadas:
            self._aviso("unidades de siunitx fuera de \\SI{}{} (" + ", ".join(sorted(set(cambiadas))) + "): se escribieron con su símbolo")
        return re.sub("(\\d+)", lambda m: protegidos[int(m.group(1))], tex)

    def matematicas(self, tex: str, saltos: bool = False) -> str:
        """El contenido de una formula se deja tal cual, salvo los caracteres Unicode que pdfLaTeX no soporta, los comandos que
        no son matematicos conocidos (que se neutralizan y dejan un aviso), las unidades de siunitx sueltas (que pasan a su simbolo)
        y la sintaxis a medias (que se completa, con aviso)."""
        tex = self._completar(self._unidades_sueltas(self._neutralizar(tex.replace(_MARCA_DOLAR, r"\$"))), saltos)
        # `\%` en modo matematico rompe la compilacion con babel espanol si le precede un espacio matematico (`100\,\%`,
        # `\;\%`, `\quad`...): babel redefine `\%` y mira `\lastskip`, que ahi es un muglue («Incompatible glue units»). Con
        # `\text{\%}` compila igual (y babel pone su espacio antes del signo).
        tex = re.sub(r"(?<!\\)((?:\\\\)*)\\%", r"\1\\text{\\%}", tex)
        salida: list[str] = []
        for ch in tex:
            if ord(ch) < 128:
                salida.append(ch)
            elif ch in _IGNORAR:
                continue
            elif ch in _ESPACIOS:
                salida.append(" ")
            elif ch in _SIMBOLOS:
                cmd = _SIMBOLOS[ch]
                salida.append(cmd + "{}" if _necesita_llaves(cmd) else cmd)
            elif soportado_por_inputenc(ch) and ch.isalpha():
                salida.append(rf"\text{{{ch}}}")        # letra acentuada dentro de una formula
            else:
                salida.append(self._no_soportado(ch, True))
        return "".join(salida)

    # --- Markdown en linea ------------------------------------------------------------------------

    def inline(self, md: str) -> str:
        """Markdown en linea (negrita, cursiva, codigo, formulas, enlaces) -> LaTeX."""
        guardados: list[str] = []

        def guardar(latex: str) -> str:
            guardados.append(latex)
            return f"{_MARCA_INI}{len(guardados) - 1}{_MARCA_FIN}"

        s = re.sub(r"<br\s*/?>", " ", md)
        s = s.replace("\\$", _MARCA_DOLAR)
        s = _MATH_DISPLAY.sub(lambda m: guardar(r"$\displaystyle " + self.matematicas(m.group(1).strip()) + "$"), s)
        s = _PARENS_MATH.sub(lambda m: guardar("$" + self.matematicas(m.group(1).strip()) + "$"), s)
        s = re.sub(r"`([^`\n]+)`", lambda m: guardar(r"\texttt{" + self.escapar(m.group(1)) + "}"), s)
        s = _MATH_INLINE.sub(lambda m: guardar("$" + self.matematicas(m.group(1)) + "$"), s)
        s = _IMAGEN.sub(lambda m: m.group(1), s)
        s = _ENLACE_MD.sub(lambda m: m.group(1), s)
        s = _ENLACE_WIKI_ALIAS.sub(lambda m: m.group(2), s)
        s = _ENLACE_WIKI.sub(lambda m: m.group(1), s)
        s = re.sub(r'"([^"\n]+)"', "«\\1»", s)
        s = s.replace('"', guardar(r"\textquotedbl{}"))
        # Un backslash que el autor dejo ante un especial de LaTeX se respeta; cualquier otro se muestra literal.
        s = re.sub(r"\\([%&_#{}])", lambda m: _MARCA_ESCAPE + m.group(1), s)
        s = self.escapar(s)
        s = _NEGRITA.sub(r"\\textbf{\1}", s)
        s = _CURSIVA.sub(r"\\textit{\1}", s)
        return re.sub(f"{_MARCA_INI}(\\d+){_MARCA_FIN}", lambda m: guardados[int(m.group(1))], s)

    def titulo(self, md: str) -> str:
        """Titulo de diapositiva o de seccion: sin marcas de enfasis (van tambien al indice y a los marcadores)."""
        plano = re.sub(r"[*`]", "", md)
        plano = _ENLACE_WIKI_ALIAS.sub(lambda m: m.group(2), plano)
        plano = _ENLACE_WIKI.sub(lambda m: m.group(1), plano)
        return self.escapar(plano.replace("\\$", _MARCA_DOLAR)).strip()


# ---------------------------------------------------------------------------
# Codigo y figuras
# ---------------------------------------------------------------------------


_LENGUAJES_LISTINGS = {"python": "Python", "py": "Python", "c": "C", "cpp": "C++", "c++": "C++", "bash": "bash",
                       "sh": "bash", "vhdl": "VHDL", "java": "Java", "matlab": "Matlab"}
_ASCII_CODIGO = {
    "─": "-", "━": "-", "│": "|", "┃": "|", "═": "=", "║": "|", "▼": "v", "▲": "^", "►": ">", "▶": ">", "◄": "<", "◀": "<",
    "→": "->", "←": "<-", "↔": "<->", "⇒": "=>", "≥": ">=", "≤": "<=", "≠": "!=", "×": "x", "•": "*", "“": '"', "”": '"',
    "‘": "'", "’": "'", "–": "-", "—": "-", "…": "...", "\u00b5": "u", "°": "o", "¿": "?", "¡": "!", "·": ".", "−": "-",
}
for _c in "┌┐└┘├┤┬┴┼╭╮╰╯╔╗╚╝╠╣╦╩╬":
    _ASCII_CODIGO[_c] = "+"


def ascii_codigo(linea: str) -> str:
    """El codigo va en lstlisting, que con pdfLaTeX no admite Unicode: se transliteran los diagramas ASCII y las tildes."""
    salida = []
    for ch in linea.replace("\t", "  "):
        if ord(ch) < 128:
            salida.append(ch)
        elif ch in _ASCII_CODIGO:
            salida.append(_ASCII_CODIGO[ch])
        else:
            base = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode()
            salida.append(base or "?")
    # `\end{lstlisting}` en una linea de codigo cerraria el entorno, y `\end{frame}` cerraria la diapositiva [fragile] (Beamer busca
    # esa linea al leer el marco): lo que siguiera se ejecutaria como TeX. Con un espacio ya no es el cierre y se ve casi igual.
    return "".join(salida).rstrip().replace("\\end{lstlisting}", "\\end {lstlisting}").replace("\\end{frame}", "\\end {frame}")


def dimensiones_png(ruta: Path) -> tuple[int, int] | None:
    """(ancho, alto) en pixeles de un PNG, leido de su cabecera IHDR (sin librerias); None si no es un PNG legible."""
    try:
        with open(ruta, "rb") as f:
            cabecera = f.read(24)
    except OSError:
        return None
    if len(cabecera) < 24 or cabecera[:8] != b"\x89PNG\r\n\x1a\n" or cabecera[12:16] != b"IHDR":
        return None
    ancho, alto = struct.unpack(">II", cabecera[16:24])
    return (ancho, alto) if ancho and alto else None


# ---------------------------------------------------------------------------
# El LaTeX que escribe el modelo (PRESENTACIONES): lista de PERMITIDOS para todo el cuerpo de una diapositiva
# ---------------------------------------------------------------------------
#
# Desde el diseno 5 el modelo escribe el cuerpo de cada diapositiva en LaTeX (TikZ, pgfplots, tcolorbox, tablas), como en las
# presentaciones de ejemplo del docente. Ese texto se compila, asi que se trata como las formulas: solo se admiten los comandos y
# entornos de estas listas (texto, TikZ, pgfplots, circuitikz, las cajas del diseno y los comandos matematicos de arriba), y todo
# lo demas —\input, \write18, \def, \csname, \catcode, \includegraphics, \usepackage...— devuelve la diapositiva al modelo con el
# motivo. Encima de la lista van las claves que leen o escriben archivos o llaman al sistema (`\addplot table {archivo}`,
# `\addplot gnuplot`, `saveto=`, `listing file=`, `escapeinside=`...), que tampoco se admiten aunque los comandos sean conocidos.

_TEXTO_LATEX = """
    textbf textit textsl textsc textup textmd textnormal textrm textsf texttt emph underline textcolor color colorbox fcolorbox
    textsuperscript textsubscript tiny scriptsize footnotesize small normalsize large Large LARGE huge Huge bfseries itshape
    slshape scshape mdseries upshape normalfont ttfamily sffamily rmfamily fontsize selectfont centering raggedright raggedleft
    par newline linebreak nolinebreak vspace hspace vfill hfill smallskip medskip bigskip quad qquad enspace thinspace noindent
    strut mbox makebox parbox raisebox rule item setlength addtolength itemsep parskip parsep topsep partopsep leftmargin labelsep
    labelwidth itemindent tabcolsep arraystretch arrayrulewidth linewidth textwidth textheight paperwidth paperheight columnwidth
    baselineskip hyphenpenalty exhyphenpenalty tolerance rowcolors rowcolor cellcolor hline cline toprule midrule bottomrule
    cmidrule addlinespace multicolumn multirow arraybackslash tabularnewline ldots dots textbullet textendash textemdash
    textquotedblleft textquotedblright textquoteleft textquoteright guillemotleft guillemotright textquestiondown textexclamdown
    textperiodcentered textdegree textpm texttimes textdiv textmu textonehalf textcopyright textregistered texttrademark texteuro
    dag ddag textasciitilde textasciicircum textbackslash textunderscore textbar textless textgreater checkmark alert structure
    column tcblower hd thc cod
"""
_TIKZ = """
    tikz node draw fill filldraw path coordinate foreach clip shade shadedraw useasboundingbox pic pgfmathsetmacro
    pgfmathtruncatemacro pgfmathparse pgfmathresult pgfmathprintnumber addplot addlegendentry legend closedcycle
"""
COMANDOS_CUERPO = frozenset((_TEXTO_LATEX + _TIKZ).split()) | _COMANDOS_MATEMATICOS
ENTORNOS_CUERPO = frozenset("""
    itemize enumerate description columns column center flushleft flushright minipage quote tabular tabularx tikzpicture scope
    axis semilogxaxis semilogyaxis loglogaxis circuitikz caja cajaplana cardB cardO cardG cardN codebox block alertblock
    exampleblock adjustbox equation equation* align align* gather gather* multline multline*
""".split()) | _ENTORNOS_MATEMATICOS
# Nombres que no se admiten como variable de un \foreach o de \pgfmathsetmacro: dentro del bucle redefinirian el comando, y fuera
# de el volverian a ser el primitivo (y la lista de permitidos los dejaria pasar por ser «variables»). Algunos (\item, \par,
# \begin) si se admiten como comando.
_NUNCA = _PRIMITIVAS_PELIGROSAS | frozenset("""
    csname endcsname expandafter noexpand string detokenize uppercase lowercase lccode uccode sfcode mathcode delcode everyeof
    everypar everyjob everymath everydisplay everyhbox everyvbox everycr output shipout endinput directlua primitive afterassignment
    aftergroup global long outer protected DeclareRobustCommand makeatletter makeatother documentclass typein typeout message
    errmessage batchmode nonstopmode scrollmode errorstopmode jobname begin end relax item par pgfkeys tikzexternalize
""".split())
_CLAVES_PROHIBIDAS = re.compile(
    r"(?<![A-Za-z])(saveto|savelowerto|saveupperto|record|recording|externalize|external|escapeinside|escapechar|escapebegin|escapeend"
    r"|mathescape|texcl|moredelim|morecomment|deletecomment|file|listing\s+file|input\s+file)\s*(=|\{)", re.I)
_TOKEN_CUERPO = re.compile(r"\\\\|\\([A-Za-z]+)|\\(.)", re.S)
_ENTORNO = re.compile(r"\\(begin|end)(?![A-Za-z])\s*(?:\{([^{}]*)\})?")
_FOREACH_VARIABLES = re.compile(r"\\foreach[ \t]*((?:\\[A-Za-z]+[ \t]*/?[ \t]*)+)")      # en una linea: el cuerpo y el documento ven lo mismo
_FOREACH_OPCIONES = re.compile(r"(?:count|evaluate|remember)\s*=\s*\\([A-Za-z]+)|(?<![A-Za-z])as\s*\\([A-Za-z]+)")
_MACRO_PGF = re.compile(r"\\pgfmath(?:set|truncate)macro\s*\{?\s*\\([A-Za-z]+)")
_ARRAYSTRETCH = re.compile(r"\\renewcommand\s*\{\\arraystretch\}\s*\{[\d.]+\}")
_CODEBOX = re.compile(r"\\begin\{codebox\}[ \t]*(?:\[([^\]\n]*)\])?[ \t]*\{([^\n]*)\}[ \t]*\n(.*?)\n?[ \t]*\\end\{codebox\}", re.S)
_OPCIONES_CODEBOX = re.compile(r"\s*(?:(?:language\s*=\s*[A-Za-z][A-Za-z0-9+]*|firstnumber\s*=\s*\d+)\s*(?:,\s*|$))*")
MAX_LINEAS_CODIGO = 22
MAX_CUERPO = 6000
_MARCA_CODIGO = "\ue020{}\ue021"           # donde va cada bloque de codigo mientras se revisa el resto


def _escapado(texto: str, i: int) -> bool:
    """True si el caracter en `i` va precedido por un numero impar de barras invertidas (\\% es un %; \\\\% es un salto y un comentario)."""
    n = 0
    while i - n - 1 >= 0 and texto[i - n - 1] == "\\":
        n += 1
    return n % 2 == 1


def _sin_escapar(texto: str, caracter: str) -> list[int]:
    return [i for i, c in enumerate(texto) if c == caracter and not _escapado(texto, i)]


_VARIABLE_SOSPECHOSA = re.compile(r"input|file|read|write|open|shell|^pdf|^lst|^verb$|^verbatim", re.I)


def _variable_segura(nombre: str) -> bool:
    """Un nombre que el texto puede usar como variable: no es un primitivo ni un comando que lea, escriba o ejecute (a diferencia de
    los comandos, `\\verbo` si vale: solo \\verb y \\verbatim leen su argumento literal)."""
    return nombre not in _NUNCA and not _VARIABLE_SOSPECHOSA.search(nombre)


def variables_locales(texto: str) -> set[str]:
    """Los nombres que el propio texto define como variables: las de un \\foreach (`\\foreach \\x/\\c in`, `count=\\i`, `as \\y`) y
    las de \\pgfmathsetmacro / \\pgfmathtruncatemacro."""
    nombres: set[str] = set()
    for m in _FOREACH_VARIABLES.finditer(texto):
        nombres |= set(re.findall(r"\\([A-Za-z]+)", m.group(1)))
    for m in _FOREACH_OPCIONES.finditer(texto):
        nombres.add(m.group(1) or m.group(2))
    nombres |= set(_MACRO_PGF.findall(texto))
    return nombres


def _fuente_addplot(texto: str, inicio: int) -> str:
    """Lo que sigue a un \\addplot (tras `3`, `+` y sus opciones [...]): `coordinates`, `{` (una expresion)... o `table`, `file`,
    `gnuplot`, `shell`, `graphics`, que leen archivos o llaman a programas."""
    i = inicio
    while i < len(texto) and (texto[i].isspace() or texto[i] in "3+"):
        i += 1
    if i < len(texto) and texto[i] == "[":
        profundidad = 0
        while i < len(texto):
            profundidad += (texto[i] == "[") - (texto[i] == "]")
            i += 1
            if profundidad == 0:
                break
    while i < len(texto) and texto[i].isspace():
        i += 1
    m = re.match(r"[A-Za-z]+|.", texto[i:], re.S)
    return m.group(0) if m else ""


def comandos_no_admitidos(texto: str, extra: frozenset[str] = frozenset(), entornos_extra: frozenset[str] = frozenset()) -> list[str]:
    """Los comandos y entornos de `texto` que no estan en la lista de permitidos del cuerpo de una diapositiva (COMANDOS_CUERPO,
    ENTORNOS_CUERPO; mas `extra`), y las variables de \\foreach o \\pgfmathsetmacro con nombre de un comando peligroso. Un comando de
    una letra (\\c, \\x, \\y: acentos o variables de TikZ) se admite; las variables que el propio texto define, tambien."""
    todas = variables_locales(texto)
    locales = {n for n in todas if _variable_segura(n)}
    malos: set[str] = {f"\\{n} (como variable)" for n in todas - locales}
    for m in _TOKEN_CUERPO.finditer(texto):
        nombre = m.group(1)
        if not nombre:                               # \\ o un simbolo de control (\, \% \{ \$ ...): no ejecutan nada
            continue
        if nombre in ("begin", "end"):
            entorno = _ENTORNO.match(texto, m.start())
            env = entorno.group(2) if entorno and entorno.group(2) is not None else None
            if env is None or env.strip() not in ENTORNOS_CUERPO | entornos_extra:
                malos.add(f"\\{nombre}{{{env if env is not None else '?'}}}")
            continue
        if nombre in locales:                        # una variable del propio texto (\verbo en un \foreach de los ejemplos)
            continue
        if _SOSPECHOSO.search(nombre) or nombre in _PRIMITIVAS_PELIGROSAS:
            malos.add("\\" + nombre)
        elif not (nombre in COMANDOS_CUERPO or nombre in extra or len(nombre) == 1):
            malos.add("\\" + nombre)
    return sorted(malos)


def _unicode_en_latex(texto: str) -> tuple[str, list[str]]:
    """Los caracteres que pdfLaTeX no compila con inputenc: un simbolo conocido sale como \\ensuremath{comando} (sirve en texto y
    en una formula); las marcas invisibles se quitan; lo demas se informa."""
    salida, raros = [], []
    for ch in texto:
        if ord(ch) < 128 or soportado_por_inputenc(ch) or ch in "\ue020\ue021":
            salida.append(ch)
        elif ch in _IGNORAR:
            continue
        elif ch in _ESPACIOS:
            salida.append(_ESPACIOS[ch])
        elif ch in _SIMBOLOS:
            salida.append(rf"\ensuremath{{{_SIMBOLOS[ch]}}}")
        elif ch in _TEXTO_COMO_COMANDO:
            salida.append(_TEXTO_COMO_COMANDO[ch])
        else:
            raros.append(f"U+{ord(ch):04X} ({ch})")
            salida.append("?")
    return "".join(salida), sorted(set(raros))


def _unir_lineas(texto: str) -> str:
    """Un % al final de una linea (`{...Comprender,%` en los \\foreach de los ejemplos del docente) une esa linea con la siguiente:
    TeX se come el % y el salto, y los espacios al comienzo de la linea siguiente. Se hace lo mismo, sin cambiar el sentido."""
    salida: list[str] = []
    pegar = False                                   # la linea anterior termino en %: esta se pega a ella
    for linea in texto.split("\n"):
        if pegar:
            linea = linea.lstrip(" \t")
        limpia = linea.rstrip(" \t")
        termina = limpia.endswith("%") and not _escapado(limpia, len(limpia) - 1)
        actual = limpia[:-1] if termina else linea
        if pegar:
            salida[-1] += actual
        else:
            salida.append(actual)
        pegar = termina
    return "\n".join(salida)


def _balance(texto: str) -> list[str]:
    problemas = []
    profundidad = 0
    for i, c in enumerate(texto):
        if c in "{}" and not _escapado(texto, i):
            profundidad += 1 if c == "{" else -1
            if profundidad < 0:
                break
    if profundidad != 0:
        problemas.append("llaves { } sin balancear")
    pila: list[str] = []
    for m in re.finditer(r"\\(begin|end)\{([^{}]*)\}", texto):
        if m.group(1) == "begin":
            pila.append(m.group(2))
        elif not pila or pila.pop() != m.group(2):
            problemas.append(f"\\end{{{m.group(2)}}} no corresponde con su \\begin")
            break
    else:
        if pila:
            problemas.append("entornos sin cerrar: " + ", ".join(pila))
    if len(_sin_escapar(texto, "$")) % 2:
        problemas.append("un número impar de signos $ (una fórmula sin cerrar)")
    return problemas


def _problemas_de_claves(texto: str) -> list[str]:
    problemas = []
    for m in _CLAVES_PROHIBIDAS.finditer(texto):
        problemas.append(f"la opción `{m.group(1)}` (lee o escribe archivos): no se admite")
    for m in re.finditer(r"\\addplot(?![A-Za-z])", texto):
        fuente = _fuente_addplot(texto, m.end())
        if fuente not in ("coordinates", "expression", "{", "(") :
            problemas.append(f"`\\addplot {fuente}`: los datos de una gráfica van con `coordinates {{(x,y) ...}}` o una expresión entre llaves "
                             "(`table`, `file`, `gnuplot`, `shell` o `graphics` leen archivos o llaman a programas)")
    if "^^" in texto:
        problemas.append("la notación ^^ de TeX (puede esconder un comando): no se admite")
    return problemas


# ---------------------------------------------------------------------------
# Opciones (claves) de TikZ, pgfplots, circuitikz, tcolorbox y adjustbox: tambien con lista de PERMITIDOS
# ---------------------------------------------------------------------------
#
# Los nombres de comandos y entornos ya van con lista de permitidos, pero estos paquetes tambien actuan a traves de sus claves:
# `execute at begin node={...}`, `every axis/.append code={...}`, `external/system call=...`, `saveto=archivo`... Por eso cada
# opcion [...] que TikZ, pgfplots, circuitikz, tcolorbox o adjustbox interpretan pasa por esta lista: colores, grosores, los
# estilos del diseno, posiciones, anclas, tamanos, fuentes, formas, las claves de ejes y leyendas de pgfplots que usan los ejemplos
# del docente y los componentes y etiquetas de circuitikz. Una clave desconocida devuelve la diapositiva al modelo. Los manejadores
# de pgfkeys (`/.code`, `/.style`, `/.append style`, `/.store in`, `/.initial`, `/.expanded`, `/.cd`...) no se admiten en ningun
# lugar del cuerpo: con ellos se define comportamiento nuevo. _CLAVES_PROHIBIDAS queda como segunda capa.

def _lista_de_claves(texto: str) -> frozenset[str]:
    return frozenset(" ".join(k.split()) for k in texto.replace("\n", ",").split(",") if k.strip())


CLAVES_PERMITIDAS = _lista_de_claves("""
    color, draw, fill, text, opacity, fill opacity, draw opacity, text opacity, line width, thin, very thin, ultra thin, semithick,
    thick, very thick, ultra thick, solid, dashed, densely dashed, loosely dashed, dotted, densely dotted, loosely dotted,
    dash pattern, dash dot, line cap, line join, rounded corners, sharp corners, double, double distance, shorten >, shorten <,
    bloque, box, bB, bO, bG, bN, flecha, arr, nodo, term, cable, dec, tag,
    anchor, above, below, left, right, above left, above right, below left, below right, centered, at, pos, midway, near start,
    near end, very near start, very near end, at start, at end, sloped, auto, swap, node distance, on grid, xshift, yshift, shift,
    x, y, scale, xscale, yscale, rotate, transform shape, remember picture, overlay, baseline, name, label, pin,
    inner sep, inner xsep, inner ysep, outer sep, minimum size, minimum width, minimum height, text width, text height, text depth,
    align, font, text centered, rectangle, circle, ellipse, diamond, aspect, isosceles triangle, isosceles triangle apex angle,
    trapezium, trapezium angle, regular polygon, regular polygon sides, star, star points, cylinder, shape, fit,
    rounded rectangle, chamfered rectangle, cross out, strike out,
    decorate, decoration, brace, amplitude, mirror, raise, zigzag, snake, coil, segment length,
    bend left, bend right, out, in, looseness, radius, x radius, y radius, start angle, end angle, delta angle, step,
    level distance, sibling distance, grow, grow', edge from parent path, child anchor, parent anchor, nodes, postaction,
    preaction, on background layer, behind path, smooth, tension, samples, domain, variable, mark, mark size, mark options,
    only marks, no marks, no markers, sharp plot, const plot, count, evaluate, remember, parse,
    width, height, scale only axis, xmin, xmax, ymin, ymax, zmin, zmax, xtick, ytick, xticklabels, yticklabels, xtick distance,
    ytick distance, extra x ticks, extra y ticks, extra tick style, minor tick num, minor x tick num, minor y tick num,
    xlabel, ylabel, title, xmode, ymode, log basis x, log basis y, axis lines, axis lines*, axis x line, axis y line,
    axis x line*, axis y line*, hide axis, axis on top, clip, enlargelimits, enlarge x limits, enlarge y limits, axis line style,
    tick style, tick label style, ticklabel style, xticklabel style, yticklabel style, x tick label style, y tick label style,
    label style, xlabel style, ylabel style, title style, xlabel near ticks, ylabel near ticks, tick align, major tick length,
    grid, grid style, major grid style, minor grid style, xmajorgrids, ymajorgrids, xminorgrids, yminorgrids, legend style,
    legend pos, legend entries, legend columns, legend cell align, legend image post style, x dir, y dir, symbolic x coords,
    symbolic y coords, xbar, ybar, bar width, bar shift, ybar stacked, xbar stacked, nodes near coords, nodes near coords align,
    nodes near coords style, point meta, samples at, restrict y to domain, restrict x to domain, unbounded coords,
    forget plot, scaled ticks, scaled x ticks, scaled y ticks, xticklabel pos, yticklabel pos, xtick pos, ytick pos,
    cycle list name, area legend, fill between, smooth,
    R, C, L, V, I, D, E, vR, vC, vL, pR, sR, thR, varistor, fuse, lamp, led, leD, battery, battery1, battery2, sV, cV, cI, sI,
    vsource, isource, american voltage source, american current source, european resistor, american resistor, generic,
    short, open, ammeter, voltmeter, ohmmeter, switch, spst, nos, ncs, push button, cute open switch, cute closed switch,
    Do, zD, sD, zzD, pD, tD, empty diode, full diode, stroke diode, opamp, op amp, nmos, pmos, nfet, pfet, npn, pnp, nigbt,
    pigbt, ground, sground, tlground, rground, cground, vcc, vee, circ, ocirc, diamondpole, squarepole,
    and port, or port, not port, nand port, nor port, xor port, xnor port, buffer port, american and port, american or port,
    american not port, american nand port, american nor port, american xor port, transformer, transformer core, inductor,
    cute inductor, american inductor, capacitor, polar capacitor, ecapacitor, crystal, antenna, speaker, mic, bulb, motor,
    elmech, sinusoidal voltage source, dcvsource, dcisource, bipoles/length,
    colback, colframe, coltext, coltitle, colbacktitle, title, fonttitle, fontupper, fontlower, left, right, top, bottom,
    boxsep, arc, boxrule, toprule, bottomrule, leftrule, rightrule, halign, valign, halign title, center title, enhanced,
    nobeforeafter, box align, equal height group, height fill, lefttitle, toptitle, bottomtitle, opacityback, opacityframe,
    opacitytext, drop shadow, before skip, after skip, left skip, right skip,
    max width, max height, max totalheight, totalheight, keepaspectratio, center, min width, min height
""")
# Las que tienen por valor otra lista de claves (se revisa igual) y las que tienen por valor un color (un estilo del diseno
# recibe su color como parametro: sin esta regla, `bloque={red, execute at begin node=...}` colaria claves por el valor).
_CLAVES_ANIDADAS = _lista_de_claves("""
    decoration, legend style, label style, tick label style, ticklabel style, xticklabel style, yticklabel style,
    x tick label style, y tick label style, xlabel style, ylabel style, title style, axis line style, tick style, grid style,
    major grid style, minor grid style, nodes near coords style, mark options, extra tick style, legend image post style, nodes,
    postaction, preaction
""")
_CLAVES_DE_COLOR = _lista_de_claves("""
    color, draw, fill, text, bloque, nodo, term, cable, tag, colback, colframe, coltext, coltitle, colbacktitle
""")
_COLORES_BASE = frozenset("""
    iubwhite iubnavy iubyellow iubblue iuborange iubgreen white black red green blue cyan magenta yellow gray darkgray lightgray
    brown lime olive orange pink purple teal violet none
""".split())
_PALABRAS_DE_FLECHA = frozenset("""
    Stealth Latex Triangle To Bar Bracket Circle Square Kite Straight Barb Rays Hooks Arc Tee Implies stealth latex to o d
    length width scale open round sep inset angle line reversed harpoon left right fill color bend pt cm mm em ex
""".split())
_ES_FLECHA = re.compile(r"^[\s{}\[\]A-Za-z0-9.=<>|*!-]+$")
_ETIQUETA_CIRCUITO = re.compile(r"^[lavif][_^<>]*[0-9]?$")      # l_=, a^=, i>=, v<=... de circuitikz
_DIMENSION = re.compile(r"^[+-]?\d*\.?\d+\s*(?:pt|cm|mm|em|ex|in|bp|sp)?$")
_MANEJADOR = re.compile(r"/\s*\.\s*([A-Za-z]+(?:\s+(?:style|code|in|value|initial|args))?)")
_ANTES_NO_ES_OPCION = re.compile(r"(?:\\\\\*?|\\(?:sqrt|item|makebox|framebox|parbox|raisebox|rule|qty|num|SI|si|unit|ang|column|newline))\s*$")


def _partir(texto: str, separador: str = ",") -> list[str]:
    """Parte por `separador` solo al nivel de arriba (fuera de {}, [] y ())."""
    partes, actual, nivel = [], [], 0
    for ch in texto:
        if ch in "{[(":
            nivel += 1
        elif ch in "}])":
            nivel -= 1
        if ch == separador and nivel == 0:
            partes.append("".join(actual))
            actual = []
        else:
            actual.append(ch)
    partes.append("".join(actual))
    return partes


def _igual_de_arriba(entrada: str) -> int:
    """La posicion del primer `=` fuera de {}, [] y () (en `-{Stealth[length=2mm]}` no hay ninguno), o -1."""
    nivel = 0
    for i, ch in enumerate(entrada):
        if ch in "{[(":
            nivel += 1
        elif ch in "}])":
            nivel -= 1
        elif ch == "=" and nivel == 0:
            return i
    return -1


def _sin_llaves(valor: str) -> str:
    valor = valor.strip()
    return valor[1:-1] if len(valor) >= 2 and valor[0] == "{" and valor[-1] == "}" else valor


def _variables_de_foreach(texto: str) -> dict[str, list[str]]:
    """{variable: valores} de cada \\foreach del texto (`\\foreach \\y/\\c in {0/iubblue, 1/iuborange}` -> {"c": ["iubblue", "iuborange"]})."""
    valores: dict[str, list[str]] = {}
    for m in re.finditer(r"\\foreach[ \t]*((?:\\[A-Za-z]+[ \t]*/?[ \t]*)+)(?:\[[^\]]*\])?\s*in\s*\{", texto):
        nombres = re.findall(r"\\([A-Za-z]+)", m.group(1))
        inicio, nivel, i = m.end(), 1, m.end()
        while i < len(texto) and nivel:
            nivel += (texto[i] == "{") - (texto[i] == "}")
            i += 1
        for item in _partir(texto[inicio:i - 1]):
            for nombre, valor in zip(nombres, _partir(item, "/")):
                valores.setdefault(nombre, []).append(_sin_llaves(valor))
    return valores


def _es_color(valor: str, variables: dict[str, list[str]], profundidad: int = 0) -> bool:
    valor = _sin_llaves(valor)
    variable = re.fullmatch(r"\\([A-Za-z]+)", valor)
    if variable:
        return profundidad == 0 and variable.group(1) in variables and all(_es_color(v, {}, 1) for v in variables[variable.group(1)])
    partes = valor.split("!")
    nombres = partes[0::2]
    numeros = partes[1::2]
    return (all(n.strip() in _COLORES_BASE or re.fullmatch(r"\\[A-Za-z]+", n.strip()) and _es_color(n.strip(), variables, profundidad) for n in nombres)
            and all(re.fullmatch(r"\s*\d{1,3}(?:\.\d+)?\s*", n) for n in numeros))


def _es_flecha(entrada: str) -> bool:
    return (bool(_ES_FLECHA.match(entrada)) and bool(re.search(r"[-<>]", entrada))
            and all(p in _PALABRAS_DE_FLECHA for p in re.findall(r"[A-Za-z]+", entrada)))


def _claves_malas(opciones: str, variables: dict[str, list[str]], profundidad: int = 0) -> list[str]:
    """Las entradas de una lista de opciones `a, b=c, ...` que no estan en la lista de permitidos."""
    malas: list[str] = []
    for entrada in _partir(opciones):
        entrada = entrada.strip()
        if not entrada:
            continue
        if _MANEJADOR.search(entrada):
            continue                                        # ya informado (se buscan en todo el texto)
        igual_en = _igual_de_arriba(entrada)
        clave, igual, valor = ((entrada[:igual_en].strip(), "=", entrada[igual_en + 1:].strip()) if igual_en >= 0 else (entrada, "", ""))
        clave = " ".join(clave.split())
        if not igual:                                       # una opcion sin valor: bandera, color, flecha, medida o variable
            variable = re.fullmatch(r"\\([A-Za-z]+)", clave)
            if clave in CLAVES_PERMITIDAS or _DIMENSION.match(clave) or _es_color(clave, variables) or _es_flecha(clave):
                continue
            if variable and variable.group(1) in variables and profundidad == 0 and all(
                    not _claves_malas(v, {}, 1) for v in variables[variable.group(1)]):
                continue
            malas.append(clave[:40])
            continue
        if clave not in CLAVES_PERMITIDAS and not _ETIQUETA_CIRCUITO.match(clave):
            malas.append(clave[:40])
        elif clave in _CLAVES_DE_COLOR and not _es_color(valor, variables):
            malas.append(f"{clave}={valor[:30]} (el valor tiene que ser un color)")
        elif clave in _CLAVES_ANIDADAS and profundidad < 3:
            malas += _claves_malas(_sin_llaves(valor), variables, profundidad + 1)
        elif clave in ("label", "pin") and _sin_llaves(valor).startswith("["):
            interior = _sin_llaves(valor)
            malas += _claves_malas(interior[1:interior.find("]")], variables, profundidad + 1)
    return malas


def _enmascarar_matematicas(texto: str) -> str:
    """Las formulas $...$ se reemplazan por un relleno del mismo largo: sus corchetes y comas no son opciones."""
    posiciones = _sin_escapar(texto, "$")
    salida = list(texto)
    for a, b in zip(posiciones[0::2], posiciones[1::2]):
        for k in range(a + 1, b):
            salida[k] = "x"
    return "".join(salida)


def _grupo(texto: str, inicio: int, abre: str, cierra: str) -> int:
    """El indice justo despues del grupo balanceado que abre en `inicio` (o len(texto) si no cierra)."""
    nivel, i = 0, inicio
    while i < len(texto):
        if texto[i] == abre and not _escapado(texto, i):
            nivel += 1
        elif texto[i] == cierra and not _escapado(texto, i):
            nivel -= 1
            if nivel == 0:
                return i + 1
        i += 1
    return len(texto)


def _regiones_graficas(texto: str) -> list[tuple[int, int]]:
    """Donde manda TikZ: cada entorno tikzpicture o circuitikz (con sus axis y scope) y cada \\tikz en linea."""
    regiones = []
    for m in re.finditer(r"\\begin\{(tikzpicture|circuitikz)\}", texto):
        fin = texto.find(f"\\end{{{m.group(1)}}}", m.end())
        regiones.append((m.start(), len(texto) if fin < 0 else fin))
    for m in re.finditer(r"\\tikz(?![A-Za-z])", texto):
        i = m.end()
        while i < len(texto) and texto[i].isspace():
            i += 1
        if i < len(texto) and texto[i] == "[":
            i = _grupo(texto, i, "[", "]")
        while i < len(texto) and texto[i].isspace():
            i += 1
        fin = _grupo(texto, i, "{", "}") if i < len(texto) and texto[i] == "{" else (texto.find(";", i) + 1 or len(texto))
        regiones.append((m.start(), fin))
    return regiones


def _tikz_sin_terminar(texto: str) -> bool:
    """Un \\tikz en linea sin llaves y sin `;`: TeX seguiria leyendo opciones en lo que viene despues (otras diapositivas)."""
    for m in re.finditer(r"\\tikz(?![A-Za-z])", texto):
        i = m.end()
        while i < len(texto) and texto[i].isspace():
            i += 1
        if i < len(texto) and texto[i] == "[":
            i = _grupo(texto, i, "[", "]")
        while i < len(texto) and texto[i].isspace():
            i += 1
        if not (i < len(texto) and texto[i] == "{") and ";" not in texto[i:]:
            return True
    return False


def opciones_no_admitidas(texto: str) -> list[str]:
    """Las claves de las opciones de TikZ, pgfplots, circuitikz, tcolorbox y adjustbox que no estan en CLAVES_PERMITIDAS, y los
    manejadores de pgfkeys (`/.code`, `/.style`...) en cualquier lugar del texto."""
    variables = _variables_de_foreach(texto)
    texto = _enmascarar_matematicas(texto)
    malas: list[str] = [f"/.{m.group(1)}" for m in _MANEJADOR.finditer(texto)]
    if _tikz_sin_terminar(texto):
        malas.append("\\tikz sin ; final")
    grupos: list[str] = []
    for a, b in _regiones_graficas(texto):
        i = a
        while i < b:
            if texto[i] == "[" and not _escapado(texto, i) and not _ANTES_NO_ES_OPCION.search(texto[max(0, i - 12):i]):
                fin = _grupo(texto, i, "[", "]")
                grupos.append(texto[i + 1:fin - 1])
                i = fin
            else:
                i += 1
    for m in re.finditer(r"\\foreach[ \t]*(?:\\[A-Za-z]+[ \t]*/?[ \t]*)+\[", texto):     # pgffor tambien fuera de TikZ
        grupos.append(texto[m.end():_grupo(texto, m.end() - 1, "[", "]") - 1])
    for m in re.finditer(r"\\begin\{(?:caja|cajaplana|card[BOGN])\}\s*\[", texto):
        grupos.append(texto[m.end():_grupo(texto, m.end() - 1, "[", "]") - 1])
    for m in re.finditer(r"\\begin\{adjustbox\}\s*\{", texto):
        grupos.append(texto[m.end():_grupo(texto, m.end() - 1, "{", "}") - 1])
    for grupo in grupos:
        malas += _claves_malas(grupo, variables)
    return sorted(set(malas))


def verificar_cuerpo(texto: str, titulo: bool = False) -> tuple[str, list[str]]:
    """(texto normalizado, problemas) del LaTeX que el modelo escribio para una diapositiva (o su titulo, con `titulo=True`).

    Normaliza sin cambiar el sentido: quita las lineas de comentario, pasa a \\ensuremath los simbolos Unicode que pdfLaTeX no
    compila y reescribe cada `codebox` en su forma canonica (el codigo transliterado a ASCII, con `\\end{frame}` y `\\end{codebox}`
    neutralizados, y solo las opciones `language=` y `firstnumber=`). Luego revisa: la lista de permitidos, las claves que leen o
    escriben archivos, ^^, llaves, entornos y $ balanceados, % y # sin escapar y el largo. Cualquier problema devuelve la
    diapositiva al modelo."""
    problemas: list[str] = []
    codigos: list[str] = []
    titulos_codigo: list[str] = []

    def guardar_codigo(m: re.Match) -> str:
        opciones, titulo_codigo, codigo = m.group(1) or "", m.group(2), m.group(3)
        # `[language=C, firstnumber=19]` o, como en los ejemplos del docente, `[listing options app={firstnumber=19}]`
        interior = re.fullmatch(r"\s*listing options app\s*=\s*\{([^{}]*)\}\s*", opciones)
        pares = interior.group(1) if interior else opciones
        if not _OPCIONES_CODEBOX.fullmatch(pares):
            problemas.append(f"opciones de codebox no admitidas: [{opciones}] (solo language=Nombre y firstnumber=N)")
        lineas = [ascii_codigo(l).replace("\\end{codebox}", "\\end {codebox}") for l in codigo.strip("\n").splitlines()]
        if len(lineas) > MAX_LINEAS_CODIGO:
            problemas.append(f"un codebox de {len(lineas)} líneas: el máximo es {MAX_LINEAS_CODIGO} (muestra el fragmento clave o repártelo en dos diapositivas)")
        limpias = ",".join(re.sub(r"\s*=\s*", "=", o.strip()) for o in pares.split(",") if o.strip())
        opciones_canonicas = f"[listing options app={{{limpias}}}]" if limpias else ""
        codigos.append(f"\\begin{{codebox}}{opciones_canonicas}{{{titulo_codigo}}}\n" + "\n".join(lineas) + "\n\\end{codebox}")
        titulos_codigo.append(titulo_codigo)               # el titulo si se compila: se revisa con el resto
        return _MARCA_CODIGO.format(len(codigos) - 1)

    texto = texto.replace("\r\n", "\n").replace("\r", "\n").strip()
    if titulo and "\n" in texto:
        problemas.append("el título va en una sola línea")
    texto = _CODEBOX.sub(guardar_codigo, texto)                        # primero el codigo: un `%` ahi es codigo (MATLAB), no comentario
    texto = re.sub(r"(?m)^[ \t]*%.*\n?", "", texto)                   # lineas de comentario
    texto = _unir_lineas(texto)
    if titulo and codigos:
        problemas.append("un título no lleva código")
    if re.search(r"\\(?:begin|end)\s*\{codebox\}", texto):
        problemas.append("cada codebox va así: `\\begin{codebox}[language=Python]{Título}` en su propia línea, el código debajo y "
                         "`\\end{codebox}` sola en su propia línea")
    texto, raros = _unicode_en_latex(texto)
    if raros:
        problemas.append("caracteres que pdfLaTeX no compila: " + ", ".join(raros[:8]) + " (escríbelos con su comando LaTeX)")
    revisable = _ARRAYSTRETCH.sub("", re.sub("\ue020\\d+\ue021", "", texto)) + "".join(f"\n{{{t}}}" for t in titulos_codigo)
    malos = comandos_no_admitidos(revisable)
    if malos:
        problemas.append("comandos o entornos no admitidos: " + ", ".join(malos[:12]) + " (usa solo LaTeX de texto, TikZ, pgfplots, "
                         "circuitikz, tablas y las cajas del diseño; sin \\def, \\newcommand, imágenes ni archivos)")
    opciones = opciones_no_admitidas(revisable)
    if opciones:
        problemas.append("opciones no admitidas: " + ", ".join(f"`{o}`" for o in opciones[:12]) + " (en TikZ, pgfplots, circuitikz y las cajas solo "
                         "se admiten colores, grosores, los estilos del diseño, posiciones, anclas, tamaños, fuentes, formas, claves de ejes y "
                         "leyendas y componentes de circuitos; nada de /.style, /.code ni otros manejadores de claves)")
    problemas += _problemas_de_claves(revisable)
    problemas += _balance(revisable)
    if _sin_escapar(revisable, "%"):
        problemas.append("un % sin escapar comenta el resto de la línea: el porcentaje se escribe \\% (y no escribas comentarios)")
    if _sin_escapar(revisable, "#"):
        problemas.append("un # sin escapar: escribe \\#")
    if len(texto) > MAX_CUERPO:
        problemas.append(f"la diapositiva tiene {len(texto)} caracteres de LaTeX: el máximo es {MAX_CUERPO} (divídela en dos)")
    salida = re.sub("\ue020(\\d+)\ue021", lambda m: "\n" + codigos[int(m.group(1))] + "\n", texto)
    return salida.strip(), problemas


# ---------------------------------------------------------------------------
# El .tex completo
# ---------------------------------------------------------------------------

# Los problemas de verificar_latex que significan que el .tex podria ejecutar algo (leer o escribir archivos, llamar a un programa):
# con ellos no se escribe ni se compila. Los demas (una llave suelta, un caracter sin soporte) solo impiden compilar o se ven mal.
PROBLEMAS_GRAVES = ("primitivas de TeX peligrosas", "comandos o entornos no admitidos", "notación ^^", "un bloque de código contiene",
                    "lee o escribe archivos", "leen archivos o llaman a programas", "opciones no admitidas")
_COMANDOS_DEL_DISENO = frozenset({"bloque", "section"})      # los que el diseno pone entre diapositivas (definidos en el preambulo)


def graves(problemas: list[str]) -> list[str]:
    """Los problemas de verificar_latex que hacen inseguro el .tex (ver PROBLEMAS_GRAVES)."""
    return [p for p in problemas if any(g in p for g in PROBLEMAS_GRAVES)]


def verificar_latex(tex: str) -> list[str]:
    """Comprobacion ESTATICA (no compila) del .tex completo, como segunda capa despues de verificar_cuerpo: el preambulo lo escribe el
    codigo; en el documento, todo comando y entorno tiene que estar en la lista de permitidos (mas \\bloque y \\section, y el entorno
    frame) y toda opcion de TikZ, pgfplots, circuitikz y las cajas en la lista de claves permitidas, sin manejadores de pgfkeys, sin
    claves que lean o escriban archivos ni ^^; ningun bloque de codigo contiene `\\end{frame}`; toda diapositiva con
    codigo es [fragile]; llaves y entornos balanceados y caracteres que pdfLaTeX compila."""
    problemas: list[str] = []
    for obligatorio in (r"\documentclass", r"\begin{document}", r"\end{document}"):
        if obligatorio not in tex:
            problemas.append(f"falta {obligatorio}")
    _, _, documento = tex.partition(r"\begin{document}")
    documento = documento.rpartition(r"\end{document}")[0]

    for marco in re.finditer(r"\\begin\{frame\}(\[[^\]]*\])?(.*?)\\end\{frame\}", documento, flags=re.S):
        if "\\begin{codebox}" in marco.group(2) and "fragile" not in (marco.group(1) or ""):
            problemas.append("una diapositiva con código no lleva [fragile]")
    for bloque in re.findall(r"\\begin\{codebox\}(.*?)\\end\{codebox\}", documento, flags=re.S):
        if "\\end{frame}" in bloque:                     # verificar_cuerpo lo escribe `\end {frame}`: aqui solo llega si algo se lo salto
            problemas.append("un bloque de código contiene «\\end{frame}»: cerraría la diapositiva [fragile] y lo que sigue se ejecutaría como TeX")
    # el codigo no se ejecuta: se revisa solo su linea de apertura (opciones y titulo)
    sin_codigo = re.sub(r"(\\begin\{codebox\}[^\n]*\n).*?(\\end\{codebox\})", r"\1\2", documento, flags=re.S)
    sin_codigo = re.sub(r"(?m)^[ \t]*%.*$", "", sin_codigo)
    sin_codigo = _ARRAYSTRETCH.sub("", sin_codigo)
    peligrosas = sorted({m.group(1) for m in _TOKEN_TEX.finditer(sin_codigo) if m.group(1) in _PRIMITIVAS_PELIGROSAS})
    if peligrosas:
        problemas.append("primitivas de TeX peligrosas en el documento (leen o escriben archivos o redefinen comandos): "
                         + ", ".join("\\" + q for q in peligrosas))
    malos = [c for c in comandos_no_admitidos(sin_codigo, _COMANDOS_DEL_DISENO, frozenset({"frame"}))
             if c.strip("\\").split("{")[0].split(" ")[0] not in _PRIMITIVAS_PELIGROSAS]
    if malos:
        problemas.append("comandos o entornos no admitidos en el documento: " + ", ".join(malos[:12]))
    opciones = opciones_no_admitidas(sin_codigo)
    if opciones:
        problemas.append("opciones no admitidas en el documento: " + ", ".join(f"`{o}`" for o in opciones[:12]))
    problemas += _problemas_de_claves(sin_codigo)
    intrusos = sorted({c for c in documento if ord(c) > 127 and not soportado_por_inputenc(c)})
    if intrusos:
        problemas.append("caracteres que pdfLaTeX no soporta: " + ", ".join(f"U+{ord(c):04X}" for c in intrusos))
    problemas += [p for p in _balance(sin_codigo) if "signos $" not in p]
    if _sin_escapar(sin_codigo, "%"):
        problemas.append("un % sin escapar comenta el resto de la línea")
    return problemas
