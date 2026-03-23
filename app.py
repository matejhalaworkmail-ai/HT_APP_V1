# app.py - main file for HT database
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

# Vytvroř Flask aplikaci
app = Flask (__name__)
# cestka k databázi
# _file_ - cesta k aktuálnímu souboru, dirname - získá adresář, join - spojí cesty
# dirname - získá adresář app.py 
# join - spojí adresář s názvem databáze
DB = os.path.join(os.path.dirname(__file__), 'tz-databaze.db')


######## BOLK 3 - Funkce pro databázi ########

def get_db():
    """Funkce pro získání připojení k databázi."""
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row  # Umožní přístup k sloupcům podle jména
    return db

def init_db():
    # vytvoření tabulky, pokud neexistuje
    # toto se spustí pouze při prvním spuštění aplikace
    db = get_db()
    db.executescript('''
         CREATE TABLE IF NOT EXISTS Materials (id INTEGER PRIMARY KEY AUTOINCREMENT , 
           name TEXT NOT NULL,
           norm TEXT, 
           type TEXT,
           C_min    REAL, C_max     REAL,
           Si_min   REAL, Si_max    REAL,
           Mn_min   REAL, Mn_max    REAL,
           P_min    REAL, P_max     REAL,
           S_min    REAL, S_max     REAL,
           Cr_min   REAL, Cr_max    REAL,
           Ni_min   REAL, Ni_max    REAL,
           Mo_min   REAL, Mo_max    REAL,   
           V_min    REAL, V_max     REAL,
           Pb_min   REAL, Pb_max    REAL,
           Hardening_Temp_Oil_min   INTEGER,
           Hardening_Temp_Oil_max   INTEGER,
           Hardening_Temp_Water_min INTEGER,
           Hardening_Temp_Water_max INTEGER,
           Tempering_Temp_min       INTEGER, 
           Tempering_Temp_max       INTEGER,
           Hardness_min             INTEGER, 
           Hardness_max             INTEGER,
           Hardness_Unit text default 'HRC',
           Note  TEXT);
        
        CREATE TABLE IF NOT EXISTS Machines ( id INTEGER PRIMARY KEY AUTOINCREMENT ,
           name TEXT NOT NULL,
           type TEXT,
           Temperature_max INTEGER,
           aktivni integer DEFAULT 1,
           technology TEXT,
           Max_Load REAL);
        
        CREATE TABLE IF NOT EXISTS Parts ( 
          
          -- IDENTIFIKACE dílů --
          
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            name_part               TEXT NOT NULL,
            SAP_code                TEXT,
            Drawing_number          TEXT,

            -- Connecting to other tables --

            Material_id              INTEGER references Materials(id),
            Machine_id               INTEGER references Machines(id),

          -- Dimensions --
            diameter                REAL,
            length                  REAL,
            width                   REAL,
            height                  REAL,

          -- Production --

            annual_volume_pcs       INTEGER,
            batch_size_pcs          INTEGER,

          -- Technology HT --

            HT_technology            TEXT,

          -- Process parameters --

            HT_temperature          INTEGER,
            Tempering_temperature   INTEGER,
            HT_time                 INTEGER,
            Tempering_time          INTEGER,

          -- HT Specificiations --
          
            Surface_Hardness_min             INTEGER,
            Surface_Hardness_max             INTEGER,
            Surface_Hardness_Unit text default 'HRC',
            Core_Hardness_min                INTEGER,
            Core_Hardness_max                INTEGER,
            Core_Hardness_Unit text default 'HRC',

          -- Carburizing / Carbonitriding specifications--
          
            CHD_min                         REAL,
            CHD_max                         REAL,

         -- Nitrding / Nitrocarburizing specifications --

            CLT_min                         REAL,
            CLT_max                         REAL,
            NHD_min                         REAL,
            NHD_max                         REAL,
            Porosity_max                    REAL,

          -- Specifications and notes --
          
            HT_Specifications TEXT,
            Note TEXT,

            vytvoreno TeXT DEFAULT (datetime('now')),
            upraveno TEXT DEFAULT (datetime('now')));
    ''')  
    db.commit()
    db.close()

@app.route('/')
def Parts():
    """Zobrazí seznam dílů."""
    db = get_db()
    search = request.args.get('q', '')  # Získá hledaný výraz z URL

    if search:
        # Hledej díly , které obsahují hledaný text 
        # % znamená cokoliv před a po hledaném textu
        parts = db.execute('''
        SELECT d.*, m.name AS material_name, ma.name AS machine_name FROM Parts d LEFT JOIN Materials m ON d.Material_id = m.id LEFT JOIN Machines ma ON d.Machine_id = ma.id WHERE d.name_part LIKE ?
        OR d.SAP_Code LIKE ? OR d.Drawing_number LIKE ? 
        ORDER BY d.name_part''', (f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    else:
        # bez filtru zobraz všechny díly
        parts = db .execute('''
        SELECT d.*, m.name AS material_name, ma.name AS machine_name FROM Parts d LEFT JOIN Materials m ON d.Material_id = m.id LEFT JOIN Machines ma ON d.Machine_id = ma.id ORDER BY d.name_part''').fetchall()
    
    quantity = db.execute('SELECT COUNT(*) FROM Parts').fetchone()[0]
    db.close()
    return render_template('parts.html', parts=parts, search=search, quantity=quantity)

@app.route('/Parts/<int:id>')
def parts_detail(id):
    """Zobrazí detail dílu."""
    db = get_db()
    parts = db.execute('''
        SELECT d.*,
               m.name AS material_name,
               m.norm AS material_norm,
               m.type AS material_type,
               m.C_min, m.C_max,
               m.Si_min, m.Si_max,
               m.Mn_min, m.Mn_max,
               m.P_min, m.P_max,
               m.S_min, m.S_max,
               m.Cr_min, m.Cr_max,
               m.Ni_min, m.Ni_max,
               m.Mo_min, m.Mo_max,
               m.V_min, m.V_max,
               m.Pb_min, m.Pb_max,
               m.Hardening_Temp_Oil_min, m.Hardening_Temp_Oil_max,
               m.Hardening_Temp_Water_min, m.Hardening_Temp_Water_max,
               m.Tempering_Temp_min, m.Tempering_Temp_max,
               ma.name AS machine_name,
               ma.type AS machine_type
               FROM Parts d
               LEFT JOIN Materials m ON d.Material_id = m.id
               LEFT JOIN Machines ma ON d.Machine_id = ma.id
               WHERE d.id = ?
               ''', (id,)).fetchone()
    db.close()
    if parts is None:
        return 'Part not found', 404
    return render_template('part_detail.html', parts=parts)

@app.route('/add', methods=['GET', 'POST'])
@app.route('/change/<int:id>', methods=['GET', 'POST'])
def parts_form (id=None):
    """Zobrazí formulář pro přidání nebo úpravu dílu."""
    db = get_db()
    materials = db.execute('SELECT id, name FROM Materials ORDER BY name').fetchall()
    machines = db.execute('SELECT id, name FROM Machines ORDER BY name').fetchall()
    if request.method == 'POST':
        name_part = request.form.get('name_part','').strip()
        SAP_code = request.form.get('SAP_code','').strip()
        Drawing_number = request.form.get('Drawing_number','').strip()
        Material_id = request.form.get('Material_id') or None
        Machine_id = request.form.get('Machine_id') or None
        diameter = request.form.get('diameter') or None
        length = request.form.get('length') or None
        width = request.form.get('width') or None
        height = request.form.get('height') or None
        annual_volume_pcs = request.form.get('annual_volume_pcs') or None
        batch_size_pcs = request.form.get('batch_size_pcs') or None
        HT_technology = request.form.get('HT_technology','').strip()
        HT_temperature = request.form.get('HT_temperature') or None
        Tempering_temperature = request.form.get('Tempering_temperature') or None
        HT_time = request.form.get('HT_time') or None
        Tempering_time = request.form.get('Tempering_time') or None
        Surface_Hardness_min = request.form.get('Surface_Hardness_min') or None
        Surface_Hardness_max = request.form.get('Surface_Hardness_max') or None
        Surface_Hardness_Unit = request.form.get('Surface_Hardness_Unit','HRC').strip()
        Core_Hardness_min = request.form.get('Core_Hardness_min') or None
        Core_Hardness_max = request.form.get('Core_Hardness_max') or None
        Core_Hardness_Unit = request.form.get('Core_Hardness_Unit','HRC').strip()
        CHD_min = request.form.get('CHD_min') or None
        CHD_max = request.form.get('CHD_max') or None
        CLT_min = request.form.get('CLT_min') or None
        CLT_max = request.form.get('CLT_max') or None
        NHD_min = request.form.get('NHD_min') or None
        NHD_max = request.form.get('NHD_max') or None
        Porosity_max = request.form.get('Porosity_max') or None
        HT_Specifications = request.form.get('HT_Specifications','').strip()
        Note = request.form.get('Note','').strip()

        if not name_part:
            return render_template('part_form.html', materials=materials, machines=machines, error='Name is required', part=request.form)

        if id:  # Update existing part
            db.execute('''
                UPDATE Parts SET 
                    name_part = ?, SAP_code = ?, Drawing_number = ?, Material_id = ?, Machine_id = ?,
                    diameter = ?, length = ?, width = ?, height = ?,
                    annual_volume_pcs = ?, batch_size_pcs = ?, HT_technology = ?,
                    HT_temperature = ?, Tempering_temperature = ?, HT_time = ?, Tempering_time = ?,
                    Surface_Hardness_min = ?, Surface_Hardness_max = ?, Surface_Hardness_Unit = ?,
                    Core_Hardness_min = ?, Core_Hardness_max = ?, Core_Hardness_Unit = ?,
                    CHD_min = ?, CHD_max = ?, CLT_min = ?, CLT_max = ?,
                    NHD_min = ?, NHD_max = ?, Porosity_max = ?,
                    HT_Specifications = ?, Note = ?,
                    upraveno = datetime('now')
                WHERE id = ?
            ''', (name_part, SAP_code, Drawing_number, Material_id, Machine_id,
                  diameter, length, width, height,
                  annual_volume_pcs, batch_size_pcs, HT_technology,
                  HT_temperature, Tempering_temperature, HT_time, Tempering_time,
                  Surface_Hardness_min, Surface_Hardness_max, Surface_Hardness_Unit,
                  Core_Hardness_min, Core_Hardness_max, Core_Hardness_Unit,
                  CHD_min, CHD_max, CLT_min, CLT_max,
                  NHD_min, NHD_max, Porosity_max,
                  HT_Specifications, Note, id))
        else:  # Insert new part
            db.execute('''
                INSERT INTO Parts (
                    name_part, SAP_code, Drawing_number, Material_id, Machine_id,
                    diameter, length, width, height,
                    annual_volume_pcs, batch_size_pcs, HT_technology,
                    HT_temperature, Tempering_temperature, HT_time, Tempering_time,
                    Surface_Hardness_min, Surface_Hardness_max, Surface_Hardness_Unit,
                    Core_Hardness_min, Core_Hardness_max, Core_Hardness_Unit,
                    CHD_min, CHD_max, CLT_min, CLT_max,
                    NHD_min, NHD_max, Porosity_max,
                    HT_Specifications, Note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name_part, SAP_code, Drawing_number, Material_id, Machine_id,
                  diameter, length, width, height,
                  annual_volume_pcs, batch_size_pcs, HT_technology,
                  HT_temperature, Tempering_temperature, HT_time, Tempering_time,
                  Surface_Hardness_min, Surface_Hardness_max, Surface_Hardness_Unit,
                  Core_Hardness_min, Core_Hardness_max, Core_Hardness_Unit,
                  CHD_min, CHD_max, CLT_min, CLT_max,
                  NHD_min, NHD_max, Porosity_max,
                  HT_Specifications, Note))

        db.commit()
        db.close()
        return redirect(url_for('Parts'))

    parts = db.execute('SELECT * FROM Parts WHERE id = ?', (id,)) .fetchone() if id else None
    db.close()
    return render_template('part_form.html',
    materials=materials, 
    machines=machines, 
    part=parts,
    error=None)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_part(id):
    """Smaže díl."""
    db = get_db()
    db.execute('DELETE FROM Parts WHERE id = ?', (id,))
    db.commit()
    db.close()
    return redirect(url_for('Parts'))

@app.route('/Materials')
def materials():
    db = get_db()
    materials = db.execute('SELECT * FROM Materials ORDER BY name').fetchall()
    quantity = {r['material_id']: r ['quantity'] for r in db.execute('SELECT material_id, COUNT(*) as quantity FROM Parts GROUP BY material_id').fetchall()}
    db.close()
    return render_template('materials.html', materials=materials, quantity=quantity)

@app.route('/materials/add', methods=['GET', 'POST'])
@app.route('/materials/change/<int:id>', methods=['GET', 'POST'])
def material_form(id=None):
    db = get_db()
    if request.method == 'POST':
        f = request.form
        def g(k): return f .get(k,'').strip() or None
        def n(k): return f. get(k) or None
        if id:
            db.execute('''
            UPDATE Materials SET 
                name = ?, norm = ?, type = ?,
                C_min = ?, C_max = ?,
                Si_min = ?, Si_max = ?,
                Mn_min = ?, Mn_max = ?,
                P_min = ?, P_max = ?,
                S_min = ?, S_max = ?,
                Cr_min = ?, Cr_max = ?,
                Ni_min = ?, Ni_max = ?,
                Mo_min = ?, Mo_max = ?,
                V_min = ?, V_max = ?,
                Pb_min = ?, Pb_max = ?,
                Hardening_Temp_Oil_min = ?, Hardening_Temp_Oil_max = ?,
                Hardening_Temp_Water_min = ?, Hardening_Temp_Water_max = ?,
                Tempering_Temp_min = ?, Tempering_Temp_max = ?,
                Hardness_min = ?, Hardness_max = ?, Hardness_Unit = ?,
                Note = ?
                WHERE id = ?''',
                (g('name'), g('norm'), g('type'),
                 n('C_min'), n('C_max'),
                 n('Si_min'), n('Si_max'),
                 n('Mn_min'), n('Mn_max'),
                 n('P_min'), n('P_max'),
                 n('S_min'), n('S_max'),
                 n('Cr_min'), n('Cr_max'),
                 n('Ni_min'), n('Ni_max'),
                 n('Mo_min'), n('Mo_max'),
                 n('V_min'), n('V_max'),
                 n('Pb_min'), n('Pb_max'),
                 n('Hardening_Temp_Oil_min'), n('Hardening_Temp_Oil_max'),
                 n('Hardening_Temp_Water_min'), n('Hardening_Temp_Water_max'),
                 n('Tempering_Temp_min'), n('Tempering_Temp_max'),
                 n('Hardness_min'), n('Hardness_max'), g ('Hardness_Unit'),
                 g ('Note'), id))
        else:
            db.execute('''
                INSERT INTO Materials (
                    name, norm, type,
                    C_min, C_max,
                    Si_min, Si_max,
                    Mn_min, Mn_max,
                    P_min, P_max,
                    S_min, S_max,
                    Cr_min, Cr_max,
                    Ni_min, Ni_max,
                    Mo_min, Mo_max,
                    V_min, V_max,
                    Pb_min, Pb_max,
                    Hardening_Temp_Oil_min, Hardening_Temp_Oil_max,
                    Hardening_Temp_Water_min, Hardening_Temp_Water_max,
                    Tempering_Temp_min, Tempering_Temp_max,
                    Hardness_min, Hardness_max, Hardness_Unit,
                    Note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,? )''',
                (g('name'), g('norm'), g('type'),
                 n('C_min'), n('C_max'),
                 n('Si_min'), n('Si_max'),
                 n('Mn_min'), n('Mn_max'),
                 n('P_min'), n('P_max'),
                 n('S_min'), n('S_max'),
                 n('Cr_min'), n('Cr_max'),
                 n('Ni_min'), n('Ni_max'),
                 n('Mo_min'), n('Mo_max'),
                 n('V_min'), n('V_max'),
                 n('Pb_min'), n('Pb_max'),
                 n('Hardening_Temp_Oil_min'), n('Hardening_Temp_Oil_max'),
                 n('Hardening_Temp_Water_min'), n('Hardening_Temp_Water_max'),
                 n('Tempering_Temp_min'), n('Tempering_Temp_max'),
                 n('Hardness_min'), n('Hardness_max'), g ('Hardness_Unit'),
                 g ('Note')))
        db.commit()
        db.close()
        return redirect(url_for('materials'))
    material = db.execute('SELECT * FROM Materials WHERE id = ?', (id,)).fetchone() if id else None
    db.close()
    return render_template('material_form.html', material=material)

@app.route('/machines')
def machines():
    db = get_db()
    machines = db.execute('SELECT * FROM Machines ORDER BY name').fetchall()
    quantity = {r['machine_id']: r ['quantity'] for r in db.execute('SELECT machine_id, COUNT(*) as quantity FROM Parts GROUP BY machine_id').fetchall()}
    db.close()
    return render_template('machines.html', machines=machines, quantity=quantity)


@app.route('/machines/add', methods=['GET', 'POST'])
def machine_add():
    if request.method == 'POST':
        db = get_db()
        db.execute('''
            INSERT INTO Machines (name, type, Temperature_max, technology, Max_Load) VALUES (?, ?, ?, ?, ?)''',
            (request.form['name'],
             request.form['type'],
             request.form['Temperature_max'],
             request.form['technology'],
             request.form['Max_Load']))
        db.commit()
        db.close()
        return redirect(url_for('machines'))
    return render_template('machine_form.html', machine=None)

if __name__ == '__main__':
    init_db()  # Inicializace databáze při spuštění aplikace
    print()
    print('  🔥  TZ Databáze spuštěna!')
    print('  🌐  Otevřete http://localhost:5000')
    print()
    app.run(debug=True, port=5000)


