import runpy
import runpy
from datetime import date
import pytest
from pydantic import ValidationError

# Load the module and extract model classes
module = runpy.run_path(r"c:\Users\Tavi\Desktop\HC3\historia_clinica_cardiologica_app_v_3.py")
Paciente = module["Paciente"]
Medicacion = module["Medicacion"]
ExamenFisico = module["ExamenFisico"]
ExamenComplementario = module["ExamenComplementario"]
HistoriaClinica = module["HistoriaClinica"]


def make_valid_payload():
    paciente = Paciente(
        edad=45,
        sexo="M",
        tabaquismo="No",
        diabetes="No",
        dislipemia="No",
        hta="No",
        antecedentes_familiares="No",
        peso_kg=75.5,
        altura_m=1.72,
        alergias="No",
    )

    medicacion = [Medicacion(nombre="Aspirina", dosis=100.0, unidad="mg", frecuencia="Diaria")]

    examen_fisico = ExamenFisico(tas=120, tad=80)

    examenes = [ExamenComplementario(fecha=date.today().isoformat(), descripcion="ECG normal")]

    hc = HistoriaClinica(
        paciente=paciente,
        medicacion=medicacion,
        examen_fisico=examen_fisico,
        examenes_complementarios=examenes,
        evaluacion_indicaciones={"texto": "Sin observaciones"},
    )
    return hc


def test_valid_historia_creates():
    hc = make_valid_payload()
    assert hc.paciente.edad == 45
    assert len(hc.medicacion) == 1


def test_invalid_peso_raises():
    paciente_data = dict(
        edad=30,
        sexo="F",
        tabaquismo="No",
        diabetes="No",
        dislipemia="No",
        hta="No",
        antecedentes_familiares="No",
        peso_kg=0.1,  # invalid, too small
        altura_m=1.6,
        alergias="No",
    )
    with pytest.raises(ValidationError):
        Paciente(**paciente_data)
