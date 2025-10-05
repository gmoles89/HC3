# -*- coding: utf-8 -*-
"""
App: Historia clínica cardiológica (v3)
Tecnología: Streamlit (single-file)

Instalación:
  pip install streamlit pydantic pandas
Ejecución:
  streamlit run app_v3.py

Cambios solicitados:
- Agregada Hipertensión arterial (Sí/No).
- Agregados antecedentes por sistemas (campos de texto y números).
- Medicación: nombre + dosis (número) + unidad (mg/gr/ng/mcg) + frecuencia (texto).
- Exámenes complementarios: fecha (selector de fecha) + descripción.
- Validaciones numéricas (edad 1–110, TAS 1–300, TAD 1–200, peso/altura con 2 decimales).
"""

from __future__ import annotations
import json
from datetime import date
from typing import List

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pydantic import BaseModel, Field, ValidationError, conint, confloat

# ---------------- Configuración de página ----------------
st.set_page_config(
    page_title="Historia clínica cardiológica",
    page_icon="❤️",
    layout="centered",
)
st.title("Historia clínica cardiológica")
st.caption("Formulario estructurado para registro clínico.")

# ---------------- Modelos de datos ----------------
class Paciente(BaseModel):
    # use plain types in annotations and enforce constraints via Field to avoid
    # call expressions in type position (static checkers)
    edad: int = Field(..., ge=1, le=110)
    sexo: str = Field(..., pattern=r"^(M|F)$")
    tabaquismo: str = Field(..., pattern=r"^(Si|No|Ex\s*tabaquista|Extabaquista)$")
    diabetes: str = Field(..., pattern=r"^(Si|No)$")
    dislipemia: str = Field(..., pattern=r"^(Si|No)$")
    hta: str = Field(..., pattern=r"^(Si|No)$")
    antecedentes_familiares: str = Field(..., pattern=r"^(Si|No)$")
    peso_kg: float = Field(..., ge=1, le=500)
    altura_m: float = Field(..., ge=0.4, le=2.5)
    alergias: str = Field(..., pattern=r"^(Si|No)$")
    ant_neurologicos: str = Field(default="")
    ant_cardiovasculares: str = Field(default="")
    ant_respiratorios: str = Field(default="")
    ant_gastrointestinales: str = Field(default="")
    ant_nefrourologicos: str = Field(default="")
    ant_traumatologicos: str = Field(default="")
    ant_otros: str = Field(default="")
    ant_gineco_obstetricos: str = Field(default="")

class Medicacion(BaseModel):
    nombre: str
    dosis: float = Field(..., gt=0)
    unidad: str = Field(..., pattern=r"^(mg|gr|ng|mcg)$")
    frecuencia: str

class ExamenFisico(BaseModel):
    neurologico: str = Field(default="")
    cardiovascular: str = Field(default="")
    respiratorio: str = Field(default="")
    gastrointestinal: str = Field(default="")
    genitourinario: str = Field(default="")
    piel_partes_blandas: str = Field(default="")
    tas: int = Field(..., ge=1, le=300)
    tad: int = Field(..., ge=1, le=200)

class ExamenComplementario(BaseModel):
    fecha: str  # ISO (YYYY-MM-DD)
    descripcion: str

class EvaluacionIndicaciones(BaseModel):
    texto: str = ""
    estado_clinico: str = Field(default="")

class HistoriaClinica(BaseModel):
    paciente: Paciente
    medicacion: List[Medicacion]
    examen_fisico: ExamenFisico
    examenes_complementarios: List[ExamenComplementario]
    evaluacion_indicaciones: EvaluacionIndicaciones


def historia_as_json(hc: HistoriaClinica) -> str:
    """Return the HistoriaClinica as a JSON string using python's json.dumps.

    Uses hc.model_dump() to produce a plain dict and then encodes it with
    ensure_ascii=False so non-ASCII characters are preserved.
    """
    # Compute BMI from paciente fields if available and include it in the output
    hc_dict = hc.model_dump()
    try:
        p = hc_dict.get("paciente", {})
        peso = p.get("peso_kg")
        altura = p.get("altura_m")
        if peso is not None and altura:
            # protect against division by zero
            imc = None
            try:
                imc = round(float(peso) / (float(altura) ** 2), 2)
            except Exception:
                imc = None
            p["imc"] = imc
        hc_dict["paciente"] = p
    except Exception:
        # if anything goes wrong, fall back to original dump
        return json.dumps(hc.model_dump(), indent=2, ensure_ascii=False)

    return json.dumps(hc_dict, indent=2, ensure_ascii=False)


def _fmt_ant(valor: str, nombre: str) -> str:
    """Formatea una entrada de antecedentes para el resumen.

    Si `valor` está vacío o solo contiene espacios retorna
    'No presenta antecedentes <nombre> conocidos'. Si tiene texto, lo retorna tal cual.
    """
    if valor is None:
        return f"No presenta antecedentes {nombre} conocidos"
    s = str(valor).strip()
    if not s:
        return f"No presenta antecedentes {nombre} conocidos"
    return s

# ---------------- Estado inicial ----------------
if "meds_df" not in st.session_state:
    st.session_state.meds_df = pd.DataFrame({
        "nombre": [""],
        "dosis": [0.0],
        "unidad": ["mg"],
        "frecuencia": [""]
    })

if "exams_df" not in st.session_state:
    st.session_state.exams_df = pd.DataFrame({
        "fecha": [date.today()],
        "descripcion": [""]
    })

# ---------------- Sección: Datos del paciente ----------------
## ---------------- Sección: Estado clínico (primer bloque) ----------------
st.header("Estado clínico")
estado_clinico = st.text_area(
    "Estado clínico",
    height=120,
    placeholder="Estado clínico: signos, síntomas, hallazgos físicos relevantes (puede contener letras y números)",
)

st.divider()

## ---------------- Sección: Datos del paciente ----------------
st.header("Datos del paciente")
col1, col2, col3 = st.columns(3)
with col1:
    edad = st.number_input("Edad", min_value=1, max_value=110, step=1)
with col2:
    sexo = st.selectbox("Sexo", ["M", "F"], index=0)
with col3:
    tabaquismo = st.selectbox("Tabaquismo", ["No", "Si", "Ex tabaquista", "Extabaquista"], index=0)

col4, col5, col6 = st.columns(3)
with col4:
    diabetes = st.selectbox("Diabetes", ["No", "Si"], index=0)
with col5:
    dislipemia = st.selectbox("Dislipemia", ["No", "Si"], index=0)
with col6:
    hta = st.selectbox("Hipertensión arterial", ["No", "Si"], index=0)

col7, col8, col9 = st.columns(3)
with col7:
    antecedentes_familiares = st.selectbox("Antecedentes Familiares", ["No", "Si"], index=0)
with col8:
    peso_kg = st.number_input("Peso (kg)", min_value=1.0, max_value=500.0, step=0.1, format="%.2f")
with col9:
    altura_m = st.number_input("Altura (m)", min_value=0.4, max_value=2.5, step=0.01, format="%.2f")

col10, = st.columns(1)
with col10:
    alergias = st.selectbox("Alergias", ["No", "Si"], index=0)

st.markdown("**Antecedentes por sistemas**")
ant_neurologicos = st.text_area("Antecedentes neurológicos")
ant_cardiovasculares = st.text_area("Antecedentes cardiovasculares")
ant_respiratorios = st.text_area("Antecedentes respiratorios")
ant_gastrointestinales = st.text_area("Antecedentes gastrointestinales")
ant_nefrourologicos = st.text_area("Antecedentes nefro-urológicos")
ant_traumatologicos = st.text_area("Antecedentes traumatológicos")
ant_gineco_obstetricos = st.text_area("Antecedentes gineco-obstétricos")
ant_otros = st.text_area("Otros antecedentes")

st.divider()

# ---------------- Sección: Medicación habitual ----------------
st.header("Medicación habitual")
st.caption("Complete nombre, dosis, unidad y frecuencia. Use +/− para agregar o quitar filas.")

st.session_state.meds_df = st.data_editor(
    st.session_state.meds_df,
    num_rows="dynamic",
    column_config={
        "nombre": st.column_config.TextColumn("Nombre"),
        "dosis": st.column_config.NumberColumn("Dosis", min_value=0.0, step=0.5, format="%.2f"),
        "unidad": st.column_config.SelectboxColumn("Unidad", options=["mg", "gr", "ng", "mcg"]),
        "frecuencia": st.column_config.TextColumn("Frecuencia"),
    },
    width='stretch',
)

st.divider()

# ---------------- Sección: Examen físico ----------------
st.header("Examen físico")
neurologico = st.text_area("Examen neurológico")
cardio = st.text_area("Examen cardiovascular")
respiratorio = st.text_area("Examen respiratorio")
gastro = st.text_area("Examen gastrointestinal")
genitourinario = st.text_area("Examen genitourinario")
piel = st.text_area("Examen de piel y partes blandas")

col_ta1, col_ta2 = st.columns(2)
with col_ta1:
    tas = st.number_input("TAS (mmHg)", min_value=1, max_value=300, step=1)
with col_ta2:
    tad = st.number_input("TAD (mmHg)", min_value=1, max_value=200, step=1)

st.divider()

# ---------------- Sección: Exámenes complementarios ----------------
st.header("Exámenes complementarios")
st.caption("Seleccione fecha y describa el resultado.")

# Editor de tabla con fecha tipo texto ISO para facilitar exportación JSON
st.session_state.exams_df = st.data_editor(
    st.session_state.exams_df,
    num_rows="dynamic",
    column_config={
        "fecha": st.column_config.DateColumn("Fecha"),
        "descripcion": st.column_config.TextColumn("Descripción"),
    },
    width='stretch',
)

st.divider()

# ---------------- Sección: Evaluación e Indicaciones ----------------
st.header("Evaluación e Indicaciones")
eval_texto = st.text_area(
    "Detalle (texto y números)",
    height=220,
    placeholder="Decisiones respecto al paciente, conducta, objetivos, farmacoterapia, seguimiento, etc.",
)


st.divider()

# ---------------- Botón de validación y vista previa ----------------
if st.button("Generar vista previa del informe"):
    try:
        # Paciente
        datos_paciente = Paciente(
            edad=edad,
            sexo=sexo,
            tabaquismo=tabaquismo,
            diabetes=diabetes,
            dislipemia=dislipemia,
            hta=hta,
            antecedentes_familiares=antecedentes_familiares,
            peso_kg=peso_kg,
            altura_m=altura_m,
            alergias=alergias,
            ant_neurologicos=ant_neurologicos,
            ant_cardiovasculares=ant_cardiovasculares,
            ant_respiratorios=ant_respiratorios,
            ant_gastrointestinales=ant_gastrointestinales,
            ant_nefrourologicos=ant_nefrourologicos,
            ant_traumatologicos=ant_traumatologicos,
            ant_otros=ant_otros,
            ant_gineco_obstetricos=ant_gineco_obstetricos,
        )
        
        # Medicación (filtrar filas vacías)
        meds_rows = st.session_state.meds_df.replace({pd.NA: None}).to_dict(orient="records")
        meds = [Medicacion(**r) for r in meds_rows if r.get("nombre")]

        # Examen físico
        examen_fisico = ExamenFisico(
            neurologico=neurologico,
            cardiovascular=cardio,
            respiratorio=respiratorio,
            gastrointestinal=gastro,
            genitourinario=genitourinario,
            piel_partes_blandas=piel,
            tas=tas,
            tad=tad,
        )

        # Exámenes complementarios (normalizar fecha a ISO string)
        exams_rows = st.session_state.exams_df.replace({pd.NA: None}).to_dict(orient="records")
        normalized_exams = []
        for r in exams_rows:
            f = r.get("fecha")
            if isinstance(f, str):
                fecha_iso = f
            elif f is None:
                fecha_iso = ""
            else:
                # Date object
                fecha_iso = f.isoformat()
            if r.get("descripcion") or fecha_iso:
                normalized_exams.append(ExamenComplementario(fecha=fecha_iso, descripcion=r.get("descripcion", "")))

        # Evaluación
        evaluacion = EvaluacionIndicaciones(texto=eval_texto, estado_clinico=estado_clinico)

        # Historia completa
        hc = HistoriaClinica(
            paciente=datos_paciente,
            medicacion=meds,
            examen_fisico=examen_fisico,
            examenes_complementarios=normalized_exams,
            evaluacion_indicaciones=evaluacion,
        )

        st.success("Datos validados correctamente.")
        st.subheader("Resumen estructurado")

        # Mostrar Estado clínico primero
        st.markdown("**Estado clínico**")
        st.write(hc.evaluacion_indicaciones.estado_clinico or "—")

        # Paciente
        p = hc.paciente
        # calcular IMC para mostrar en pantalla (protección contra división por cero)
        imc_display = None
        try:
            if p.altura_m and p.peso_kg:
                imc_display = round(float(p.peso_kg) / (float(p.altura_m) ** 2), 2)
        except Exception:
            imc_display = None
        imc_line = f" | IMC: {imc_display:.2f}" if imc_display is not None else ""

        st.markdown(
            f"""
            **Paciente**  
            - Edad: **{p.edad}** años  
            - Sexo: **{p.sexo}**  
            - Tabaquismo: **{p.tabaquismo}**  
            - Diabetes: **{p.diabetes}**  
            - Dislipemia: **{p.dislipemia}**  
            - Hipertensión arterial: **{p.hta}**  
            - Antecedentes familiares: **{p.antecedentes_familiares}**  
            - Peso: **{p.peso_kg:.2f} kg** | Altura: **{p.altura_m:.2f} m**{imc_line}  
            - Alergias: **{p.alergias}**

            **Antecedentes por sistemas**  
            - Neurológicos: {_fmt_ant(p.ant_neurologicos, 'neurológicos')}  
            - Cardiovasculares: {_fmt_ant(p.ant_cardiovasculares, 'cardiovasculares')}  
            - Respiratorios: {_fmt_ant(p.ant_respiratorios, 'respiratorios')}  
            - Gastrointestinales: {_fmt_ant(p.ant_gastrointestinales, 'gastrointestinales')}  
            - Nefro-urológicos: {_fmt_ant(p.ant_nefrourologicos, 'nefro-urológicos')}  
            - Traumatológicos: {_fmt_ant(p.ant_traumatologicos, 'traumatológicos')}  
            - Gineco-obstétricos: {_fmt_ant(p.ant_gineco_obstetricos, 'gineco-obstétricos')}  
            - Otros: {_fmt_ant(p.ant_otros, 'otros')}
            """
        )

        # Medicación
        st.markdown("**Medicación habitual**")
        if hc.medicacion:
            for m in hc.medicacion:
                st.write(f"• {m.nombre}: {m.dosis} {m.unidad}, {m.frecuencia}")
        else:
            st.write("• Sin medicación informada")

        # Examen físico
        ef = hc.examen_fisico
        st.markdown("**Examen físico**")
        st.write(f"Neurológico: {ef.neurologico or '—'}")
        st.write(f"Cardiovascular: {ef.cardiovascular or '—'}")
        st.write(f"Respiratorio: {ef.respiratorio or '—'}")
        st.write(f"Gastrointestinal: {ef.gastrointestinal or '—'}")
        st.write(f"Genitourinario: {ef.genitourinario or '—'}")
        st.write(f"Piel y partes blandas: {ef.piel_partes_blandas or '—'}")
        st.write(f"Tensión arterial: TAS {ef.tas} / TAD {ef.tad} mmHg")

        # Exámenes complementarios
        st.markdown("**Exámenes complementarios**")
        if hc.examenes_complementarios:
            for e in hc.examenes_complementarios:
                st.write(f"• Fecha: {e.fecha or '—'} — {e.descripcion}")
        else:
            st.write("• No registrados")

        # Evaluación
        st.markdown("**Evaluación e Indicaciones**")
        st.write(hc.evaluacion_indicaciones.texto or "—")

        # Construir texto plano del informe para copiar al portapapeles
        lines = []
        lines.append("Estado clínico:")
        lines.append(hc.evaluacion_indicaciones.estado_clinico or "-")
        lines.append("")
        lines.append("Paciente:")
        lines.append(f"Edad: {p.edad} años")
        lines.append(f"Sexo: {p.sexo}")
        lines.append(f"Tabaquismo: {p.tabaquismo}")
        lines.append(f"Diabetes: {p.diabetes}")
        lines.append(f"Dislipemia: {p.dislipemia}")
        lines.append(f"Hipertensión arterial: {p.hta}")
        lines.append(f"Antecedentes familiares: {p.antecedentes_familiares}")
        lines.append(f"Peso: {p.peso_kg:.2f} kg | Altura: {p.altura_m:.2f} m")
        lines.append(f"Alergias: {p.alergias}")
        lines.append("")
        lines.append("Antecedentes por sistemas:")
        lines.append(f"Neurológicos: {_fmt_ant(p.ant_neurologicos, 'neurológicos')}")
        lines.append(f"Cardiovasculares: {_fmt_ant(p.ant_cardiovasculares, 'cardiovasculares')}")
        lines.append(f"Respiratorios: {_fmt_ant(p.ant_respiratorios, 'respiratorios')}")
        lines.append(f"Gastrointestinales: {_fmt_ant(p.ant_gastrointestinales, 'gastrointestinales')}")
        lines.append(f"Nefro-urológicos: {_fmt_ant(p.ant_nefrourologicos, 'nefro-urológicos')}")
        lines.append(f"Traumatológicos: {_fmt_ant(p.ant_traumatologicos, 'traumatológicos')}")
        lines.append(f"Gineco-obstétricos: {_fmt_ant(p.ant_gineco_obstetricos, 'gineco-obstétricos')}")
        lines.append(f"Otros: {_fmt_ant(p.ant_otros, 'otros')}")
        lines.append("")
        # Medicación
        lines.append("Medicación habitual:")
        if hc.medicacion:
            for m in hc.medicacion:
                lines.append(f"- {m.nombre}: {m.dosis} {m.unidad}, {m.frecuencia}")
        else:
            lines.append("- Sin medicación informada")
        # Examen físico resumen corto: incluir solo secciones completadas
        lines.append("")
        lines.append("Examen físico:")
        if ef.neurologico and str(ef.neurologico).strip():
            lines.append(f"Neurológico: {ef.neurologico}")
        if ef.cardiovascular and str(ef.cardiovascular).strip():
            lines.append(f"Cardiovascular: {ef.cardiovascular}")
        if ef.respiratorio and str(ef.respiratorio).strip():
            lines.append(f"Respiratorio: {ef.respiratorio}")
        if ef.gastrointestinal and str(ef.gastrointestinal).strip():
            lines.append(f"Gastrointestinal: {ef.gastrointestinal}")
        if ef.genitourinario and str(ef.genitourinario).strip():
            lines.append(f"Genitourinario: {ef.genitourinario}")
        if ef.piel_partes_blandas and str(ef.piel_partes_blandas).strip():
            lines.append(f"Piel y partes blandas: {ef.piel_partes_blandas}")
        # Siempre incluir la tensión arterial (es numérica y obligatoria en el modelo)
        lines.append(f"Tensión arterial: TAS {ef.tas} / TAD {ef.tad} mmHg")

        report_text = "\n".join(lines)

        # Botón para copiar al portapapeles (usa componente HTML/JS con fallback)
        if st.button("Copiar informe al portapapeles"):
            html = (
                "<script>" +
                "(async function(){\n" +
                "  const text = " + json.dumps(report_text) + ";\n" +
                "  try{\n" +
                "    if(navigator && navigator.clipboard && navigator.clipboard.writeText){\n" +
                "      await navigator.clipboard.writeText(text);\n" +
                "      alert('Informe copiado al portapapeles');\n" +
                "      return;\n" +
                "    }\n" +
                "  }catch(e){}\n" +
                "  // fallback: create a textarea, select and execCommand('copy')\n" +
                "  try{\n" +
                "    var ta = document.createElement('textarea');\n" +
                "    ta.value = text;\n" +
                "    document.body.appendChild(ta);\n" +
                "    ta.select();\n" +
                "    document.execCommand('copy');\n" +
                "    ta.remove();\n" +
                "    alert('Informe copiado al portapapeles (fallback)');\n" +
                "    return;\n" +
                "  }catch(e){\n" +
                "    alert('No fue posible copiar al portapapeles desde este entorno.');\n" +
                "  }\n" +
                "})();" +
                "</script>"
            )
            components.html(html, height=10)

        # Exportar JSON
        st.download_button(
            label="Descargar JSON de la historia",
            data=historia_as_json(hc),
            file_name="historia_clinica_cardiologica.json",
            mime="application/json",
        )

    except ValidationError as e:
        st.error("Errores de validación:")
        for err in e.errors():
            st.write(f"- {err['loc']}: {err['msg']}")

st.info("Nota: Esta versión no persiste datos ni exporta PDF. Se puede agregar si lo necesitás.")

# Botón para abrir calculadora de riesgo cardiovascular (abre en nueva pestaña)
st.markdown(
        """
        <div style="display:flex; gap:8px">
            <a href="https://www.paho.org/cardioapp/web/#/cvrisk" target="_blank"><button>Calcular riesgo cardiovascular</button></a>
            <a href="https://www.paho.org/cardioapp/web/#/renalrisk" target="_blank"><button>Calcular filtrado glomerular</button></a>
        </div>
        """,
        unsafe_allow_html=True,
)
