from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ACTS_FOLDER'] = 'acts/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ACTS_FOLDER'], exist_ok=True)

DB_PATH = 'database.sqlite'

# ========== EMAIL НАСТРОЙКИ ==========
EMAIL_HOST = 'smtp.gmail.com'          
EMAIL_PORT = 587
EMAIL_USER = 'vika565455565455@gmail.com'     
EMAIL_PASSWORD = 'dovl jibb qxsd nufv'          
EMAIL_TO = 'vika565455565455@gmail.com'    
# =====================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def upgrade_db():
    """Автоматически добавляет новые колонки в существующую базу данных"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем, есть ли колонка 'street' в таблице 'flats'
    cursor.execute("PRAGMA table_info(flats)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'street' not in columns:
        print("🚀 Обновляю структуру базы данных...")
        try:
            cursor.execute('ALTER TABLE flats ADD COLUMN street TEXT')
            cursor.execute('ALTER TABLE flats ADD COLUMN house TEXT')
            conn.commit()
            print("✅ База данных успешно обновлена! Добавлены колонки street и house")
        except Exception as e:
            print(f"❌ Ошибка при обновлении базы данных: {e}")
    
    # Проверяем, есть ли данные в таблице flats (если нет — создаём тестовые квартиры)
    cursor.execute('SELECT COUNT(*) FROM flats')
    count = cursor.fetchone()[0]
    if count == 0:
        print("🚀 Добавляю тестовые квартиры...")
        test_flats = [
            ('1', 'ул. Ленина', '12', 'Корпус 1', 1, 1, 'in_progress'),
            ('2', 'ул. Ленина', '12', 'Корпус 1', 1, 1, 'in_progress'),
            ('3', 'ул. Ленина', '12', 'Корпус 1', 1, 2, 'in_progress'),
            ('5', 'ул. Гагарина', '5', 'Корпус 2', 1, 1, 'in_progress'),
            ('10', 'ул. Гагарина', '5', 'Корпус 2', 2, 3, 'in_progress'),
        ]
        cursor.executemany('''
            INSERT INTO flats (number, street, house, building, entrance, floor, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', test_flats)
        conn.commit()
        print("✅ Добавлено 5 тестовых квартир")
    
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def send_email_notification(flat_number, room, location_detail, defect_code, defect_description):
    """Отправляет email подрядчику о новом дефекте"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_TO
        msg['Subject'] = f'🔧 Новая заявка на исправление - Квартира {flat_number}'
        
        body = f"""
Здравствуйте!

Поступила новая заявка на исправление дефекта.

📋 ДЕТАЛИ ЗАЯВКИ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 Квартира: №{flat_number}
📍 Помещение: {room if room else 'не указано'}
📌 Точное место: {location_detail if location_detail else 'не указано'}

📄 Нормативный документ: {defect_code}
📝 Описание дефекта: {defect_description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Для просмотра всех заявок и управления перейдите по ссылке:
👉 http://127.0.0.1:5000/defects

{chr(10)}Если вы работаете с телефона в той же сети, используйте IP-адрес компьютера.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
С уважением,
Система контроля качества СЗ «Андор»
"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email отправлен на {EMAIL_TO}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
        return False

@app.route('/')
def index():
    conn = get_db()
    flats = conn.execute('''
        SELECT f.*, COUNT(d.id) as defect_count,
               SUM(CASE WHEN d.status = 'open' THEN 1 ELSE 0 END) as open_count
        FROM flats f
        LEFT JOIN defects d ON f.id = d.flat_id
        GROUP BY f.id
        ORDER BY f.street, f.house, f.building, f.floor, f.number
    ''').fetchall()
    conn.close()
    return render_template('index.html', flats=flats)

@app.route('/flat/<int:flat_id>')
def flat(flat_id):
    conn = get_db()
    flat = conn.execute('SELECT * FROM flats WHERE id = ?', (flat_id,)).fetchone()
    defects = conn.execute('''
        SELECT d.*, s.code, s.category, s.description, s.severity
        FROM defects d
        JOIN snip_defects s ON d.snip_defect_id = s.id
        WHERE d.flat_id = ?
        ORDER BY d.created_at DESC
    ''', (flat_id,)).fetchall()
    snip_defects = conn.execute('SELECT * FROM snip_defects ORDER BY category, code').fetchall()
    conn.close()
    return render_template('flat.html', flat=flat, defects=defects, snip_defects=snip_defects)

@app.route('/add_defect', methods=['POST'])
def add_defect():
    flat_id = request.form['flat_id']
    snip_defect_id = request.form['snip_defect_id']
    room = request.form.get('room', '')
    location_detail = request.form.get('location_detail', '')
    comment = request.form.get('comment', '')
    
    photo_path = None
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo and allowed_file(photo.filename):
            filename = f"{uuid.uuid4().hex}.jpg"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
    
    conn = get_db()
    conn.execute('''
        INSERT INTO defects (flat_id, snip_defect_id, room, location_detail, comment, photo_path, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
    ''', (flat_id, snip_defect_id, room, location_detail, comment, photo_path, datetime.now()))
    conn.commit()
    
    # Получаем информацию о дефекте для email
    snip_info = conn.execute('SELECT code, description FROM snip_defects WHERE id = ?', (snip_defect_id,)).fetchone()
    flat_info = conn.execute('SELECT number FROM flats WHERE id = ?', (flat_id,)).fetchone()
    conn.close()
    
    # Отправляем email уведомление
    if snip_info and flat_info:
        send_email_notification(
            flat_number=flat_info['number'],
            room=room,
            location_detail=location_detail,
            defect_code=snip_info['code'],
            defect_description=snip_info['description']
        )
    
    return redirect(url_for('flat', flat_id=flat_id))

@app.route('/defects')
def defects():
    conn = get_db()
    all_defects = conn.execute('''
        SELECT d.*, f.number as flat_number, f.street, f.house, f.building, 
               s.code, s.category, s.description, s.severity
        FROM defects d
        JOIN flats f ON d.flat_id = f.id
        JOIN snip_defects s ON d.snip_defect_id = s.id
        ORDER BY 
            CASE d.status 
                WHEN 'open' THEN 1 
                WHEN 'fixed' THEN 2 
                WHEN 'closed' THEN 3 
            END,
            d.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('defects.html', defects=all_defects)

@app.route('/defect/<int:defect_id>/fix')
def fix_defect(defect_id):
    conn = get_db()
    conn.execute('UPDATE defects SET status = "fixed", fixed_at = ? WHERE id = ?', (datetime.now(), defect_id))
    conn.commit()
    conn.close()
    return redirect(url_for('defects'))

@app.route('/defect/<int:defect_id>/close')
def close_defect(defect_id):
    conn = get_db()
    conn.execute('UPDATE defects SET status = "closed" WHERE id = ?', (defect_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('defects'))

@app.route('/defect/<int:defect_id>/reopen')
def reopen_defect(defect_id):
    conn = get_db()
    conn.execute('UPDATE defects SET status = "open" WHERE id = ?', (defect_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('defects'))

@app.route('/defect/<int:defect_id>/delete')
def delete_defect(defect_id):
    conn = get_db()
    
    defect = conn.execute('SELECT photo_path FROM defects WHERE id = ?', (defect_id,)).fetchone()
    
    if defect and defect['photo_path']:
        try:
            if os.path.exists(defect['photo_path']):
                os.remove(defect['photo_path'])
        except:
            pass
    
    conn.execute('DELETE FROM defects WHERE id = ?', (defect_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('defects'))

@app.route('/generate_act/<int:defect_id>')
def generate_act(defect_id):
    import os
    from datetime import datetime
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Регистрируем шрифт из папки проекта
    font_path = os.path.join(os.path.dirname(__file__), 'ofont.ru_Arial.ttf')
    try:
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        font_name = 'Arial'
    except Exception as e:
        print(f"Font error: {e}")
        font_name = 'Helvetica'

    conn = get_db()
    defect = conn.execute('''
        SELECT d.*, f.number as flat_number, f.street, f.house, f.building, f.entrance, f.floor,
               s.code, s.category, s.description, s.severity
        FROM defects d
        JOIN flats f ON d.flat_id = f.id
        JOIN snip_defects s ON d.snip_defect_id = s.id
        WHERE d.id = ?
    ''', (defect_id,)).fetchone()
    conn.close()

    if not defect:
        return "Дефект не найден", 404

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"act_{defect_id}_{timestamp}.pdf"
    filepath = os.path.join(app.config['ACTS_FOLDER'], filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    c.setFont(font_name, 16)
    c.drawString(50, height - 50, "АКТ ОСМОТРА КВАРТИРЫ")

    c.setFont(font_name, 12)
    c.drawString(50, height - 80, "ООО СЗ «Андор»")

    c.setFont(font_name, 11)
    c.drawString(50, height - 105, f"Квартира №{defect['flat_number']}")
    c.drawString(50, height - 125, f"Адрес: {defect['street']}, д. {defect['house']}, {defect['building']}")
    c.drawString(50, height - 145, f"Подъезд: {defect['entrance']}, Этаж: {defect['floor']}")
    c.drawString(50, height - 165, f"Дата осмотра: {defect['created_at']}")

    c.line(50, height - 185, width - 50, height - 185)

    c.setFont(font_name, 14)
    c.drawString(50, height - 215, "ВЫЯВЛЕННЫЙ ДЕФЕКТ")

    c.setFont(font_name, 11)
    c.drawString(50, height - 240, f"Нормативный документ: {defect['code']}")
    c.drawString(50, height - 260, f"Категория: {defect['category']}")

    description = defect['description']
    if len(description) > 70:
        c.drawString(50, height - 280, f"Описание: {description[:70]}...")
    else:
        c.drawString(50, height - 280, f"Описание: {description}")

    y_pos = 300
    if defect['room']:
        location_text = f"Место: {defect['room']}"
        if defect['location_detail']:
            location_text += f" ({defect['location_detail']})"
        c.drawString(50, height - y_pos, location_text)
        y_pos += 20

    if defect['comment']:
        c.drawString(50, height - y_pos, f"Комментарий: {defect['comment'][:60]}")
        y_pos += 20

    severity_text = "КРИТИЧНЫЙ" if defect['severity'] == 'critical' else "КОСМЕТИЧЕСКИЙ"
    if defect['severity'] == 'critical':
        c.setFillColorRGB(0.8, 0, 0)
    c.drawString(50, height - y_pos, f"Критичность: {severity_text}")
    c.setFillColorRGB(0, 0, 0)
    y_pos += 25

    status_text = {
        'open': 'НЕ ИСПРАВЛЕН',
        'fixed': 'ИСПРАВЛЕН (ожидает проверки)',
        'closed': 'ЗАКРЫТ'
    }.get(defect['status'], defect['status'])
    c.drawString(50, height - y_pos, f"Статус: {status_text}")

    y_sign = 400
    c.line(50, height - y_sign, 200, height - y_sign)
    c.drawString(60, height - y_sign - 20, "Прораб")

    c.line(width - 200, height - y_sign, width - 50, height - y_sign)
    c.drawString(width - 190, height - y_sign - 20, "Представитель подрядчика")

    y_sign2 = y_sign + 60
    c.line(50, height - y_sign2, width - 50, height - y_sign2)
    c.drawString(50, height - y_sign2 - 20, "Покупатель (дольщик)")

    c.setFont(font_name, 9)
    c.drawString(50, height - 520, f"Акт сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    c.save()

    return send_file(filepath, as_attachment=True)

@app.route('/report')
def report():
    conn = get_db()
    
    stats = conn.execute('''
        SELECT s.category, COUNT(d.id) as count,
               SUM(CASE WHEN d.status != 'closed' THEN 1 ELSE 0 END) as open_count
        FROM defects d
        JOIN snip_defects s ON d.snip_defect_id = s.id
        GROUP BY s.category
    ''').fetchall()
    
    top_defects = conn.execute('''
        SELECT s.code, s.description, COUNT(d.id) as count
        FROM defects d
        JOIN snip_defects s ON d.snip_defect_id = s.id
        GROUP BY d.snip_defect_id
        ORDER BY count DESC
        LIMIT 5
    ''').fetchall()
    
    total = conn.execute('SELECT COUNT(id) FROM defects').fetchone()[0]
    closed = conn.execute('SELECT COUNT(id) FROM defects WHERE status = "closed"').fetchone()[0]
    
    conn.close()
    
    return render_template('report.html', 
                          stats=stats, 
                          top_defects=top_defects,
                          total=total, 
                          closed=closed)

# ========== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ПРИ ЗАПУСКЕ ==========
# Вызываем обновление структуры БД перед запуском сервера
upgrade_db()

if __name__ == '__main__':
    print("\n🚀 Запуск сервера...")
    print("📱 Открой в браузере: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)