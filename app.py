# app.py - HT Parts Management Database
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import sqlite3
import os
import json

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'tz-databaze.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'dwg', 'dxf', 'png', 'jpg', 'jpeg', 'xlsx', 'xls', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db


def save_file(file, subfolder):
    """Save uploaded file, return relative path or None."""
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        folder = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        return subfolder + '/' + filename
    return None


def save_files(files_list, subfolder):
    """Save multiple uploaded files, return list of relative paths."""
    paths = []
    for file in files_list:
        path = save_file(file, subfolder)
        if path:
            paths.append(path)
    return paths


def init_db():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS Materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            norm TEXT,
            type TEXT,
            C_min REAL, C_max REAL,
            Si_min REAL, Si_max REAL,
            Mn_min REAL, Mn_max REAL,
            P_min REAL, P_max REAL,
            S_min REAL, S_max REAL,
            Cr_min REAL, Cr_max REAL,
            Ni_min REAL, Ni_max REAL,
            Mo_min REAL, Mo_max REAL,
            V_min REAL, V_max REAL,
            Pb_min REAL, Pb_max REAL,
            Hardening_Temp_Oil_min INTEGER, Hardening_Temp_Oil_max INTEGER,
            Hardening_Temp_Water_min INTEGER, Hardening_Temp_Water_max INTEGER,
            Tempering_Temp_min INTEGER, Tempering_Temp_max INTEGER,
            Temp_Cementace_min INTEGER, Temp_Cementace_max INTEGER,
            Temp_Nitrocementace_min INTEGER, Temp_Nitrocementace_max INTEGER,
            Temp_Nitridace_min INTEGER, Temp_Nitridace_max INTEGER,
            Temp_Karbonitridace_min INTEGER, Temp_Karbonitridace_max INTEGER,
            Hardness_min INTEGER, Hardness_max INTEGER,
            Hardness_Unit TEXT DEFAULT 'HRC',
            Note TEXT,
            pdf_path TEXT,
            pdf_paths TEXT
        );

        CREATE TABLE IF NOT EXISTS Machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            Temperature_max INTEGER,
            aktivni INTEGER DEFAULT 1,
            technology TEXT,
            Max_Load REAL,
            manual_path TEXT,
            manual_paths TEXT
        );

        CREATE TABLE IF NOT EXISTS Parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_part TEXT NOT NULL,
            SAP_code TEXT,
            Drawing_number TEXT,
            Material_id INTEGER REFERENCES Materials(id),
            Machine_id INTEGER REFERENCES Machines(id),
            diameter REAL,
            length REAL,
            width REAL,
            height REAL,
            weight_g REAL,
            annual_volume_pcs INTEGER,
            batch_size_pcs INTEGER,
            HT_technology TEXT,
            HT_temperature INTEGER,
            Tempering_temperature INTEGER,
            HT_time INTEGER,
            Tempering_time INTEGER,
            Surface_Hardness_min INTEGER,
            Surface_Hardness_max INTEGER,
            Surface_Hardness_Unit TEXT DEFAULT 'HRC',
            Core_Hardness_min INTEGER,
            Core_Hardness_max INTEGER,
            Core_Hardness_Unit TEXT DEFAULT 'HRC',
            CHD_min REAL, CHD_max REAL,
            EHT_min REAL, EHT_max REAL,
            CLT_min REAL, CLT_max REAL,
            NHD_min REAL, NHD_max REAL,
            Porosity_max REAL,
            Soft_Points TEXT,
            HT_Specifications TEXT,
            Note TEXT,
            drawing_path TEXT,
            calculation_path TEXT,
            vytvoreno TEXT DEFAULT (datetime('now')),
            upraveno TEXT DEFAULT (datetime('now'))
        );
    ''')
    # Migrations for existing databases
    for sql in [
        "ALTER TABLE Materials ADD COLUMN pdf_path TEXT",
        "ALTER TABLE Materials ADD COLUMN pdf_paths TEXT",
        "ALTER TABLE Materials ADD COLUMN Temp_Cementace_min INTEGER",
        "ALTER TABLE Materials ADD COLUMN Temp_Cementace_max INTEGER",
        "ALTER TABLE Materials ADD COLUMN Temp_Nitrocementace_min INTEGER",
        "ALTER TABLE Materials ADD COLUMN Temp_Nitrocementace_max INTEGER",
        "ALTER TABLE Materials ADD COLUMN Temp_Nitridace_min INTEGER",
        "ALTER TABLE Materials ADD COLUMN Temp_Nitridace_max INTEGER",
        "ALTER TABLE Materials ADD COLUMN Temp_Karbonitridace_min INTEGER",
        "ALTER TABLE Materials ADD COLUMN Temp_Karbonitridace_max INTEGER",
        "ALTER TABLE Machines ADD COLUMN manual_path TEXT",
        "ALTER TABLE Machines ADD COLUMN manual_paths TEXT",
        "ALTER TABLE Parts ADD COLUMN weight_g REAL",
        "ALTER TABLE Parts ADD COLUMN drawing_path TEXT",
        "ALTER TABLE Parts ADD COLUMN calculation_path TEXT",
        "ALTER TABLE Parts ADD COLUMN EHT_min REAL",
        "ALTER TABLE Parts ADD COLUMN EHT_max REAL",
        "ALTER TABLE Parts ADD COLUMN Soft_Points TEXT",
    ]:
        try:
            db.execute(sql)
        except Exception:
            pass
    db.commit()
    db.close()


# ── Serve uploaded files ──────────────────────────────────────────────────────

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ── PARTS ─────────────────────────────────────────────────────────────────────

@app.route('/')
def Parts():
    db = get_db()
    search = request.args.get('q', '')
    if search:
        parts = db.execute('''
            SELECT d.*, m.name AS material_name, ma.name AS machine_name
            FROM Parts d
            LEFT JOIN Materials m ON d.Material_id = m.id
            LEFT JOIN Machines ma ON d.Machine_id = ma.id
            WHERE d.name_part LIKE ? OR d.SAP_code LIKE ? OR d.Drawing_number LIKE ?
            ORDER BY d.name_part
        ''', (f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    else:
        parts = db.execute('''
            SELECT d.*, m.name AS material_name, ma.name AS machine_name
            FROM Parts d
            LEFT JOIN Materials m ON d.Material_id = m.id
            LEFT JOIN Machines ma ON d.Machine_id = ma.id
            ORDER BY d.name_part
        ''').fetchall()
    quantity = db.execute('SELECT COUNT(*) FROM Parts').fetchone()[0]
    db.close()
    return render_template('parts.html', parts=parts, search=search, quantity=quantity)


@app.route('/Parts/<int:id>')
def parts_detail(id):
    db = get_db()
    part = db.execute('''
        SELECT d.*,
               m.name AS material_name, m.norm AS material_norm, m.type AS material_type,
               m.C_min, m.C_max, m.Si_min, m.Si_max, m.Mn_min, m.Mn_max,
               m.P_min, m.P_max, m.S_min, m.S_max, m.Cr_min, m.Cr_max,
               m.Ni_min, m.Ni_max, m.Mo_min, m.Mo_max, m.V_min, m.V_max,
               m.Pb_min, m.Pb_max,
               m.Hardening_Temp_Oil_min, m.Hardening_Temp_Oil_max,
               m.Hardening_Temp_Water_min, m.Hardening_Temp_Water_max,
               m.Tempering_Temp_min, m.Tempering_Temp_max,
               m.pdf_path AS material_pdf, m.pdf_paths AS material_pdf_paths,
               ma.name AS machine_name, ma.type AS machine_type,
               ma.manual_path AS machine_manual, ma.manual_paths AS machine_manual_paths
        FROM Parts d
        LEFT JOIN Materials m ON d.Material_id = m.id
        LEFT JOIN Machines ma ON d.Machine_id = ma.id
        WHERE d.id = ?
    ''', (id,)).fetchone()
    db.close()
    if part is None:
        return 'Part not found', 404
    return render_template('part_detail.html', part=part)


@app.route('/add', methods=['GET', 'POST'])
@app.route('/change/<int:id>', methods=['GET', 'POST'])
def parts_form(id=None):
    db = get_db()
    materials = db.execute('SELECT id, name FROM Materials ORDER BY name').fetchall()
    machines = db.execute('SELECT id, name FROM Machines WHERE aktivni=1 ORDER BY name').fetchall()

    if request.method == 'POST':
        name_part = request.form.get('name_part', '').strip()
        if not name_part:
            part = db.execute('SELECT * FROM Parts WHERE id=?', (id,)).fetchone() if id else None
            db.close()
            return render_template('part_form.html', materials=materials, machines=machines,
                                   error='Název dílu je povinný!', part=request.form, id=id)

        drawing = save_file(request.files.get('drawing_file'), 'parts')
        calculation = save_file(request.files.get('calculation_file'), 'parts')

        f = request.form
        def s(k): return f.get(k, '').strip() or None
        def n(k): return f.get(k) or None

        if id:
            existing = db.execute('SELECT drawing_path, calculation_path FROM Parts WHERE id=?', (id,)).fetchone()
            if not drawing and existing:
                drawing = existing['drawing_path']
            if not calculation and existing:
                calculation = existing['calculation_path']
            db.execute('''
                UPDATE Parts SET
                    name_part=?, SAP_code=?, Drawing_number=?,
                    Material_id=?, Machine_id=?,
                    diameter=?, length=?, width=?, height=?, weight_g=?,
                    annual_volume_pcs=?, batch_size_pcs=?,
                    HT_technology=?, HT_temperature=?, Tempering_temperature=?,
                    HT_time=?, Tempering_time=?,
                    Surface_Hardness_min=?, Surface_Hardness_max=?, Surface_Hardness_Unit=?,
                    Core_Hardness_min=?, Core_Hardness_max=?, Core_Hardness_Unit=?,
                    CHD_min=?, CHD_max=?, EHT_min=?, EHT_max=?,
                    CLT_min=?, CLT_max=?,
                    NHD_min=?, NHD_max=?, Porosity_max=?, Soft_Points=?,
                    HT_Specifications=?, Note=?,
                    drawing_path=?, calculation_path=?,
                    upraveno=datetime('now')
                WHERE id=?
            ''', (name_part, s('SAP_code'), s('Drawing_number'),
                  n('Material_id'), n('Machine_id'),
                  n('diameter'), n('length'), n('width'), n('height'), n('weight_g'),
                  n('annual_volume_pcs'), n('batch_size_pcs'),
                  s('HT_technology'), n('HT_temperature'), n('Tempering_temperature'),
                  n('HT_time'), n('Tempering_time'),
                  n('Surface_Hardness_min'), n('Surface_Hardness_max'), s('Surface_Hardness_Unit') or 'HRC',
                  n('Core_Hardness_min'), n('Core_Hardness_max'), s('Core_Hardness_Unit') or 'HRC',
                  n('CHD_min'), n('CHD_max'), n('EHT_min'), n('EHT_max'),
                  n('CLT_min'), n('CLT_max'),
                  n('NHD_min'), n('NHD_max'), n('Porosity_max'), s('Soft_Points'),
                  s('HT_Specifications'), s('Note'),
                  drawing, calculation, id))
        else:
            db.execute('''
                INSERT INTO Parts (
                    name_part, SAP_code, Drawing_number,
                    Material_id, Machine_id,
                    diameter, length, width, height, weight_g,
                    annual_volume_pcs, batch_size_pcs,
                    HT_technology, HT_temperature, Tempering_temperature,
                    HT_time, Tempering_time,
                    Surface_Hardness_min, Surface_Hardness_max, Surface_Hardness_Unit,
                    Core_Hardness_min, Core_Hardness_max, Core_Hardness_Unit,
                    CHD_min, CHD_max, EHT_min, EHT_max,
                    CLT_min, CLT_max,
                    NHD_min, NHD_max, Porosity_max, Soft_Points,
                    HT_Specifications, Note,
                    drawing_path, calculation_path
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (name_part, s('SAP_code'), s('Drawing_number'),
                  n('Material_id'), n('Machine_id'),
                  n('diameter'), n('length'), n('width'), n('height'), n('weight_g'),
                  n('annual_volume_pcs'), n('batch_size_pcs'),
                  s('HT_technology'), n('HT_temperature'), n('Tempering_temperature'),
                  n('HT_time'), n('Tempering_time'),
                  n('Surface_Hardness_min'), n('Surface_Hardness_max'), s('Surface_Hardness_Unit') or 'HRC',
                  n('Core_Hardness_min'), n('Core_Hardness_max'), s('Core_Hardness_Unit') or 'HRC',
                  n('CHD_min'), n('CHD_max'), n('EHT_min'), n('EHT_max'),
                  n('CLT_min'), n('CLT_max'),
                  n('NHD_min'), n('NHD_max'), n('Porosity_max'), s('Soft_Points'),
                  s('HT_Specifications'), s('Note'),
                  drawing, calculation))
        db.commit()
        db.close()
        return redirect(url_for('Parts'))

    part = db.execute('SELECT * FROM Parts WHERE id=?', (id,)).fetchone() if id else None
    db.close()
    return render_template('part_form.html', materials=materials, machines=machines,
                           part=part, error=None, id=id)


@app.route('/delete/<int:id>', methods=['POST'])
def delete_part(id):
    db = get_db()
    db.execute('DELETE FROM Parts WHERE id=?', (id,))
    db.commit()
    db.close()
    return redirect(url_for('Parts'))


# ── MATERIALS ─────────────────────────────────────────────────────────────────

@app.route('/Materials')
def materials():
    db = get_db()
    mats = db.execute('SELECT * FROM Materials ORDER BY name').fetchall()
    qty = {r['mid']: r['cnt'] for r in db.execute(
        'SELECT Material_id AS mid, COUNT(*) AS cnt FROM Parts WHERE Material_id IS NOT NULL GROUP BY Material_id'
    ).fetchall()}
    db.close()
    return render_template('materials.html', materials=mats, quantity=qty)


@app.route('/api/materials/search')
def materials_search():
    q = request.args.get('q', '')
    db = get_db()
    rows = db.execute(
        'SELECT id, name FROM Materials WHERE name LIKE ? ORDER BY name LIMIT 15',
        (f'%{q}%',)
    ).fetchall()
    db.close()
    return jsonify([{'id': r['id'], 'name': r['name']} for r in rows])


@app.route('/materials/add', methods=['GET', 'POST'])
@app.route('/materials/change/<int:id>', methods=['GET', 'POST'])
def material_form(id=None):
    db = get_db()
    if request.method == 'POST':
        f = request.form
        def g(k): return f.get(k, '').strip() or None
        def n(k): return f.get(k) or None

        new_pdf_files = request.files.getlist('pdf_files')
        new_paths = save_files(new_pdf_files, 'materials')

        if id:
            existing = db.execute('SELECT pdf_path, pdf_paths FROM Materials WHERE id=?', (id,)).fetchone()
            if existing:
                existing_paths = json.loads(existing['pdf_paths'] or '[]') if existing['pdf_paths'] else []
                # migrate old single pdf_path
                if existing['pdf_path'] and existing['pdf_path'] not in existing_paths:
                    existing_paths.append(existing['pdf_path'])
            else:
                existing_paths = []
            combined = existing_paths + new_paths
            pdf_paths_json = json.dumps(combined)

            db.execute('''
                UPDATE Materials SET
                    name=?, norm=?, type=?,
                    C_min=?, C_max=?, Si_min=?, Si_max=?,
                    Mn_min=?, Mn_max=?, P_min=?, P_max=?,
                    S_min=?, S_max=?, Cr_min=?, Cr_max=?,
                    Ni_min=?, Ni_max=?, Mo_min=?, Mo_max=?,
                    V_min=?, V_max=?, Pb_min=?, Pb_max=?,
                    Hardening_Temp_Oil_min=?, Hardening_Temp_Oil_max=?,
                    Hardening_Temp_Water_min=?, Hardening_Temp_Water_max=?,
                    Tempering_Temp_min=?, Tempering_Temp_max=?,
                    Temp_Cementace_min=?, Temp_Cementace_max=?,
                    Temp_Nitrocementace_min=?, Temp_Nitrocementace_max=?,
                    Temp_Nitridace_min=?, Temp_Nitridace_max=?,
                    Temp_Karbonitridace_min=?, Temp_Karbonitridace_max=?,
                    Hardness_min=?, Hardness_max=?, Hardness_Unit=?,
                    Note=?, pdf_paths=?
                WHERE id=?
            ''', (g('name'), g('norm'), g('type'),
                  n('C_min'), n('C_max'), n('Si_min'), n('Si_max'),
                  n('Mn_min'), n('Mn_max'), n('P_min'), n('P_max'),
                  n('S_min'), n('S_max'), n('Cr_min'), n('Cr_max'),
                  n('Ni_min'), n('Ni_max'), n('Mo_min'), n('Mo_max'),
                  n('V_min'), n('V_max'), n('Pb_min'), n('Pb_max'),
                  n('Hardening_Temp_Oil_min'), n('Hardening_Temp_Oil_max'),
                  n('Hardening_Temp_Water_min'), n('Hardening_Temp_Water_max'),
                  n('Tempering_Temp_min'), n('Tempering_Temp_max'),
                  n('Temp_Cementace_min'), n('Temp_Cementace_max'),
                  n('Temp_Nitrocementace_min'), n('Temp_Nitrocementace_max'),
                  n('Temp_Nitridace_min'), n('Temp_Nitridace_max'),
                  n('Temp_Karbonitridace_min'), n('Temp_Karbonitridace_max'),
                  n('Hardness_min'), n('Hardness_max'), g('Hardness_Unit') or 'HRC',
                  g('Note'), pdf_paths_json, id))
        else:
            pdf_paths_json = json.dumps(new_paths)
            db.execute('''
                INSERT INTO Materials (
                    name, norm, type,
                    C_min, C_max, Si_min, Si_max,
                    Mn_min, Mn_max, P_min, P_max,
                    S_min, S_max, Cr_min, Cr_max,
                    Ni_min, Ni_max, Mo_min, Mo_max,
                    V_min, V_max, Pb_min, Pb_max,
                    Hardening_Temp_Oil_min, Hardening_Temp_Oil_max,
                    Hardening_Temp_Water_min, Hardening_Temp_Water_max,
                    Tempering_Temp_min, Tempering_Temp_max,
                    Temp_Cementace_min, Temp_Cementace_max,
                    Temp_Nitrocementace_min, Temp_Nitrocementace_max,
                    Temp_Nitridace_min, Temp_Nitridace_max,
                    Temp_Karbonitridace_min, Temp_Karbonitridace_max,
                    Hardness_min, Hardness_max, Hardness_Unit,
                    Note, pdf_paths
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (g('name'), g('norm'), g('type'),
                  n('C_min'), n('C_max'), n('Si_min'), n('Si_max'),
                  n('Mn_min'), n('Mn_max'), n('P_min'), n('P_max'),
                  n('S_min'), n('S_max'), n('Cr_min'), n('Cr_max'),
                  n('Ni_min'), n('Ni_max'), n('Mo_min'), n('Mo_max'),
                  n('V_min'), n('V_max'), n('Pb_min'), n('Pb_max'),
                  n('Hardening_Temp_Oil_min'), n('Hardening_Temp_Oil_max'),
                  n('Hardening_Temp_Water_min'), n('Hardening_Temp_Water_max'),
                  n('Tempering_Temp_min'), n('Tempering_Temp_max'),
                  n('Temp_Cementace_min'), n('Temp_Cementace_max'),
                  n('Temp_Nitrocementace_min'), n('Temp_Nitrocementace_max'),
                  n('Temp_Nitridace_min'), n('Temp_Nitridace_max'),
                  n('Temp_Karbonitridace_min'), n('Temp_Karbonitridace_max'),
                  n('Hardness_min'), n('Hardness_max'), g('Hardness_Unit') or 'HRC',
                  g('Note'), pdf_paths_json))
        db.commit()
        db.close()
        return redirect(url_for('materials'))

    material = db.execute('SELECT * FROM Materials WHERE id=?', (id,)).fetchone() if id else None
    # Build list of pdf paths for template
    mat_pdfs = []
    if material:
        if material['pdf_paths']:
            mat_pdfs = json.loads(material['pdf_paths'])
        elif material['pdf_path']:
            mat_pdfs = [material['pdf_path']]
    db.close()
    return render_template('material_form.html', material=material, mat_pdfs=mat_pdfs, id=id)


@app.route('/materials/delete_pdf', methods=['POST'])
def delete_material_pdf():
    mat_id = request.form.get('mat_id')
    path = request.form.get('path')
    db = get_db()
    existing = db.execute('SELECT pdf_paths FROM Materials WHERE id=?', (mat_id,)).fetchone()
    if existing and existing['pdf_paths']:
        paths = json.loads(existing['pdf_paths'])
        paths = [p for p in paths if p != path]
        db.execute('UPDATE Materials SET pdf_paths=? WHERE id=?', (json.dumps(paths), mat_id))
        db.commit()
    db.close()
    return redirect(url_for('material_form', id=mat_id))


@app.route('/materials/delete/<int:id>', methods=['POST'])
def delete_material(id):
    db = get_db()
    db.execute('DELETE FROM Materials WHERE id=?', (id,))
    db.commit()
    db.close()
    return redirect(url_for('materials'))


# ── MACHINES ──────────────────────────────────────────────────────────────────

@app.route('/machines')
def machines():
    db = get_db()
    machs = db.execute('SELECT * FROM Machines ORDER BY name').fetchall()
    qty = {r['mid']: r['cnt'] for r in db.execute(
        'SELECT Machine_id AS mid, COUNT(*) AS cnt FROM Parts WHERE Machine_id IS NOT NULL GROUP BY Machine_id'
    ).fetchall()}
    db.close()
    return render_template('machines.html', machines=machs, quantity=qty)


@app.route('/machines/add', methods=['GET', 'POST'])
@app.route('/machines/change/<int:id>', methods=['GET', 'POST'])
def machine_form(id=None):
    db = get_db()
    if request.method == 'POST':
        f = request.form

        # Multiple technologies stored as JSON
        techs = f.getlist('technology')
        technology_json = json.dumps(techs) if techs else None

        # Multiple files
        new_manual_files = request.files.getlist('manual_files')
        new_paths = save_files(new_manual_files, 'machines')

        if id:
            existing = db.execute('SELECT manual_path, manual_paths FROM Machines WHERE id=?', (id,)).fetchone()
            if existing:
                existing_paths = json.loads(existing['manual_paths'] or '[]') if existing['manual_paths'] else []
                if existing['manual_path'] and existing['manual_path'] not in existing_paths:
                    existing_paths.append(existing['manual_path'])
            else:
                existing_paths = []
            combined = existing_paths + new_paths
            manual_paths_json = json.dumps(combined)

            db.execute('''
                UPDATE Machines SET
                    name=?, type=?, Temperature_max=?, technology=?, Max_Load=?, aktivni=?, manual_paths=?
                WHERE id=?
            ''', (f.get('name'), f.get('type') or None,
                  f.get('Temperature_max') or None, technology_json,
                  f.get('Max_Load') or None, 1 if f.get('aktivni') else 0,
                  manual_paths_json, id))
        else:
            manual_paths_json = json.dumps(new_paths)
            db.execute('''
                INSERT INTO Machines (name, type, Temperature_max, technology, Max_Load, manual_paths)
                VALUES (?,?,?,?,?,?)
            ''', (f.get('name'), f.get('type') or None,
                  f.get('Temperature_max') or None, technology_json,
                  f.get('Max_Load') or None, manual_paths_json))
        db.commit()
        db.close()
        return redirect(url_for('machines'))

    machine = db.execute('SELECT * FROM Machines WHERE id=?', (id,)).fetchone() if id else None
    # Build lists for template
    mach_techs = []
    mach_files = []
    if machine:
        if machine['technology']:
            try:
                mach_techs = json.loads(machine['technology'])
            except Exception:
                mach_techs = [machine['technology']] if machine['technology'] else []
        if machine['manual_paths']:
            mach_files = json.loads(machine['manual_paths'])
        elif machine['manual_path']:
            mach_files = [machine['manual_path']]
    db.close()
    return render_template('machine_form.html', machine=machine, mach_techs=mach_techs,
                           mach_files=mach_files, id=id)


@app.route('/machines/delete_file', methods=['POST'])
def delete_machine_file():
    mach_id = request.form.get('mach_id')
    path = request.form.get('path')
    db = get_db()
    existing = db.execute('SELECT manual_paths FROM Machines WHERE id=?', (mach_id,)).fetchone()
    if existing and existing['manual_paths']:
        paths = json.loads(existing['manual_paths'])
        paths = [p for p in paths if p != path]
        db.execute('UPDATE Machines SET manual_paths=? WHERE id=?', (json.dumps(paths), mach_id))
        db.commit()
    db.close()
    return redirect(url_for('machine_form', id=mach_id))


@app.route('/machines/delete/<int:id>', methods=['POST'])
def delete_machine(id):
    db = get_db()
    db.execute('DELETE FROM Machines WHERE id=?', (id,))
    db.commit()
    db.close()
    return redirect(url_for('machines'))


if __name__ == '__main__':
    init_db()
    print()
    print('  TZ Databaze spustena!')
    print('  Otevrete http://localhost:5000')
    print()
    app.run(debug=True, host='0.0.0.0', port=5000)
