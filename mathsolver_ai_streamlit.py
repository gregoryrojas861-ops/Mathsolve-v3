# ============================================================
# MATHSOLVER AI v3
# Plataforma educativa de Matemática, Física, OCR y resolución asistida
# Python + Streamlit + SymPy
#
# Ejecutar:
#   pip install -r requirements.txt
#   python -m streamlit run mathsolver_ai.py
# ============================================================

import ast
import io
import math
import random
import re
import urllib.parse
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import sympy as sp
import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image, ImageOps, ImageEnhance, ImageFilter


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="MathSolver AI",
    page_icon="∑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main { max-width: 1400px; margin: auto; }
.block-container { padding-top: 1.2rem; }
.formula-card {
    padding: 14px; border-radius: 12px;
    border: 1px solid rgba(128,128,128,.25);
    margin-bottom: 10px;
}
.result-box {
    padding: 18px; border-radius: 14px;
    background: rgba(0, 188, 212, .08);
    border: 1px solid rgba(0, 188, 212, .25);
}
.small-muted { opacity: .75; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# MODELOS
# ============================================================

@dataclass
class Formula:
    nombre: str
    area: str
    nivel: str
    tema: str
    formula: str
    variables: str
    descripcion: str
    condiciones: str = ""
    youtube_query: str = ""


# ============================================================
# BASE DE CONOCIMIENTO MATEMÁTICO
# La lista es extensible: agregar Formula(...) permite ampliar
# el conocimiento sin modificar el motor.
# ============================================================

FORMULAS = [

# ---------------- ARITMÉTICA ----------------
Formula("Porcentaje", "Matemática", "Liceo", "Aritmética", "p = (parte / total) × 100", "parte, total",
        "Calcula qué porcentaje representa una cantidad de otra.", youtube_query="porcentajes matemática explicación ejercicios"),
Formula("Regla de tres", "Matemática", "Liceo", "Proporciones", "a/b = c/x", "a,b,c,x",
        "Permite encontrar un valor desconocido en una proporción.", youtube_query="regla de tres simple explicación"),
Formula("Promedio aritmético", "Matemática", "Liceo", "Aritmética", "x̄ = Σx / n", "x,n",
        "Suma los valores y divide entre el número de observaciones.", youtube_query="promedio media aritmética"),
Formula("Interés simple", "Matemática", "Liceo", "Matemática financiera", "I = C·i·t", "C,i,t",
        "Interés generado sobre un capital con tasa y tiempo.", youtube_query="interés simple matemática"),
Formula("Monto de interés simple", "Matemática", "Liceo", "Matemática financiera", "M = C(1 + it)", "C,i,t",
        "Capital más el interés simple.", youtube_query="monto interés simple"),

# ---------------- ÁLGEBRA ----------------
Formula("Propiedad distributiva", "Matemática", "Liceo", "Álgebra", "a(b+c)=ab+ac", "a,b,c",
        "Multiplica un factor por cada término del paréntesis.", youtube_query="propiedad distributiva álgebra"),
Formula("Producto notable: cuadrado de suma", "Matemática", "Liceo", "Productos notables", "(a+b)²=a²+2ab+b²", "a,b",
        "Identidad fundamental para expandir binomios.", youtube_query="cuadrado de un binomio"),
Formula("Producto notable: cuadrado de diferencia", "Matemática", "Liceo", "Productos notables", "(a-b)²=a²-2ab+b²", "a,b",
        "Expansión del cuadrado de una diferencia.", youtube_query="cuadrado de diferencia binomio"),
Formula("Diferencia de cuadrados", "Matemática", "Liceo", "Factorización", "a²-b²=(a-b)(a+b)", "a,b",
        "Factorización de una diferencia de cuadrados.", youtube_query="diferencia de cuadrados factorización"),
Formula("Cubo de una suma", "Matemática", "Liceo", "Productos notables", "(a+b)³=a³+3a²b+3ab²+b³", "a,b",
        "Expansión del cubo de un binomio.", youtube_query="cubo de un binomio"),
Formula("Cubo de una diferencia", "Matemática", "Liceo", "Productos notables", "(a-b)³=a³-3a²b+3ab²-b³", "a,b",
        "Expansión del cubo de una diferencia.", youtube_query="cubo de diferencia binomio"),
Formula("Fórmula general", "Matemática", "Liceo / Universidad", "Ecuaciones", "x=(-b±√(b²-4ac))/(2a)", "a,b,c",
        "Resuelve ecuaciones cuadráticas ax²+bx+c=0.", "a ≠ 0", "fórmula general ecuación cuadrática"),
Formula("Discriminante", "Matemática", "Liceo", "Ecuaciones", "Δ=b²-4ac", "a,b,c",
        "Determina la naturaleza de las raíces de una cuadrática.", "a ≠ 0", "discriminante ecuación cuadrática"),
Formula("Vértice de parábola", "Matemática", "Liceo", "Funciones", "xv=-b/(2a), yv=f(xv)", "a,b",
        "Obtiene el vértice de ax²+bx+c.", "a ≠ 0", "vértice parábola"),
Formula("Pendiente", "Matemática", "Liceo", "Geometría analítica", "m=(y₂-y₁)/(x₂-x₁)", "x₁,y₁,x₂,y₂",
        "Calcula la pendiente de una recta.", "x₁ ≠ x₂", "pendiente de una recta"),
Formula("Recta punto-pendiente", "Matemática", "Liceo", "Geometría analítica", "y-y₁=m(x-x₁)", "x₁,y₁,m",
        "Ecuación de una recta con punto y pendiente.", youtube_query="ecuación punto pendiente"),
Formula("Distancia entre dos puntos", "Matemática", "Liceo", "Geometría analítica", "d=√((x₂-x₁)²+(y₂-y₁)²)", "puntos",
        "Distancia euclidiana en el plano.", youtube_query="distancia entre dos puntos"),
Formula("Punto medio", "Matemática", "Liceo", "Geometría analítica", "M=((x₁+x₂)/2,(y₁+y₂)/2)", "puntos",
        "Punto medio de un segmento.", youtube_query="punto medio geometría analítica"),

# ---------------- EXPONENTES Y LOGARITMOS ----------------
Formula("Producto de potencias", "Matemática", "Liceo", "Exponentes", "a^m·a^n=a^(m+n)", "a,m,n",
        "Suma exponentes cuando la base es igual."),
Formula("Cociente de potencias", "Matemática", "Liceo", "Exponentes", "a^m/a^n=a^(m-n)", "a,m,n",
        "Resta exponentes con la misma base."),
Formula("Potencia de potencia", "Matemática", "Liceo", "Exponentes", "(a^m)^n=a^(mn)", "a,m,n",
        "Multiplica exponentes."),
Formula("Logaritmo de producto", "Matemática", "Liceo", "Logaritmos", "log(ab)=log(a)+log(b)", "a,b",
        "Convierte productos en sumas de logaritmos.", "a,b > 0"),
Formula("Logaritmo de cociente", "Matemática", "Liceo", "Logaritmos", "log(a/b)=log(a)-log(b)", "a,b",
        "Convierte cocientes en diferencias.", "a,b > 0"),
Formula("Cambio de base", "Matemática", "Liceo / Universidad", "Logaritmos", "log_b(a)=ln(a)/ln(b)", "a,b",
        "Permite calcular logaritmos usando otra base.", "a>0, b>0, b≠1"),

# ---------------- GEOMETRÍA ----------------
Formula("Área del cuadrado", "Matemática", "Liceo", "Geometría", "A=l²", "l",
        "Área de un cuadrado."),
Formula("Perímetro del cuadrado", "Matemática", "Liceo", "Geometría", "P=4l", "l",
        "Perímetro de un cuadrado."),
Formula("Área del rectángulo", "Matemática", "Liceo", "Geometría", "A=bh", "b,h",
        "Base por altura."),
Formula("Área del triángulo", "Matemática", "Liceo", "Geometría", "A=bh/2", "b,h",
        "Mitad del área de un rectángulo equivalente."),
Formula("Teorema de Pitágoras", "Matemática", "Liceo", "Geometría", "a²+b²=c²", "a,b,c",
        "Relación entre los lados de un triángulo rectángulo.", "c es la hipotenusa", "teorema de Pitágoras"),
Formula("Área del círculo", "Matemática", "Liceo", "Geometría", "A=πr²", "r",
        "Área de un círculo.", youtube_query="área del círculo"),
Formula("Longitud de circunferencia", "Matemática", "Liceo", "Geometría", "C=2πr", "r",
        "Longitud de una circunferencia."),
Formula("Área de trapecio", "Matemática", "Liceo", "Geometría", "A=(B+b)h/2", "B,b,h",
        "Área de un trapecio."),
Formula("Área de polígono regular", "Matemática", "Liceo", "Geometría", "A=Pa/2", "P,a",
        "Perímetro por apotema dividido entre dos."),
Formula("Volumen de prisma", "Matemática", "Liceo", "Geometría espacial", "V=A_bh", "A_b,h",
        "Volumen de un prisma."),
Formula("Volumen de cilindro", "Matemática", "Liceo", "Geometría espacial", "V=πr²h", "r,h",
        "Volumen de un cilindro."),
Formula("Volumen de esfera", "Matemática", "Liceo", "Geometría espacial", "V=4πr³/3", "r",
        "Volumen de una esfera."),
Formula("Área de esfera", "Matemática", "Liceo", "Geometría espacial", "A=4πr²", "r",
        "Área superficial de una esfera."),

# ---------------- TRIGONOMETRÍA ----------------
Formula("Seno", "Matemática", "Liceo", "Trigonometría", "sin(θ)=opuesto/hipotenusa", "θ",
        "Razón trigonométrica en triángulos rectángulos.", youtube_query="seno coseno tangente trigonometría"),
Formula("Coseno", "Matemática", "Liceo", "Trigonometría", "cos(θ)=adyacente/hipotenusa", "θ",
        "Razón trigonométrica."),
Formula("Tangente", "Matemática", "Liceo", "Trigonometría", "tan(θ)=opuesto/adyacente", "θ",
        "Razón trigonométrica."),
Formula("Identidad pitagórica", "Matemática", "Liceo / Universidad", "Trigonometría", "sin²x+cos²x=1", "x",
        "Identidad trigonométrica fundamental."),
Formula("Ley de senos", "Matemática", "Liceo / Universidad", "Trigonometría", "a/sin(A)=b/sin(B)=c/sin(C)", "a,b,c,A,B,C",
        "Relaciona lados y ángulos de un triángulo."),
Formula("Ley de cosenos", "Matemática", "Liceo / Universidad", "Trigonometría", "c²=a²+b²-2ab cos(C)", "a,b,c,C",
        "Generalización del teorema de Pitágoras."),

# ---------------- SUCESIONES ----------------
Formula("Término de sucesión aritmética", "Matemática", "Liceo", "Sucesiones", "a_n=a_1+(n-1)d", "a₁,n,d",
        "Término n de una progresión aritmética."),
Formula("Suma aritmética", "Matemática", "Liceo", "Sucesiones", "S_n=n(a₁+a_n)/2", "n,a₁,a_n",
        "Suma de los primeros n términos."),
Formula("Término de sucesión geométrica", "Matemática", "Liceo", "Sucesiones", "a_n=a₁r^(n-1)", "a₁,r,n",
        "Término n de una progresión geométrica."),
Formula("Suma geométrica finita", "Matemática", "Liceo", "Sucesiones", "S_n=a₁(1-r^n)/(1-r)", "a₁,r,n",
        "Suma finita cuando r ≠ 1."),

# ---------------- CÁLCULO I ----------------
Formula("Definición de derivada", "Matemática", "Universidad", "Cálculo", "f'(x)=lim[h→0](f(x+h)-f(x))/h", "f,h",
        "Definición fundamental de derivada.", "Debe existir el límite", "definición de derivada cálculo"),
Formula("Regla de potencia", "Matemática", "Universidad", "Derivadas", "d(x^n)/dx=n x^(n-1)", "n",
        "Derivada de una potencia."),
Formula("Derivada de suma", "Matemática", "Universidad", "Derivadas", "(f+g)'=f'+g'", "f,g",
        "Derivada término a término."),
Formula("Regla del producto", "Matemática", "Universidad", "Derivadas", "(fg)'=f'g+fg'", "f,g",
        "Derivada de un producto."),
Formula("Regla del cociente", "Matemática", "Universidad", "Derivadas", "(f/g)'=(f'g-fg')/g²", "f,g",
        "Derivada de un cociente.", "g ≠ 0"),
Formula("Regla de la cadena", "Matemática", "Universidad", "Derivadas", "(f(g(x)))'=f'(g(x))g'(x)", "f,g",
        "Derivada de funciones compuestas.", youtube_query="regla de la cadena derivadas"),
Formula("Derivada de exponencial", "Matemática", "Universidad", "Derivadas", "d(e^x)/dx=e^x", "x",
        "Derivada de la exponencial natural."),
Formula("Derivada de logaritmo", "Matemática", "Universidad", "Derivadas", "d(ln x)/dx=1/x", "x",
        "Derivada del logaritmo natural.", "x>0"),
Formula("Derivada de seno", "Matemática", "Universidad", "Derivadas", "d(sin x)/dx=cos x", "x",
        "Derivada del seno."),
Formula("Derivada de coseno", "Matemática", "Universidad", "Derivadas", "d(cos x)/dx=-sin x", "x",
        "Derivada del coseno."),
Formula("Integral de potencia", "Matemática", "Universidad", "Integrales", "∫x^n dx=x^(n+1)/(n+1)+C", "n",
        "Antiderivada de una potencia.", "n ≠ -1", "integral de potencia cálculo"),
Formula("Integral de 1/x", "Matemática", "Universidad", "Integrales", "∫1/x dx=ln|x|+C", "x",
        "Integral del inverso de x."),
Formula("Integral de exponencial", "Matemática", "Universidad", "Integrales", "∫e^x dx=e^x+C", "x",
        "Antiderivada de la exponencial."),
Formula("Teorema fundamental del cálculo", "Matemática", "Universidad", "Integrales", "∫_a^b f(x)dx=F(b)-F(a)", "a,b,F",
        "Relaciona derivación e integración."),
Formula("Integración por partes", "Matemática", "Universidad", "Integración", "∫u dv=uv-∫v du", "u,v",
        "Método para integrar productos."),
Formula("Sustitución", "Matemática", "Universidad", "Integración", "∫f(g(x))g'(x)dx=∫f(u)du", "u=g(x)",
        "Cambio de variable en integrales."),
Formula("Taylor", "Matemática", "Universidad", "Series", "f(x)=Σ f^(n)(a)(x-a)^n/n!", "f,a,n",
        "Aproximación mediante serie de Taylor."),
Formula("Maclaurin", "Matemática", "Universidad", "Series", "f(x)=Σ f^(n)(0)x^n/n!", "f,n",
        "Caso particular de Taylor alrededor de cero."),

# ---------------- CÁLCULO MULTIVARIABLE ----------------
Formula("Gradiente", "Matemática", "Universidad", "Cálculo multivariable", "∇f=(∂f/∂x,∂f/∂y,∂f/∂z)", "f",
        "Vector de derivadas parciales."),
Formula("Divergencia", "Matemática", "Universidad", "Cálculo vectorial", "∇·F=∂P/∂x+∂Q/∂y+∂R/∂z", "F=(P,Q,R)",
        "Mide la divergencia de un campo vectorial."),
Formula("Rotacional", "Matemática", "Universidad", "Cálculo vectorial", "∇×F", "F",
        "Mide la circulación local de un campo vectorial."),
Formula("Jacobiano", "Matemática", "Universidad", "Cálculo multivariable", "J=det(∂(u,v)/∂(x,y))", "u,v,x,y",
        "Determinante de la matriz de derivadas parciales."),

# ---------------- ÁLGEBRA LINEAL ----------------
Formula("Determinante 2×2", "Matemática", "Universidad", "Álgebra lineal", "det(A)=ad-bc", "a,b,c,d",
        "Determinante de matriz 2×2."),
Formula("Producto matricial", "Matemática", "Universidad", "Álgebra lineal", "C_ij=Σ A_ik B_kj", "A,B",
        "Producto de matrices compatibles."),
Formula("Inversa 2×2", "Matemática", "Universidad", "Álgebra lineal", "A⁻¹=1/(ad-bc)[[d,-b],[-c,a]]", "A",
        "Inversa de matriz 2×2.", "det(A) ≠ 0"),
Formula("Ecuación matricial", "Matemática", "Universidad", "Álgebra lineal", "Ax=b", "A,x,b",
        "Sistema lineal expresado matricialmente."),
Formula("Autovalor", "Matemática", "Universidad", "Álgebra lineal", "det(A-λI)=0", "A,λ",
        "Ecuación característica para encontrar autovalores."),

# ---------------- PROBABILIDAD ----------------
Formula("Probabilidad clásica", "Matemática", "Liceo / Universidad", "Probabilidad", "P(A)=casos favorables/casos posibles", "A",
        "Modelo equiprobable."),
Formula("Complemento", "Matemática", "Liceo / Universidad", "Probabilidad", "P(Aᶜ)=1-P(A)", "A",
        "Probabilidad de que no ocurra A."),
Formula("Unión", "Matemática", "Universidad", "Probabilidad", "P(A∪B)=P(A)+P(B)-P(A∩B)", "A,B",
        "Probabilidad de que ocurra A o B."),
Formula("Probabilidad condicional", "Matemática", "Universidad", "Probabilidad", "P(A|B)=P(A∩B)/P(B)", "A,B",
        "Probabilidad de A dado B.", "P(B)>0"),
Formula("Bayes", "Matemática", "Universidad", "Probabilidad", "P(A|B)=P(B|A)P(A)/P(B)", "A,B",
        "Actualización de probabilidades mediante evidencia.", "P(B)>0"),
Formula("Esperanza", "Matemática", "Universidad", "Probabilidad", "E[X]=ΣxP(X=x)", "X",
        "Valor esperado de una variable discreta."),
Formula("Varianza", "Matemática", "Universidad", "Probabilidad", "Var(X)=E[X²]-E[X]²", "X",
        "Mide dispersión de una variable aleatoria."),

# ---------------- ESTADÍSTICA ----------------
Formula("Varianza poblacional", "Matemática", "Universidad", "Estadística", "σ²=Σ(x-μ)²/N", "x,μ,N",
        "Dispersión de una población."),
Formula("Desviación estándar", "Matemática", "Liceo / Universidad", "Estadística", "σ=√σ²", "σ²",
        "Raíz de la varianza."),
Formula("Varianza muestral", "Matemática", "Universidad", "Estadística", "s²=Σ(x-x̄)²/(n-1)", "x,x̄,n",
        "Estimador muestral de varianza."),
Formula("Z-score", "Matemática", "Universidad", "Estadística", "z=(x-μ)/σ", "x,μ,σ",
        "Estandariza una observación."),
Formula("Covarianza", "Matemática", "Universidad", "Estadística", "Cov(X,Y)=E[(X-μx)(Y-μy)]", "X,Y",
        "Mide variación conjunta."),
Formula("Correlación", "Matemática", "Universidad", "Estadística", "r=Cov(X,Y)/(σxσy)", "X,Y",
        "Mide asociación lineal estandarizada."),
Formula("Error estándar de la media", "Matemática", "Universidad", "Estadística", "SE=s/√n", "s,n",
        "Variabilidad estimada de la media muestral."),

# ---------------- FÍSICA: MECÁNICA ----------------
Formula("Velocidad media", "Física", "Liceo / Universidad", "Cinemática", "v=Δx/Δt", "Δx,Δt",
        "Cambio de posición por tiempo.", youtube_query="velocidad media física"),
Formula("Aceleración media", "Física", "Liceo / Universidad", "Cinemática", "a=Δv/Δt", "Δv,Δt",
        "Cambio de velocidad por tiempo."),
Formula("MRUA posición", "Física", "Liceo / Universidad", "Cinemática", "x=x₀+v₀t+(1/2)at²", "x₀,v₀,a,t",
        "Posición en movimiento uniformemente acelerado."),
Formula("MRUA velocidad", "Física", "Liceo / Universidad", "Cinemática", "v=v₀+at", "v₀,a,t",
        "Velocidad en MRUA."),
Formula("Ecuación sin tiempo", "Física", "Liceo / Universidad", "Cinemática", "v²=v₀²+2aΔx", "v,v₀,a,Δx",
        "Relaciona velocidad, aceleración y desplazamiento."),
Formula("Segunda ley de Newton", "Física", "Liceo / Universidad", "Dinámica", "F=ma", "F,m,a",
        "Fuerza neta igual a masa por aceleración.", youtube_query="segunda ley de Newton ejercicios"),
Formula("Peso", "Física", "Liceo", "Dinámica", "P=mg", "m,g",
        "Fuerza gravitatoria cerca de la superficie terrestre."),
Formula("Fricción cinética", "Física", "Liceo / Universidad", "Dinámica", "f_k=μ_k N", "μk,N",
        "Modelo de fricción cinética."),
Formula("Trabajo", "Física", "Liceo / Universidad", "Energía", "W=Fd cos(θ)", "F,d,θ",
        "Trabajo de una fuerza constante."),
Formula("Energía cinética", "Física", "Liceo / Universidad", "Energía", "K=mv²/2", "m,v",
        "Energía asociada al movimiento."),
Formula("Energía potencial gravitatoria", "Física", "Liceo / Universidad", "Energía", "U=mgh", "m,g,h",
        "Energía gravitatoria cerca de la superficie."),
Formula("Potencia", "Física", "Liceo / Universidad", "Energía", "P=W/t", "W,t",
        "Rapidez con que se realiza trabajo."),
Formula("Cantidad de movimiento", "Física", "Universidad", "Mecánica", "p=mv", "m,v",
        "Momento lineal."),
Formula("Impulso", "Física", "Universidad", "Mecánica", "J=FΔt=Δp", "F,Δt,Δp",
        "Cambio en la cantidad de movimiento."),
Formula("Momento angular", "Física", "Universidad", "Mecánica", "L=r×p", "r,p",
        "Momento angular respecto a un punto."),
Formula("Torque", "Física", "Universidad", "Mecánica", "τ=rF sin(θ)", "r,F,θ",
        "Momento de una fuerza."),
Formula("Gravitación universal", "Física", "Universidad", "Gravitación", "F=Gm₁m₂/r²", "G,m₁,m₂,r",
        "Fuerza gravitatoria entre masas."),
Formula("Movimiento circular", "Física", "Universidad", "Movimiento circular", "a_c=v²/r", "v,r",
        "Aceleración centrípeta."),
Formula("Frecuencia", "Física", "Liceo / Universidad", "Oscilaciones", "f=1/T", "T",
        "Inversa del período."),
Formula("Velocidad angular", "Física", "Universidad", "Rotación", "ω=Δθ/Δt", "Δθ,Δt",
        "Cambio angular por tiempo."),

# ---------------- FÍSICA: FLUIDOS Y TERMODINÁMICA ----------------
Formula("Densidad", "Física", "Liceo", "Fluidos", "ρ=m/V", "m,V",
        "Masa por unidad de volumen."),
Formula("Presión", "Física", "Liceo / Universidad", "Fluidos", "P=F/A", "F,A",
        "Fuerza normal distribuida sobre un área."),
Formula("Presión hidrostática", "Física", "Liceo / Universidad", "Fluidos", "P=P₀+ρgh", "P₀,ρ,g,h",
        "Presión en un fluido en reposo."),
Formula("Empuje de Arquímedes", "Física", "Liceo / Universidad", "Fluidos", "F_b=ρgV_d", "ρ,g,Vd",
        "Fuerza de flotación."),
Formula("Primera ley de la termodinámica", "Física", "Universidad", "Termodinámica", "ΔU=Q-W", "ΔU,Q,W",
        "Conservación de la energía en un sistema termodinámico."),
Formula("Gas ideal", "Física", "Universidad", "Termodinámica", "PV=nRT", "P,V,n,R,T",
        "Ecuación de estado del gas ideal."),
Formula("Calor sensible", "Física", "Liceo / Universidad", "Termodinámica", "Q=mcΔT", "m,c,ΔT",
        "Calor para cambiar la temperatura."),
Formula("Calor latente", "Física", "Liceo / Universidad", "Termodinámica", "Q=mL", "m,L",
        "Energía asociada a cambio de fase."),

# ---------------- ELECTRICIDAD Y MAGNETISMO ----------------
Formula("Ley de Ohm", "Física", "Liceo / Universidad", "Electricidad", "V=IR", "V,I,R",
        "Relación entre voltaje, corriente y resistencia.", youtube_query="ley de Ohm ejercicios"),
Formula("Potencia eléctrica", "Física", "Liceo / Universidad", "Electricidad", "P=VI", "V,I",
        "Potencia eléctrica."),
Formula("Energía eléctrica", "Física", "Liceo", "Electricidad", "E=Pt", "P,t",
        "Energía consumida o entregada."),
Formula("Resistencias en serie", "Física", "Liceo / Universidad", "Circuitos", "R_eq=R₁+R₂+...", "R",
        "Resistencia equivalente en serie."),
Formula("Resistencias en paralelo", "Física", "Liceo / Universidad", "Circuitos", "1/R_eq=Σ1/R_i", "R_i",
        "Resistencia equivalente en paralelo."),
Formula("Ley de Coulomb", "Física", "Universidad", "Electrostática", "F=k|q₁q₂|/r²", "k,q₁,q₂,r",
        "Fuerza electrostática."),
Formula("Campo eléctrico", "Física", "Universidad", "Electrostática", "E=F/q", "F,q",
        "Fuerza por unidad de carga."),
Formula("Potencial eléctrico puntual", "Física", "Universidad", "Electrostática", "V=kq/r", "k,q,r",
        "Potencial de una carga puntual."),
Formula("Fuerza magnética", "Física", "Universidad", "Magnetismo", "F=qvB sin(θ)", "q,v,B,θ",
        "Fuerza magnética sobre una carga."),
Formula("Ley de Faraday", "Física", "Universidad", "Electromagnetismo", "ε=-dΦ/dt", "Φ,t",
        "Fuerza electromotriz inducida."),
Formula("Flujo magnético", "Física", "Universidad", "Magnetismo", "Φ=BA cos(θ)", "B,A,θ",
        "Flujo de campo magnético."),

# ---------------- ÓPTICA Y ONDAS ----------------
Formula("Velocidad de onda", "Física", "Liceo / Universidad", "Ondas", "v=fλ", "f,λ",
        "Relación entre frecuencia, longitud de onda y velocidad."),
Formula("Índice de refracción", "Física", "Universidad", "Óptica", "n=c/v", "c,v",
        "Relación entre velocidad de luz en vacío y medio."),
Formula("Ley de Snell", "Física", "Universidad", "Óptica", "n₁ sinθ₁=n₂ sinθ₂", "n₁,n₂,θ₁,θ₂",
        "Refracción de la luz.", youtube_query="ley de Snell refracción ejercicios"),
Formula("Ecuación de lente delgada", "Física", "Universidad", "Óptica", "1/f=1/d_o+1/d_i", "f,d_o,d_i",
        "Relación para lentes delgadas."),
Formula("Aumento de lente", "Física", "Universidad", "Óptica", "m=-d_i/d_o", "d_i,d_o",
        "Aumento lateral de una lente."),

# ---------------- MÉTODOS NUMÉRICOS ----------------
Formula("Newton-Raphson", "Matemática", "Universidad", "Métodos numéricos", "x_(n+1)=x_n-f(x_n)/f'(x_n)", "x,f",
        "Método iterativo para aproximar raíces.", youtube_query="Newton Raphson método numérico"),
Formula("Error relativo", "Matemática", "Universidad", "Métodos numéricos", "E_r=|valor real-aprox|/|valor real|", "valores",
        "Mide error relativo de una aproximación."),
Formula("Interpolación lineal", "Matemática", "Universidad", "Métodos numéricos", "y=y₁+(x-x₁)(y₂-y₁)/(x₂-x₁)", "x,y,x₁,y₁,x₂,y₂",
        "Aproximación entre dos puntos."),

# ---------------- MATEMÁTICA FINANCIERA ----------------
Formula("Interés compuesto", "Matemática", "Universidad", "Finanzas", "M=C(1+i)^n", "C,i,n",
        "Capitalización periódica."),
Formula("Valor presente", "Matemática", "Universidad", "Finanzas", "VP=VF/(1+i)^n", "VF,i,n",
        "Valor actual de un monto futuro."),
Formula("Valor futuro", "Matemática", "Universidad", "Finanzas", "VF=VP(1+i)^n", "VP,i,n",
        "Valor futuro de un capital."),
Formula("Anualidad ordinaria", "Matemática", "Universidad", "Finanzas", "VP=R(1-(1+i)^(-n))/i", "R,i,n",
        "Valor presente de pagos periódicos.", "i ≠ 0"),
]


# ============================================================
# AMPLIACIÓN UNIVERSITARIA — CÁLCULO AVANZADO, ECUACIONES
# DIFERENCIALES, ESTADÍSTICA INFERENCIAL, OPTIMIZACIÓN,
# TRANSFORMADAS Y FÍSICA UNIVERSITARIA
# ============================================================
FORMULAS.extend([
    Formula("Ecuación diferencial lineal de primer orden", "Matemática", "Universidad", "Ecuaciones diferenciales", "y' + P(x)y = Q(x)", "P,Q,y",
            "Forma estándar de una ecuación diferencial lineal de primer orden.", youtube_query="ecuaciones diferenciales primer orden lineales"),
    Formula("Factor integrante", "Matemática", "Universidad", "Ecuaciones diferenciales", "μ(x)=e^(∫P(x)dx)", "P(x)",
            "Método para resolver ecuaciones lineales de primer orden."),
    Formula("Ecuación separable", "Matemática", "Universidad", "Ecuaciones diferenciales", "dy/dx=g(x)h(y)", "g,h",
            "Se separan variables y se integran ambos lados.", youtube_query="ecuaciones diferenciales variables separables"),
    Formula("Ecuación característica de segundo orden", "Matemática", "Universidad", "Ecuaciones diferenciales", "ar²+br+c=0", "a,b,c",
            "Permite resolver ecuaciones lineales homogéneas de coeficientes constantes."),
    Formula("Transformada de Laplace", "Matemática", "Universidad", "Transformadas", "L{f(t)}=∫₀∞e^(-st)f(t)dt", "f,t,s",
            "Transforma funciones del tiempo a una variable compleja s.", youtube_query="transformada de Laplace desde cero"),
    Formula("Laplace de una derivada", "Matemática", "Universidad", "Transformadas", "L{f'}=sF(s)-f(0)", "f,F,s",
            "Permite transformar ecuaciones diferenciales en ecuaciones algebraicas."),
    Formula("Laplace de segunda derivada", "Matemática", "Universidad", "Transformadas", "L{f''}=s²F(s)-sf(0)-f'(0)", "f,F,s",
            "Útil en problemas con condiciones iniciales."),
    Formula("Transformada inversa de Laplace", "Matemática", "Universidad", "Transformadas", "f(t)=L⁻¹{F(s)}", "F,s",
            "Recupera la función temporal desde su transformada."),
    Formula("Serie de Fourier", "Matemática", "Universidad", "Fourier", "f(x)=a₀/2+Σ[a_n cos(nx)+b_n sin(nx)]", "a₀,a_n,b_n",
            "Representación periódica mediante senos y cosenos.", youtube_query="series de Fourier explicación universitaria"),
    Formula("Transformada de Fourier", "Matemática", "Universidad", "Fourier", "F(ω)=∫f(t)e^(-iωt)dt", "f,t,ω",
            "Representación de una señal en frecuencia.", youtube_query="transformada de Fourier desde cero"),
    Formula("Convolución", "Matemática", "Universidad", "Señales", "(f*g)(t)=∫f(τ)g(t-τ)dτ", "f,g",
            "Operación fundamental en señales y sistemas."),
    Formula("Multiplicadores de Lagrange", "Matemática", "Universidad", "Optimización", "∇f=λ∇g", "f,g,λ",
            "Encuentra extremos sujetos a restricciones.", youtube_query="multiplicadores de Lagrange ejercicios"),
    Formula("Condición de primer orden", "Matemática", "Universidad", "Optimización", "∇f(x)=0", "f,x",
            "Condición necesaria para un extremo interior diferenciable."),
    Formula("Matriz Hessiana", "Matemática", "Universidad", "Optimización", "H=[∂²f/∂x_i∂x_j]", "f",
            "Matriz de segundas derivadas usada para clasificar puntos críticos."),
    Formula("Intervalo de confianza de la media", "Estadística", "Universidad", "Inferencia", "x̄ ± z·σ/√n", "x̄,z,σ,n",
            "Intervalo para una media cuando la desviación poblacional es conocida."),
    Formula("Intervalo t de la media", "Estadística", "Universidad", "Inferencia", "x̄ ± t·s/√n", "x̄,t,s,n",
            "Intervalo de confianza usando la distribución t de Student."),
    Formula("Prueba de hipótesis", "Estadística", "Universidad", "Inferencia", "H₀ vs H₁", "H₀,H₁",
            "Marco para contrastar una afirmación estadística mediante datos."),
    Formula("Estadístico z", "Estadística", "Universidad", "Inferencia", "z=(estimación-valor nulo)/SE", "SE",
            "Estandariza una estimación para pruebas de hipótesis."),
    Formula("Regresión lineal", "Estadística", "Universidad", "Regresión", "y=β₀+β₁x+ε", "β₀,β₁",
            "Modelo lineal entre variable respuesta y predictor.", youtube_query="regresión lineal estadística desde cero"),
    Formula("Pendiente de mínimos cuadrados", "Estadística", "Universidad", "Regresión", "β₁=Σ(x-x̄)(y-ȳ)/Σ(x-x̄)²", "x,y",
            "Estimador de la pendiente de regresión lineal."),
    Formula("Coeficiente de determinación", "Estadística", "Universidad", "Regresión", "R²=1-SSE/SST", "SSE,SST",
            "Proporción de variabilidad explicada por el modelo lineal."),
    Formula("Distribución binomial", "Estadística", "Universidad", "Probabilidad", "P(X=k)=C(n,k)p^k(1-p)^(n-k)", "n,k,p",
            "Modelo para número de éxitos en n ensayos independientes."),
    Formula("Distribución normal", "Estadística", "Universidad", "Probabilidad", "f(x)=1/(σ√(2π))e^(-(x-μ)²/(2σ²))", "μ,σ",
            "Distribución continua fundamental en estadística."),
    Formula("Teorema central del límite", "Estadística", "Universidad", "Inferencia", "(x̄-μ)/(σ/√n)≈N(0,1)", "μ,σ,n",
            "Aproximación normal de medias muestrales bajo condiciones adecuadas."),
    Formula("Euler para números complejos", "Matemática", "Universidad", "Complejos", "e^(iθ)=cosθ+i sinθ", "θ",
            "Conecta exponenciales y trigonometría."),
    Formula("Forma polar compleja", "Matemática", "Universidad", "Complejos", "z=r(cosθ+i sinθ)", "r,θ",
            "Representación polar de un número complejo."),
    Formula("Fórmula de Euler-Moivre", "Matemática", "Universidad", "Complejos", "(cosθ+i sinθ)^n=cos(nθ)+i sin(nθ)", "θ,n",
            "Potencias de números complejos en forma trigonométrica."),
    Formula("Teorema de Green", "Matemática", "Universidad", "Cálculo vectorial", "∮(Pdx+Qdy)=∬(∂Q/∂x-∂P/∂y)dA", "P,Q",
            "Relaciona una integral de línea con una integral doble."),
    Formula("Teorema de Stokes", "Matemática", "Universidad", "Cálculo vectorial", "∮F·dr=∬(∇×F)·n dS", "F",
            "Relaciona circulación e integral de superficie."),
    Formula("Teorema de la divergencia", "Matemática", "Universidad", "Cálculo vectorial", "∭∇·F dV=∯F·n dS", "F",
            "Relaciona flujo superficial con divergencia volumétrica."),
    Formula("Ecuación de continuidad", "Física", "Universidad", "Fluidos", "A₁v₁=A₂v₂", "A,v",
            "Conservación de masa para flujo estacionario e incompresible."),
    Formula("Bernoulli", "Física", "Universidad", "Fluidos", "P+ρv²/2+ρgh=constante", "P,ρ,v,g,h",
            "Conservación de energía mecánica en un fluido ideal bajo condiciones apropiadas.", youtube_query="ecuación de Bernoulli ejercicios"),
    Formula("Oscilador armónico", "Física", "Universidad", "Oscilaciones", "x=A cos(ωt+φ)", "A,ω,t,φ",
            "Modelo de movimiento armónico simple."),
    Formula("Frecuencia angular", "Física", "Universidad", "Oscilaciones", "ω=√(k/m)", "k,m",
            "Frecuencia angular de un sistema masa-resorte ideal."),
    Formula("Péndulo simple", "Física", "Universidad", "Oscilaciones", "T=2π√(L/g)", "L,g",
            "Período aproximado para pequeñas oscilaciones."),
    Formula("Momento de inercia", "Física", "Universidad", "Rotación", "I=Σmr²", "m,r",
            "Medida de resistencia a cambios de rotación."),
    Formula("Energía rotacional", "Física", "Universidad", "Rotación", "K_rot=Iω²/2", "I,ω",
            "Energía cinética de rotación."),
    Formula("Ecuación de torque", "Física", "Universidad", "Rotación", "τ=Iα", "I,α",
            "Análogo rotacional de F=ma."),
    Formula("Energía relativista", "Física", "Universidad", "Relatividad", "E=mc²", "m,c",
            "Equivalencia entre masa en reposo y energía."),
    Formula("Factor de Lorentz", "Física", "Universidad", "Relatividad", "γ=1/√(1-v²/c²)", "v,c",
            "Factor relativista para velocidades cercanas a c."),
    Formula("Energía de fotón", "Física", "Universidad", "Física moderna", "E=hf", "h,f",
            "Energía de un fotón."),
    Formula("De Broglie", "Física", "Universidad", "Física cuántica", "λ=h/p", "h,p",
            "Longitud de onda asociada a una partícula."),
    Formula("Ley de decaimiento radiactivo", "Física", "Universidad", "Física nuclear", "N=N₀e^(-λt)", "N₀,λ,t",
            "Modelo exponencial de decaimiento radiactivo."),
    Formula("Semivida", "Física", "Universidad", "Física nuclear", "t₁/₂=ln(2)/λ", "λ",
            "Tiempo para que quede la mitad de una población radiactiva."),
    Formula("Ecuación de Schrödinger independiente del tiempo", "Física", "Universidad", "Mecánica cuántica", "Ĥψ=Eψ", "H,ψ,E",
            "Ecuación fundamental para estados estacionarios cuánticos.", youtube_query="ecuación de Schrödinger explicación"),
    Formula("Ley de Ampère-Maxwell", "Física", "Universidad", "Electromagnetismo", "∮B·dl=μ₀(I+ε₀ dΦ_E/dt)", "B,I,ΦE",
            "Relaciona circulación del campo magnético con corriente y campo eléctrico variable."),
    Formula("Ley de Gauss eléctrica", "Física", "Universidad", "Electromagnetismo", "∮E·dA=Q_enc/ε₀", "E,Q",
            "Relaciona flujo eléctrico y carga encerrada."),
    Formula("Ley de Gauss magnética", "Física", "Universidad", "Electromagnetismo", "∮B·dA=0", "B",
            "No se han observado monopolos magnéticos clásicos."),
    Formula("Ley de Kirchhoff de corrientes", "Física", "Universidad", "Circuitos", "ΣI=0", "I",
            "Conservación de carga en un nodo."),
    Formula("Ley de Kirchhoff de voltajes", "Física", "Universidad", "Circuitos", "ΣΔV=0", "V",
            "Conservación de energía en una malla cerrada."),
    Formula("Circuito RC", "Física", "Universidad", "Circuitos", "V_C=V₀(1-e^(-t/RC))", "R,C,t",
            "Carga de un capacitor mediante una resistencia."),
    Formula("Circuito RL", "Física", "Universidad", "Circuitos", "I=I₀(1-e^(-tR/L))", "R,L,t",
            "Respuesta transitoria ideal de un circuito RL."),
    Formula("Primera ley de la termodinámica", "Física", "Universidad", "Termodinámica", "ΔU=Q-W", "U,Q,W",
            "Conservación de energía termodinámica."),
    Formula("Entropía", "Física", "Universidad", "Termodinámica", "ΔS=∫δQ_rev/T", "Q,T",
            "Cambio de entropía para un proceso reversible."),
    Formula("Eficiencia de Carnot", "Física", "Universidad", "Termodinámica", "η=1-Tc/Th", "Tc,Th",
            "Límite ideal de eficiencia de una máquina térmica reversible."),
])


# ============================================================
# UTILIDADES
# ============================================================

def youtube_search_url(query: str) -> str:
    q = urllib.parse.quote_plus(query)
    return f"https://www.youtube.com/results?search_query={q}"


def normalize_text(text: str) -> str:
    text = text.lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n"
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip()


def detect_area(text: str) -> str:
    t = normalize_text(text)

    physics_words = [
        "newton", "fuerza", "masa", "aceleracion", "velocidad",
        "energia", "trabajo", "potencia", "voltaje", "corriente",
        "resistencia", "carga", "campo electrico", "magnetico",
        "presion", "densidad", "temperatura", "calor", "onda",
        "frecuencia", "luz", "lente", "circuito", "gravitacion"
    ]
    if any(w in t for w in physics_words):
        return "Física"

    return "Matemática"


def detect_topic(text: str) -> str:
    t = normalize_text(text)
    topics = {
        "Ecuaciones": ["ecuacion", "resolver x", "raices", "polinomio"],
        "Derivadas": ["derivada", "derivar", "d/dx"],
        "Integrales": ["integral", "integrar", "antiderivada"],
        "Límites": ["limite", "lim x"],
        "Trigonometría": ["seno", "coseno", "tangente", "trigonometr"],
        "Geometría": ["area", "perimetro", "volumen", "triangulo", "circulo", "rectangulo"],
        "Probabilidad": ["probabilidad", "bayes", "evento"],
        "Estadística": ["media", "mediana", "varianza", "desviacion", "correlacion", "estadistica"],
        "Matrices": ["matriz", "determinante", "autovalor", "vector"],
        "Sucesiones": ["sucesion", "progresion", "termino n"],
        "Logaritmos": ["logaritmo", "log(", "ln("],
        "Cinemática": ["mru", "mrua", "movimiento", "velocidad", "aceleracion"],
        "Dinámica": ["newton", "fuerza", "friccion", "peso"],
        "Energía": ["energia", "trabajo", "potencia"],
        "Electricidad": ["ohm", "voltaje", "corriente", "resistencia", "coulomb"],
        "Óptica": ["lente", "refraccion", "snell", "optica"],
        "Termodinámica": ["gas ideal", "termodinamica", "calor", "temperatura"],
    }
    for topic, words in topics.items():
        if any(w in t for w in words):
            return topic
    return "General"


def detect_level(text: str) -> str:
    t = normalize_text(text)
    if any(x in t for x in ["integral", "derivada", "jacobiano", "autovalor",
                             "ecuacion diferencial", "taylor", "gradiente"]):
        return "Universidad"
    if any(x in t for x in ["pitagoras", "porcentaje", "fraccion", "area",
                             "ecuacion cuadratica", "seno", "coseno"]):
        return "Liceo"
    return "Liceo / Universidad"


def relevant_formulas(query: str, limit: int = 20):
    area = detect_area(query)
    topic = detect_topic(query)
    tokens = set(re.findall(r"[a-záéíóúñ]+", normalize_text(query)))

    scored = []
    for f in FORMULAS:
        score = 0
        ft = normalize_text(f.nombre + " " + f.area + " " + f.tema + " " + f.descripcion)
        if normalize_text(f.area) == normalize_text(area):
            score += 3
        if normalize_text(f.tema) == normalize_text(topic):
            score += 5
        for token in tokens:
            if len(token) > 3 and token in ft:
                score += 1
        if score:
            scored.append((score, f))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in scored[:limit]]


# ============================================================
# MOTOR SIMBÓLICO
# ============================================================

def parse_math(text: str):
    t = text.strip()
    t = t.replace("^", "**")
    t = t.replace("sen", "sin")
    t = t.replace("tg", "tan")
    t = re.sub(r"(?<=\d)(?=[a-zA-Z])", "*", t)
    t = re.sub(r"(?<=[a-zA-Z])(?=\d)", "*", t)
    return sp.sympify(t, locals={
        "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
        "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
        "sqrt": sp.sqrt, "log": sp.log, "ln": sp.log,
        "exp": sp.exp, "pi": sp.pi, "E": sp.E,
        "Abs": sp.Abs
    })


def solve_equation(text: str):
    expr_text = text.replace("=", "-(") + ")" if "=" in text else text
    if "=" in text:
        left, right = text.split("=", 1)
        expr = parse_math(left) - parse_math(right)
    else:
        expr = parse_math(text)

    symbols = sorted(expr.free_symbols, key=lambda s: str(s))
    if not symbols:
        return sp.simplify(expr), [], expr

    variable = symbols[0]
    solutions = sp.solve(expr, variable)
    return variable, solutions, expr


def solve_math_problem(text: str):
    t = text.strip()
    lower = normalize_text(t)

    # Derivadas
    if "deriv" in lower or "d/dx" in lower:
        expr_text = re.sub(r".*?(?:de|derivada de|derivar)\s+", "", t, flags=re.I)
        expr_text = expr_text.strip(" :")
        if not expr_text:
            expr_text = t.split(":", 1)[-1]
        try:
            expr = parse_math(expr_text)
            x = sp.Symbol("x")
            result = sp.diff(expr, x)
            return {
                "tipo": "Derivada",
                "resultado": result,
                "pasos": [
                    f"Función: {sp.latex(expr)}",
                    "Aplicamos las reglas de derivación.",
                    f"Resultado: {sp.latex(result)}"
                ],
                "verificacion": sp.simplify(sp.diff(expr, x) - result) == 0
            }
        except Exception as e:
            return {"error": f"No pude interpretar la derivada: {e}"}

    # Integrales
    if "integral" in lower:
        expr_text = re.sub(r".*?(?:integral de|integra)\s+", "", t, flags=re.I)
        expr_text = expr_text.strip(" :")
        try:
            expr = parse_math(expr_text)
            x = sp.Symbol("x")
            result = sp.integrate(expr, x)
            return {
                "tipo": "Integral indefinida",
                "resultado": result,
                "pasos": [
                    f"Integrando: {sp.latex(expr)}",
                    "Buscamos una antiderivada.",
                    f"Resultado: {sp.latex(result)} + C"
                ],
                "verificacion": sp.simplify(sp.diff(result, x) - expr) == 0
            }
        except Exception as e:
            return {"error": f"No pude interpretar la integral: {e}"}

    # Límite
    if "limite" in lower:
        match = re.search(r"limite.*?(?:x\s*(?:->|→)\s*)?([-\w]+).*?:\s*(.+)", t, re.I)
        if match:
            try:
                point = sp.sympify(match.group(1))
                expr = parse_math(match.group(2))
                x = sp.Symbol("x")
                result = sp.limit(expr, x, point)
                return {
                    "tipo": "Límite",
                    "resultado": result,
                    "pasos": [
                        f"Función: {sp.latex(expr)}",
                        f"Evaluamos el límite cuando x → {point}.",
                        f"Resultado: {sp.latex(result)}"
                    ],
                    "verificacion": True
                }
            except Exception as e:
                return {"error": f"No pude interpretar el límite: {e}"}

    # Simplificación
    if lower.startswith(("simplifica", "simplificar")):
        expr_text = re.sub(r"^simplifica(?:r)?\s*:?\s*", "", t, flags=re.I)
        try:
            expr = parse_math(expr_text)
            result = sp.simplify(expr)
            return {
                "tipo": "Simplificación",
                "resultado": result,
                "pasos": [
                    f"Expresión original: {sp.latex(expr)}",
                    "Aplicamos simplificación simbólica.",
                    f"Resultado: {sp.latex(result)}"
                ],
                "verificacion": sp.simplify(expr - result) == 0
            }
        except Exception as e:
            return {"error": f"No pude simplificar: {e}"}

    # Factorización
    if lower.startswith(("factoriza", "factorizar")):
        expr_text = re.sub(r"^factoriza(?:r)?\s*:?\s*", "", t, flags=re.I)
        try:
            expr = parse_math(expr_text)
            result = sp.factor(expr)
            return {
                "tipo": "Factorización",
                "resultado": result,
                "pasos": [
                    f"Expresión: {sp.latex(expr)}",
                    "Buscamos factores algebraicos.",
                    f"Resultado: {sp.latex(result)}"
                ],
                "verificacion": sp.expand(result - expr) == 0
            }
        except Exception as e:
            return {"error": f"No pude factorizar: {e}"}

    # Ecuaciones
    if "=" in t:
        try:
            variable, solutions, expr = solve_equation(t)
            if isinstance(variable, sp.Symbol):
                checks = []
                for s in solutions:
                    checks.append(sp.simplify(expr.subs(variable, s)) == 0)
                return {
                    "tipo": "Ecuación",
                    "variable": variable,
                    "resultado": solutions,
                    "pasos": [
                        f"Variable detectada: {variable}",
                        f"Ecuación llevada a cero: {sp.latex(expr)} = 0",
                        "Aplicamos resolución simbólica.",
                        "Comprobamos cada solución sustituyéndola en la ecuación."
                    ],
                    "verificacion": all(checks) if checks else False
                }
        except Exception as e:
            return {"error": f"No pude resolver la ecuación: {e}"}

    # Expansión
    if lower.startswith(("expande", "expandir")):
        expr_text = re.sub(r"^expande(?:r)?\s*:?\s*", "", t, flags=re.I)
        try:
            expr = parse_math(expr_text)
            result = sp.expand(expr)
            return {
                "tipo": "Expansión",
                "resultado": result,
                "pasos": [
                    f"Expresión: {sp.latex(expr)}",
                    "Aplicamos expansión algebraica.",
                    f"Resultado: {sp.latex(result)}"
                ],
                "verificacion": sp.simplify(expr - result) == 0
            }
        except Exception as e:
            return {"error": f"No pude expandir: {e}"}

    # Expresión numérica/general
    try:
        expr = parse_math(t)
        result = sp.simplify(expr)
        return {
            "tipo": "Cálculo / expresión",
            "resultado": result,
            "pasos": [
                f"Expresión interpretada: {sp.latex(expr)}",
                "Evaluamos y simplificamos.",
                f"Resultado: {sp.latex(result)}"
            ],
            "verificacion": True
        }
    except Exception:
        return {
            "error": (
                "No pude identificar una operación matemática directa. "
                "Prueba, por ejemplo: 2x+5=17, derivada de x^3, "
                "integral de x^2, simplifica (x+1)^2 o 5*(3+2)."
            )
        }


# ============================================================
# ESTADÍSTICA
# ============================================================

def statistics_from_numbers(values):
    arr = np.array(values, dtype=float)
    return {
        "Cantidad": len(arr),
        "Media": float(np.mean(arr)),
        "Mediana": float(np.median(arr)),
        "Mínimo": float(np.min(arr)),
        "Máximo": float(np.max(arr)),
        "Rango": float(np.max(arr) - np.min(arr)),
        "Varianza poblacional": float(np.var(arr)),
        "Desviación estándar poblacional": float(np.std(arr)),
        "Varianza muestral": float(np.var(arr, ddof=1)) if len(arr) > 1 else None,
        "Desviación estándar muestral": float(np.std(arr, ddof=1)) if len(arr) > 1 else None,
    }


# ============================================================
# MATRICES
# ============================================================

def parse_matrix(text):
    rows = []
    for row in text.strip().split(";"):
        values = [sp.sympify(v.strip()) for v in row.split(",") if v.strip()]
        if values:
            rows.append(values)
    return sp.Matrix(rows)


# ============================================================
# GENERADOR DE EJERCICIOS
# ============================================================

def generate_practice(topic, level):
    if topic == "Álgebra":
        a, b = random.randint(2, 9), random.randint(2, 12)
        return f"Resuelve la ecuación: {a}x + {b} = {a * random.randint(3, 10) + b}"

    if topic == "Ecuaciones":
        a = random.randint(1, 5)
        r1, r2 = random.randint(-6, 6), random.randint(-6, 6)
        b = -a * (r1 + r2)
        c = a * r1 * r2
        return f"Resuelve: {a}x² + ({b})x + ({c}) = 0"

    if topic == "Derivadas":
        n = random.randint(2, 6)
        return f"Calcula la derivada de x^{n} + 3*x^2 - 5*x"

    if topic == "Integrales":
        n = random.randint(1, 5)
        return f"Calcula la integral de x^{n} + 2*x"

    if topic == "Trigonometría":
        return "En un triángulo rectángulo, calcula la hipotenusa si los catetos miden 3 y 4."

    if topic == "Física":
        return "Un automóvil parte con v₀=5 m/s y acelera a 2 m/s² durante 4 s. ¿Cuál es su velocidad final?"

    if topic == "Estadística":
        return "Calcula media, mediana, varianza y desviación estándar de: 4, 5, 5, 7, 9, 10."

    return "Simplifica: (x + 2)^2 - (x^2 + 4*x + 4)"


# ============================================================
# MOTOR AVANZADO
# ============================================================
def solve_ode_expression(equation_text: str):
    """Resuelve ecuaciones diferenciales introducidas como y' = ... o y'' + ... = 0."""
    x = sp.Symbol("x")
    y = sp.Function("y")
    text = equation_text.strip().replace("^", "**")
    text = re.sub(r"^ode\s*:\s*", "", text, flags=re.I)
    try:
        if "=" in text:
            left, right = text.split("=", 1)
            # Convierte y' y y'' a derivadas SymPy.
            left = re.sub(r"y\s*''", "Derivative(y(x),x,2)", left)
            left = re.sub(r"y\s*'", "Derivative(y(x),x)", left)
            left = re.sub(r"\by\b", "y(x)", left)
            right = re.sub(r"y\s*''", "Derivative(y(x),x,2)", right)
            right = re.sub(r"y\s*'", "Derivative(y(x),x)", right)
            right = re.sub(r"\by\b", "y(x)", right)
            eq = sp.Eq(sp.sympify(left), sp.sympify(right))
        else:
            raise ValueError("Usa el formato y' = ... o y'' + ... = ...")
        sol = sp.dsolve(eq, y(x))
        return sol
    except Exception as exc:
        raise ValueError(f"No pude resolver la EDO: {exc}") from exc


def solve_laplace_expression(expression: str):
    t = sp.Symbol("t", positive=True)
    s = sp.Symbol("s", positive=True)
    expr = parse_math(expression.replace("t", "t"))
    return sp.laplace_transform(expr, t, s, noconds=True)


def inverse_laplace_expression(expression: str):
    s = sp.Symbol("s", positive=True)
    t = sp.Symbol("t", positive=True)
    expr = sp.sympify(expression.replace("^", "**"))
    return sp.inverse_laplace_transform(expr, s, t)


def fourier_series_expression(expression: str, variable: str = "x", interval=(-sp.pi, sp.pi)):
    x = sp.Symbol(variable, real=True)
    expr = sp.sympify(expression.replace("^", "**"), locals={"sin": sp.sin, "cos": sp.cos, "pi": sp.pi})
    return sp.fourier_series(expr, (x, interval[0], interval[1]))


def linear_regression(values_x, values_y):
    x = np.asarray(values_x, dtype=float)
    y = np.asarray(values_y, dtype=float)
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Se necesitan al menos dos pares (x,y).")
    slope, intercept = np.polyfit(x, y, 1)
    pred = intercept + slope * x
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    corr = float(np.corrcoef(x, y)[0, 1])
    return float(intercept), float(slope), float(r2), corr, pred


def optimize_one_variable(expression: str, variable: str = "x"):
    x = sp.Symbol(variable, real=True)
    expr = parse_math(expression)
    first = sp.diff(expr, x)
    second = sp.diff(expr, x, 2)
    critical = sp.solve(sp.Eq(first, 0), x)
    points = []
    for c in critical:
        try:
            value = sp.simplify(expr.subs(x, c))
            curvature = sp.simplify(second.subs(x, c))
            kind = "mínimo local" if curvature.is_positive else "máximo local" if curvature.is_negative else "indeterminado con la segunda derivada"
            points.append((c, value, curvature, kind))
        except Exception:
            points.append((c, None, None, "no clasificado"))
    return first, second, points



# ============================================================
# OCR DE EJERCICIOS Y FÓRMULAS
# ============================================================

def preprocess_ocr_image(image: Image.Image, variant: str = "contraste") -> Image.Image:
    """Preprocesa una imagen para mejorar OCR de texto y fórmulas simples."""
    img = image.convert("L")
    if variant == "contraste":
        img = ImageOps.autocontrast(img)
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
    elif variant == "binario":
        img = ImageOps.autocontrast(img)
        img = img.point(lambda p: 255 if p > 160 else 0)
    elif variant == "suave":
        img = ImageOps.autocontrast(img)
        img = img.filter(ImageFilter.MedianFilter(size=3))
    return img


def ocr_image(image: Image.Image) -> dict:
    """Ejecuta varias pasadas de Tesseract si está instalado."""
    try:
        import pytesseract
    except ImportError:
        return {"ok": False, "error": "pytesseract no está instalado."}

    variants = ["contraste", "suave", "binario"]
    results = []
    errors = []
    for variant in variants:
        try:
            processed = preprocess_ocr_image(image, variant)
            text = pytesseract.image_to_string(processed, config="--psm 6")
            if text.strip():
                results.append((variant, text.strip()))
        except Exception as exc:
            errors.append(str(exc))

    if not results:
        return {
            "ok": False,
            "error": "No fue posible extraer texto. Comprueba que Tesseract OCR esté instalado en el equipo."
        }

    # Elegimos el resultado con mayor cantidad de caracteres útiles.
    best = max(results, key=lambda item: sum(ch.isalnum() for ch in item[1]))
    return {"ok": True, "text": best[1], "variant": best[0], "alternatives": results, "errors": errors}


def normalize_ocr_math(text: str) -> str:
    """Convierte errores frecuentes de OCR a una forma más interpretable por SymPy."""
    replacements = {
        "×": "*", "÷": "/", "−": "-", "–": "-", "—": "-",
        "·": "*", "π": "pi", "√": "sqrt", "∞": "oo",
        "²": "**2", "³": "**3", "⁴": "**4", "⁵": "**5",
        "∫": "integral ", "∑": "sum ", "≤": "<=", "≥": ">=",
        "≠": "!=", "→": "->", "^": "**",
    }
    out = text
    for old, new in replacements.items():
        out = out.replace(old, new)
    # Correcciones conservadoras comunes de OCR.
    out = re.sub(r"(?<=\d)[oO](?=\d)", "0", out)
    out = re.sub(r"\bI\b", "1", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def recognize_handwritten_formula(image: Image.Image) -> dict:
    """Intenta reconocer fórmulas manuscritas mediante OCR local.

    No inventa una fórmula si la lectura es ambigua. Devuelve las lecturas
    candidatas para que el usuario pueda elegir/corregir antes de resolver.
    """
    result = ocr_image(image)
    if not result.get("ok"):
        return result
    candidates = []
    for _, raw in result.get("alternatives", []):
        normalized = normalize_ocr_math(raw)
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return {
        "ok": True,
        "candidates": candidates,
        "raw": result.get("text", ""),
        "note": "El reconocimiento manuscrito depende de la calidad de la foto y de Tesseract; revisa la fórmula antes de resolverla."
    }


# ============================================================
# MOTOR DE FÍSICA PASO A PASO
# ============================================================

PHYSICS_FORMULAS = [
    Formula("Velocidad media", "Física", "Liceo / Universidad", "Cinemática", "v=Δx/Δt", "Δx,Δt", "Cambio de posición dividido entre tiempo."),
    Formula("Aceleración media", "Física", "Liceo / Universidad", "Cinemática", "a=Δv/Δt", "Δv,Δt", "Cambio de velocidad por unidad de tiempo."),
    Formula("MRUA", "Física", "Liceo / Universidad", "Cinemática", "x=x₀+v₀t+at²/2", "x₀,v₀,a,t", "Posición en movimiento rectilíneo uniformemente acelerado."),
    Formula("Velocidad en MRUA", "Física", "Liceo / Universidad", "Cinemática", "v=v₀+at", "v₀,a,t", "Velocidad final con aceleración constante."),
    Formula("Segunda ley de Newton", "Física", "Liceo / Universidad", "Dinámica", "F=ma", "F,m,a", "Relación entre fuerza neta, masa y aceleración."),
    Formula("Peso", "Física", "Liceo", "Dinámica", "P=mg", "m,g", "Fuerza gravitatoria cerca de la superficie terrestre."),
    Formula("Trabajo", "Física", "Liceo / Universidad", "Energía", "W=Fd cos(θ)", "F,d,θ", "Trabajo de una fuerza constante."),
    Formula("Energía cinética", "Física", "Liceo / Universidad", "Energía", "K=mv²/2", "m,v", "Energía asociada al movimiento."),
    Formula("Energía potencial gravitatoria", "Física", "Liceo", "Energía", "U=mgh", "m,g,h", "Energía gravitatoria cerca de la superficie terrestre."),
    Formula("Potencia", "Física", "Liceo / Universidad", "Energía", "P=W/t", "W,t", "Trabajo realizado por unidad de tiempo."),
    Formula("Cantidad de movimiento", "Física", "Liceo / Universidad", "Momento lineal", "p=mv", "m,v", "Producto de masa por velocidad."),
    Formula("Impulso", "Física", "Liceo / Universidad", "Momento lineal", "J=FΔt=Δp", "F,Δt,Δp", "Cambio de cantidad de movimiento."),
    Formula("Fuerza centrípeta", "Física", "Liceo / Universidad", "Movimiento circular", "F_c=mv²/r", "m,v,r", "Fuerza radial necesaria para movimiento circular."),
    Formula("Ley de Hooke", "Física", "Liceo / Universidad", "Oscilaciones", "F=-kx", "k,x", "Modelo lineal de un resorte ideal."),
    Formula("Ley de Ohm", "Física", "Liceo / Universidad", "Electricidad", "V=IR", "V,I,R", "Relación entre tensión, corriente y resistencia."),
    Formula("Potencia eléctrica", "Física", "Liceo / Universidad", "Circuitos", "P=VI", "V,I", "Potencia eléctrica en un elemento."),
    Formula("Carga eléctrica", "Física", "Liceo / Universidad", "Electrostática", "F=q", "q", "Magnitud de carga eléctrica; relación base para modelos electrostáticos."),
    Formula("Ley de Coulomb", "Física", "Universidad", "Electrostática", "F=k|q₁q₂|/r²", "q₁,q₂,r", "Fuerza electrostática entre cargas puntuales."),
    Formula("Campo eléctrico", "Física", "Universidad", "Electrostática", "E=F/q", "F,q", "Campo eléctrico definido como fuerza por carga de prueba."),
    Formula("Flujo de calor", "Física", "Universidad", "Transferencia de calor", "Q=mcΔT", "m,c,ΔT", "Calor sensible sin cambio de fase."),
]

# Se mantiene una única biblioteca visible para el buscador.
FORMULAS.extend(PHYSICS_FORMULAS)


def parse_number(text: str, default=None):
    try:
        return float(str(text).replace(",", ".").strip())
    except Exception:
        return default


def physics_step_solver(problem: str) -> dict:
    """Resuelve un conjunto de problemas de física frecuentes con pasos explícitos.
    Si no identifica con suficiente seguridad el tipo, no inventa datos.
    """
    t = normalize_ocr_math(problem).lower()
    steps = []
    variables = {}

    # Patrones deliberadamente sencillos y transparentes.
    m = re.search(r"(?:masa|m)\s*=\s*([0-9.,]+).*?(?:aceleraci[oó]n|a)\s*=\s*([0-9.,]+)", t)
    if m and ("fuerza" in t or "newton" in t):
        mass, acc = map(lambda x: parse_number(x), m.groups())
        force = mass * acc
        steps += [
            "Datos: masa m y aceleración a.",
            "Fórmula: F = m·a.",
            f"Sustitución: F = {mass}·{acc}.",
            f"Resultado: F = {force:g} N.",
            "Verificación: las unidades kg·m/s² equivalen a N.",
        ]
        return {"ok": True, "tipo": "Segunda ley de Newton", "resultado": force, "unidad": "N", "pasos": steps}

    m = re.search(r"(?:velocidad inicial|v0|v₀)\s*=\s*([0-9.,-]+).*?(?:aceleraci[oó]n|a)\s*=\s*([0-9.,-]+).*?(?:tiempo|t)\s*=\s*([0-9.,-]+)", t)
    if m and ("velocidad final" in t or "v final" in t or "mrua" in t):
        v0, acc, tm = [parse_number(x) for x in m.groups()]
        vf = v0 + acc * tm
        steps += [
            "Datos: v₀, a y t.",
            "Fórmula: v = v₀ + a·t.",
            f"Sustitución: v = {v0} + ({acc})({tm}).",
            f"Resultado: v = {vf:g} m/s.",
            "Verificación: se usan unidades coherentes de velocidad.",
        ]
        return {"ok": True, "tipo": "MRUA — velocidad final", "resultado": vf, "unidad": "m/s", "pasos": steps}

    m = re.search(r"(?:distancia|desplazamiento|d)\s*=\s*([0-9.,]+).*?(?:tiempo|t)\s*=\s*([0-9.,]+)", t)
    if m and "velocidad" in t:
        dist, tm = [parse_number(x) for x in m.groups()]
        if tm == 0:
            return {"ok": False, "error": "El tiempo no puede ser cero."}
        v = dist / tm
        steps += [
            "Datos: desplazamiento Δx y tiempo Δt.",
            "Fórmula: v = Δx/Δt.",
            f"Sustitución: v = {dist}/{tm}.",
            f"Resultado: v = {v:g} m/s.",
            "Verificación: distancia dividida entre tiempo produce velocidad.",
        ]
        return {"ok": True, "tipo": "Velocidad media", "resultado": v, "unidad": "m/s", "pasos": steps}

    m = re.search(r"(?:voltaje|tensi[oó]n|v)\s*=\s*([0-9.,]+).*?(?:resistencia|r)\s*=\s*([0-9.,]+)", t)
    if m and "corriente" in t:
        voltage, resistance = [parse_number(x) for x in m.groups()]
        if resistance == 0:
            return {"ok": False, "error": "La resistencia no puede ser cero para I=V/R."}
        current = voltage / resistance
        steps += [
            "Datos: tensión V y resistencia R.",
            "Fórmula: I = V/R.",
            f"Sustitución: I = {voltage}/{resistance}.",
            f"Resultado: I = {current:g} A.",
            "Verificación: V/Ω = A.",
        ]
        return {"ok": True, "tipo": "Ley de Ohm", "resultado": current, "unidad": "A", "pasos": steps}

    return {
        "ok": False,
        "error": "No identifiqué con suficiente seguridad un modelo físico resoluble automáticamente.",
        "suggestion": "Escribe los datos con unidades y el dato que quieres encontrar. Ejemplo: masa=5 kg, aceleración=2 m/s^2, encontrar fuerza."
    }


# ============================================================
# INTERFAZ
# ============================================================

if "history" not in st.session_state:
    st.session_state.history = []


st.title("∑ MathSolver AI")
st.caption("Plataforma educativa de Matemática, Física, Estadística, OCR y Cálculo")

with st.sidebar:
    st.header("Configuración")

    level = st.selectbox(
        "Nivel educativo",
        ["Liceo", "Preuniversitario", "Universidad", "Avanzado"]
    )

    language = st.selectbox(
        "Idioma",
        ["Español", "English", "Português", "Français"]
    )

    st.divider()

    section = st.radio(
        "Módulo",
        [
            "Resolver",
            "Biblioteca de fórmulas",
            "Estadística",
            "Matrices",
            "Práctica",
            "Gráficas",
            "OCR y fotos",
            "Física paso a paso",
            "Avanzado universitario",
            "Videos educativos",
            "Historial",
        ]
    )

    st.divider()
    st.write(f"📚 Fórmulas cargadas: **{len(FORMULAS)}**")
    st.caption("La base puede ampliarse sin cambiar el motor.")


# ============================================================
# RESOLVER
# ============================================================

if section == "Resolver":
    st.header("🧠 Resolver ejercicio")

    problem = st.text_area(
        "Escribe tu problema",
        placeholder=(
            "Ejemplos:\n"
            "2*x + 5 = 17\n"
            "derivada de x^3 + 2*x\n"
            "integral de x^2\n"
            "simplifica (x+1)^2\n"
            "5*(3+2)"
        ),
        height=170,
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        solve_button = st.button("🚀 Resolver", type="primary", use_container_width=True)

    with col2:
        if st.button("🎲 Generar ejercicio", use_container_width=True):
            problem = generate_practice("General", level)
            st.info(f"Ejercicio generado: {problem}")

    if solve_button and problem.strip():
        area = detect_area(problem)
        topic = detect_topic(problem)
        detected_level = detect_level(problem)

        st.markdown(
            f"""
            <div class="result-box">
            <b>Área detectada:</b> {area}<br>
            <b>Tema detectado:</b> {topic}<br>
            <b>Nivel sugerido:</b> {detected_level}
            </div>
            """,
            unsafe_allow_html=True,
        )

        result = solve_math_problem(problem)

        if "error" in result:
            st.error(result["error"])
        else:
            st.subheader("📐 Solución")

            st.write("**Tipo:**", result["tipo"])

            for i, step in enumerate(result.get("pasos", []), 1):
                st.write(f"**Paso {i}.** {step}")

            st.latex(sp.latex(result["resultado"]))

            if result.get("verificacion"):
                st.success("✅ Verificación correcta.")
            else:
                st.warning("⚠️ No se pudo confirmar completamente la verificación.")

            st.subheader("📚 Fórmulas relacionadas")

            for formula in relevant_formulas(problem, 6):
                with st.expander(formula.nombre):
                    st.write(f"**Área:** {formula.area}")
                    st.write(f"**Nivel:** {formula.nivel}")
                    st.write(f"**Tema:** {formula.tema}")
                    st.latex(formula.formula)
                    st.write(formula.descripcion)
                    if formula.condiciones:
                        st.caption(f"Condiciones: {formula.condiciones}")

                    query = formula.youtube_query or f"{formula.nombre} {formula.tema} matemática física"
                    st.link_button(
                        "▶ Buscar explicación en YouTube",
                        youtube_search_url(query),
                    )

            st.session_state.history.append({
                "problema": problem,
                "area": area,
                "tema": topic,
                "resultado": str(result["resultado"]),
            })


# ============================================================
# BIBLIOTECA
# ============================================================

elif section == "Biblioteca de fórmulas":
    st.header("📚 Biblioteca matemática y física")

    col1, col2, col3 = st.columns(3)

    with col1:
        areas = ["Todas"] + sorted(set(f.area for f in FORMULAS))
        selected_area = st.selectbox("Área", areas)

    with col2:
        levels = ["Todos"] + sorted(set(f.nivel for f in FORMULAS))
        selected_level = st.selectbox("Nivel", levels)

    with col3:
        search = st.text_input("Buscar fórmula")

    filtered = FORMULAS

    if selected_area != "Todas":
        filtered = [f for f in filtered if f.area == selected_area]

    if selected_level != "Todos":
        filtered = [f for f in filtered if selected_level in f.nivel]

    if search:
        q = normalize_text(search)
        filtered = [
            f for f in filtered
            if q in normalize_text(
                f.nombre + " " + f.tema + " " + f.descripcion + " " + f.formula
            )
        ]

    st.info(f"Se encontraron **{len(filtered)}** fórmulas.")

    for f in filtered:
        with st.expander(f"{f.nombre} — {f.tema}"):
            st.write(f"**Área:** {f.area}")
            st.write(f"**Nivel:** {f.nivel}")
            st.latex(f.formula)
            st.write(f"**Variables:** {f.variables}")
            st.write(f"**Descripción:** {f.descripcion}")
            if f.condiciones:
                st.write(f"**Condiciones:** {f.condiciones}")

            query = f.youtube_query or f"{f.nombre} {f.tema} explicación"
            st.link_button(
                "▶ Buscar explicación en YouTube",
                youtube_search_url(query),
            )


# ============================================================
# ESTADÍSTICA
# ============================================================

elif section == "Estadística":
    st.header("📊 Laboratorio de Estadística")

    raw = st.text_input(
        "Introduce números separados por comas",
        "4, 5, 5, 7, 9, 10"
    )

    try:
        values = [
            float(x.strip())
            for x in raw.split(",")
            if x.strip()
        ]

        if len(values) >= 1:
            stats = statistics_from_numbers(values)
            st.dataframe(
                pd.DataFrame(
                    list(stats.items()),
                    columns=["Medida", "Valor"]
                ),
                use_container_width=True,
                hide_index=True,
            )

            fig, ax = plt.subplots()
            ax.hist(values, bins=min(10, max(2, len(values))))
            ax.set_title("Distribución de los datos")
            ax.set_xlabel("Valor")
            ax.set_ylabel("Frecuencia")
            st.pyplot(fig)
            plt.close(fig)

    except ValueError:
        st.error("Introduce solamente números separados por comas.")


# ============================================================
# MATRICES
# ============================================================

elif section == "Matrices":
    st.header("🔢 Álgebra Lineal")

    st.write(
        "Escribe cada fila separada por ';' y cada elemento por ','. "
        "Ejemplo: `1,2;3,4`"
    )

    matrix_text = st.text_input("Matriz", "1,2;3,4")

    try:
        M = parse_matrix(matrix_text)

        st.write("Matriz:")
        st.latex(sp.latex(M))

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Filas", M.rows)

        with c2:
            st.metric("Columnas", M.cols)

        with c3:
            if M.rows == M.cols:
                st.metric("Determinante", str(M.det()))
            else:
                st.metric("Determinante", "No aplica")

        if M.rows == M.cols:
            st.write("**Rango:**", M.rank())

            if M.det() != 0:
                st.write("**Matriz inversa:**")
                st.latex(sp.latex(M.inv()))

            st.write("**Autovalores:**")
            st.write(M.eigenvals())

    except Exception as e:
        st.error(f"No se pudo interpretar la matriz: {e}")


# ============================================================
# PRÁCTICA
# ============================================================

elif section == "Práctica":
    st.header("🎯 Modo práctica")

    topic = st.selectbox(
        "Tema",
        [
            "General",
            "Álgebra",
            "Ecuaciones",
            "Derivadas",
            "Integrales",
            "Trigonometría",
            "Estadística",
            "Física",
        ]
    )

    if st.button("Generar ejercicio", type="primary"):
        exercise = generate_practice(topic, level)
        st.session_state.practice = exercise

    if "practice" in st.session_state:
        st.info(st.session_state.practice)

        answer = st.text_input("Tu respuesta")

        if st.button("Comprobar"):
            try:
                expected = solve_math_problem(st.session_state.practice)
                st.write("Resultado matemático:", expected.get("resultado"))
                st.write(
                    "Usa el desarrollo mostrado para comparar tu procedimiento."
                )
            except Exception as e:
                st.error(str(e))


# ============================================================
# GRÁFICAS
# ============================================================

elif section == "Gráficas":
    st.header("📈 Graficador matemático")

    expression = st.text_input(
        "Función en x",
        "x**2 - 4*x + 3"
    )

    xmin, xmax = st.slider(
        "Intervalo",
        -20.0, 20.0,
        (-10.0, 10.0)
    )

    if st.button("Graficar", type="primary"):
        try:
            x = sp.Symbol("x")
            expr = parse_math(expression)
            fn = sp.lambdify(x, expr, "numpy")

            xs = np.linspace(xmin, xmax, 1000)
            ys = fn(xs)

            fig, ax = plt.subplots()
            ax.plot(xs, ys)
            ax.axhline(0, linewidth=1)
            ax.axvline(0, linewidth=1)
            ax.grid(True, alpha=.25)
            ax.set_xlabel("x")
            ax.set_ylabel("f(x)")
            ax.set_title(f"f(x) = {expression}")

            st.pyplot(fig)
            plt.close(fig)

        except Exception as e:
            st.error(f"No se pudo graficar: {e}")



# ============================================================
# OCR Y FOTOS
# ============================================================

elif section == "OCR y fotos":
    st.header("📷 OCR de ejercicios y fórmulas")
    st.caption("Sube una foto de un ejercicio, una página o una fórmula. El sistema intenta extraerla y convertirla a una forma utilizable.")

    uploaded = st.file_uploader(
        "Sube una imagen",
        type=["png", "jpg", "jpeg", "webp", "bmp"],
        help="Para mejores resultados usa buena iluminación, enfoque y una sola sección del ejercicio."
    )

    if uploaded:
        image = Image.open(uploaded)
        st.image(image, caption="Imagen recibida", use_container_width=True)

        if st.button("🔎 Extraer texto y fórmula", type="primary"):
            with st.spinner("Analizando imagen..."):
                result = ocr_image(image)
            if result.get("ok"):
                st.success(f"OCR completado usando la variante: {result.get('variant')}")
                raw_text = result.get("text", "")
                st.text_area("Texto detectado", raw_text, height=180)
                normalized = normalize_ocr_math(raw_text)
                st.text_area("Versión matemática normalizada", normalized, height=120)
                st.session_state.ocr_text = normalized
            else:
                st.error(result.get("error", "No se pudo procesar la imagen."))
                st.info("Tesseract OCR es opcional. En Windows debe estar instalado además del paquete Python pytesseract.")

        st.divider()
        st.subheader("✍️ Intento de reconocimiento de fórmula manuscrita")
        st.caption("Esta función trabaja como reconocimiento asistido: puede equivocarse con exponentes, raíces o símbolos manuscritos, así que siempre revisa el resultado antes de resolverlo.")
        if st.button("Reconocer fórmula manuscrita"):
            result = recognize_handwritten_formula(image)
            if result.get("ok"):
                for i, candidate in enumerate(result.get("candidates", []), 1):
                    st.code(candidate, language="text")
                st.warning(result.get("note", "Revisa la fórmula antes de resolver."))
            else:
                st.error(result.get("error", "No se pudo reconocer la fórmula."))

        if "ocr_text" in st.session_state and st.button("🧠 Intentar resolver lo extraído"):
            try:
                solved = solve_math_problem(st.session_state.ocr_text)
                st.subheader("Resultado")
                st.write(solved)
            except Exception as exc:
                st.error(f"No se pudo resolver automáticamente: {exc}")


# ============================================================
# FÍSICA PASO A PASO
# ============================================================

elif section == "Física paso a paso":
    st.header("⚙️ Física paso a paso")
    st.caption("Modelos básicos de mecánica y electricidad con datos, fórmula, sustitución, resultado y verificación.")

    physics_problem = st.text_area(
        "Describe el problema",
        placeholder="Ejemplo: masa=5 kg, aceleración=2 m/s^2, encontrar fuerza",
        height=140,
    )

    if st.button("Resolver problema de física", type="primary"):
        result = physics_step_solver(physics_problem)
        if result.get("ok"):
            st.success(result.get("tipo", "Problema resuelto"))
            for step in result.get("pasos", []):
                st.write("•", step)
            st.metric("Resultado", f"{result['resultado']:g} {result['unidad']}")
        else:
            st.warning(result.get("error", "No se pudo resolver."))
            if result.get("suggestion"):
                st.info(result["suggestion"])

    st.divider()
    st.subheader("📚 Fórmulas de física disponibles")
    physics_df = pd.DataFrame([
        {"Fórmula": f.nombre, "Tema": f.tema, "Expresión": f.formula, "Nivel": f.nivel}
        for f in PHYSICS_FORMULAS
    ])
    st.dataframe(physics_df, use_container_width=True, hide_index=True)


# ============================================================
# AVANZADO UNIVERSITARIO
# ============================================================

elif section == "Avanzado universitario":
    st.header("🎓 Laboratorio universitario avanzado")
    st.caption("Herramientas para EDO, Laplace, Fourier, optimización y regresión.")

    tool = st.selectbox(
        "Herramienta",
        [
            "Ecuaciones diferenciales",
            "Transformada de Laplace",
            "Laplace inversa",
            "Serie de Fourier",
            "Optimización de una variable",
            "Regresión lineal",
        ]
    )

    if tool == "Ecuaciones diferenciales":
        st.subheader("Ecuaciones diferenciales ordinarias")
        st.write("Ejemplos: `y' = 2*y` o `y'' + 3*y' + 2*y = 0`")
        ode = st.text_input("EDO", "y' = 2*y")
        if st.button("Resolver EDO", type="primary"):
            try:
                result = solve_ode_expression(ode)
                st.latex(sp.latex(result))
                st.success("Solución simbólica obtenida con SymPy.")
            except Exception as exc:
                st.error(str(exc))

    elif tool == "Transformada de Laplace":
        st.subheader("Transformada de Laplace")
        expr = st.text_input("f(t)", "sin(t)")
        if st.button("Calcular Laplace", type="primary"):
            try:
                result = solve_laplace_expression(expr)
                st.latex(sp.latex(result))
            except Exception as exc:
                st.error(str(exc))

    elif tool == "Laplace inversa":
        st.subheader("Transformada inversa de Laplace")
        expr = st.text_input("F(s)", "1/(s^2+1)")
        if st.button("Calcular inversa", type="primary"):
            try:
                result = inverse_laplace_expression(expr)
                st.latex(sp.latex(result))
            except Exception as exc:
                st.error(str(exc))

    elif tool == "Serie de Fourier":
        st.subheader("Serie de Fourier")
        expr = st.text_input("f(x)", "x")
        period_half = st.number_input("Límite L del intervalo [-L,L]", value=float(math.pi), min_value=0.1)
        if st.button("Calcular serie", type="primary"):
            try:
                result = fourier_series_expression(expr, "x", (-period_half, period_half))
                st.latex(sp.latex(result.truncate(8)))
            except Exception as exc:
                st.error(str(exc))

    elif tool == "Optimización de una variable":
        st.subheader("Máximos y mínimos mediante derivadas")
        expr = st.text_input("f(x)", "x**3 - 3*x**2 + 2")
        if st.button("Optimizar", type="primary"):
            try:
                first, second, points = optimize_one_variable(expr)
                st.write("Primera derivada:")
                st.latex(sp.latex(first))
                st.write("Segunda derivada:")
                st.latex(sp.latex(second))
                if points:
                    for x0, y0, curvature, kind in points:
                        st.write(f"x = {x0} | f(x) = {y0} | f''(x) = {curvature} → **{kind}**")
                else:
                    st.info("No se encontraron puntos críticos simbólicos.")
            except Exception as exc:
                st.error(str(exc))

    elif tool == "Regresión lineal":
        st.subheader("Regresión lineal por mínimos cuadrados")
        xs = st.text_input("Valores X", "1,2,3,4,5")
        ys = st.text_input("Valores Y", "2,4,5,8,10")
        if st.button("Calcular regresión", type="primary"):
            try:
                x_values = [float(v.strip()) for v in xs.split(",") if v.strip()]
                y_values = [float(v.strip()) for v in ys.split(",") if v.strip()]
                intercept, slope, r2, corr, pred = linear_regression(x_values, y_values)
                st.latex(sp.latex(sp.Float(intercept)) + " + " + sp.latex(sp.Float(slope)) + "x")
                c1, c2 = st.columns(2)
                c1.metric("R²", f"{r2:.5f}")
                c2.metric("Correlación r", f"{corr:.5f}")
                fig, ax = plt.subplots()
                ax.scatter(x_values, y_values)
                ax.plot(x_values, pred)
                ax.set_xlabel("X")
                ax.set_ylabel("Y")
                ax.set_title("Regresión lineal")
                ax.grid(True, alpha=.25)
                st.pyplot(fig)
                plt.close(fig)
            except Exception as exc:
                st.error(str(exc))


# ============================================================
# VIDEOS
# ============================================================

elif section == "Videos educativos":
    st.header("🎥 Biblioteca de videos")

    query = st.text_input(
        "¿Qué tema quieres estudiar?",
        "derivadas desde cero"
    )

    if st.button("Buscar videos", type="primary"):
        url = youtube_search_url(query)
        st.link_button(
            "▶ Abrir resultados de YouTube",
            url,
        )

        st.info(
            "El enlace abre una búsqueda de YouTube basada en el tema. "
            "Así se evita inventar videos o enlaces que puedan dejar de existir."
        )

    st.subheader("Temas populares")

    popular = [
        "Álgebra desde cero",
        "Ecuaciones cuadráticas",
        "Trigonometría básica",
        "Derivadas desde cero",
        "Regla de la cadena",
        "Integrales desde cero",
        "Álgebra lineal",
        "Probabilidad",
        "Estadística universitaria",
        "Cálculo multivariable",
        "Ecuaciones diferenciales",
        "Mecánica clásica",
        "Electricidad y magnetismo",
        "Termodinámica",
        "Óptica",
    ]

    cols = st.columns(3)

    for i, item in enumerate(popular):
        with cols[i % 3]:
            st.link_button(
                f"▶ {item}",
                youtube_search_url(item),
                use_container_width=True,
            )


# ============================================================
# HISTORIAL
# ============================================================

elif section == "Historial":
    st.header("🕘 Historial")

    if not st.session_state.history:
        st.info("Todavía no has resuelto ejercicios en esta sesión.")
    else:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True)

        if st.button("🗑️ Limpiar historial"):
            st.session_state.history = []
            st.rerun()


# ============================================================
# PIE
# ============================================================

st.divider()
st.caption(
    "MathSolver AI v2 — motor educativo basado en Python, SymPy, NumPy y Streamlit. "
    "Las fórmulas son una base de conocimiento extensible; el motor simbólico "
    "permite resolver muchas expresiones más allá de las fórmulas catalogadas."
)
