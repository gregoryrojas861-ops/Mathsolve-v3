# MathSolver AI v3

Aplicación educativa de Matemática, Cálculo, Estadística, Álgebra Lineal y Física.

## Ejecutar en Windows / VS Code

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run mathsolver_ai.py
```

## Funciones

- Resolución simbólica con SymPy.
- Ecuaciones.
- Derivadas.
- Integrales.
- Límites.
- Simplificación.
- Factorización.
- Expansión.
- Estadística.
- Matrices.
- Álgebra lineal.
- Gráficas.
- Generador de ejercicios.
- Biblioteca de fórmulas de matemática y física.
- Clasificación por área, tema y nivel.
- Enlaces de búsqueda de YouTube.

## Importante

La base de fórmulas está diseñada para crecer. El motor SymPy también puede resolver expresiones que no estén escritas explícitamente en la biblioteca.

## v3 — ampliación OCR y Física
Esta versión incorpora:
- OCR de imágenes de ejercicios.
- Preprocesamiento de imágenes para mejorar OCR.
- Normalización de símbolos matemáticos detectados.
- Intento de reconocimiento asistido de fórmulas manuscritas.
- Laboratorio de Física paso a paso para modelos frecuentes.
- Biblioteca ampliada de fórmulas de Física.

### OCR en Windows
`pytesseract` es el puente Python, pero para OCR local también debes tener instalado Tesseract OCR en Windows y que su ejecutable esté disponible para el sistema. Si no está disponible, la aplicación seguirá funcionando en Matemática/Física, pero el OCR mostrará un aviso.
