import runpy
import json
from datetime import date
from pydantic import ValidationError

m = runpy.run_path(r"c:\Users\Tavi\Desktop\HC3\historia_clinica_cardiologica_app_v_3.py")
Paciente = m['Paciente']
Medicacion = m['Medicacion']
ExamenFisico = m['ExamenFisico']
ExamenComplementario = m['ExamenComplementario']
HistoriaClinica = m['HistoriaClinica']
historia_as_json = m['historia_as_json']


def test_json_export_and_structure():
    # build minimal valid historia
    p = Paciente(
        edad=40,
        sexo='F',
        tabaquismo='No',
        diabetes='No',
        dislipemia='No',
        hta='No',
        antecedentes_familiares='No',
        peso_kg=65.0,
        altura_m=1.6,
        alergias='No'
    )
    m1 = Medicacion(nombre='Aspirina', dosis=75.0, unidad='mg', frecuencia='Diaria')
    ef = ExamenFisico(tas=110, tad=70)
    ex = ExamenComplementario(fecha=date.today().isoformat(), descripcion='Normal')

    hc = HistoriaClinica(
        paciente=p,
        medicacion=[m1],
        examen_fisico=ef,
        examenes_complementarios=[ex],
        evaluacion_indicaciones={'texto':'OK'}
    )

    # validate model_dump_json compatibility and helper
    expected = json.dumps(hc.model_dump(), indent=2, ensure_ascii=False)
    got = historia_as_json(hc)
    assert expected == got
    assert 'paciente' in got
    assert 'medicacion' in got
    assert 'examenes_complementarios' in got


def test_medicacion_filtering():
    # simulate the data_editor -> to_dict records with an empty row
    rows = [
        {'nombre': 'Aspirina', 'dosis': 100.0, 'unidad': 'mg', 'frecuencia': 'Diaria'},
        {'nombre': '', 'dosis': 0.0, 'unidad': 'mg', 'frecuencia': ''},
    ]
    meds = [Medicacion(**r) for r in rows if r.get('nombre')]
    assert len(meds) == 1
    assert meds[0].nombre == 'Aspirina'


def test_date_normalization_from_mixed_types():
    # The app normalizes dates from strings and date objects.
    # emulate mixed inputs
    raw = [
        {'fecha': date.today(), 'descripcion': 'A'},
        {'fecha': date.today().isoformat(), 'descripcion': 'B'},
        {'fecha': None, 'descripcion': ''},
    ]

    normalized = []
    for r in raw:
        f = r.get('fecha')
        if isinstance(f, str):
            fecha_iso = f
        elif f is None:
            fecha_iso = ''
        else:
            fecha_iso = f.isoformat()
        if r.get('descripcion') or fecha_iso:
            normalized.append({'fecha': fecha_iso, 'descripcion': r.get('descripcion', '')})

    assert len(normalized) == 2
    assert normalized[0]['fecha'] == date.today().isoformat()
    assert normalized[1]['fecha'] == date.today().isoformat()
