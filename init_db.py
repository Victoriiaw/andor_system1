import sqlite3
import os

DB_PATH = 'database.sqlite'

def init_db():
    # удаляем старую БД, если есть
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица квартир
    cursor.execute('''
        CREATE TABLE flats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL,
            building TEXT NOT NULL,
            entrance INTEGER,
            floor INTEGER,
            status TEXT DEFAULT 'in_progress'
        )
    ''')
    
    # Таблица СНиП дефектов (справочник)
    cursor.execute('''
        CREATE TABLE snip_defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL
        )
    ''')
    
    # Таблица недочетов
    cursor.execute('''
        CREATE TABLE defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flat_id INTEGER NOT NULL,
            snip_defect_id INTEGER NOT NULL,
            room TEXT,
            location_detail TEXT,
            comment TEXT,
            photo_path TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP,
            fixed_at TIMESTAMP,
            FOREIGN KEY (flat_id) REFERENCES flats(id),
            FOREIGN KEY (snip_defect_id) REFERENCES snip_defects(id)
        )
    ''')
    
    # Заполняем справочник СНиП (20 дефектов)
    snip_data = [
        # Стены
        ('3.04.01-87 п.3.23', 'стены', 'Отклонение поверхности от вертикали более 2 мм на 1 м высоты', 'critical'),
        ('3.04.01-87 п.3.24', 'стены', 'Неровность поверхности под правило 2 м более 2 мм', 'minor'),
        ('3.04.01-87 п.3.25', 'стены', 'Трещины, раковины, наплывы на оштукатуренной поверхности', 'critical'),
        ('3.04.01-87 п.3.28', 'стены', 'Отклонение углов от вертикали более 2 мм на 1 м', 'critical'),
        # Полы
        ('3.04.01-87 п.3.47', 'пол', 'Зазор между досками паркета более 0.5 мм', 'critical'),
        ('3.04.01-87 п.3.48', 'пол', 'Скрип половых досок при ходьбе', 'critical'),
        ('3.04.01-87 п.3.50', 'пол', 'Отклонение пола от горизонтали более 2 мм на 2 м', 'minor'),
        ('3.04.01-87 п.3.52', 'пол', 'Вздутие или отслоение линолеума', 'critical'),
        # Окна
        ('ГОСТ 30971-2012 п.5.2', 'окна', 'Щель между рамой и стеной более 5 мм', 'critical'),
        ('ГОСТ 30971-2012 п.5.4', 'окна', 'Нарушение герметизации монтажного шва', 'critical'),
        ('ГОСТ 30674-99 п.5.7', 'окна', 'Царапины или сколы на ПВХ профиле', 'minor'),
        ('ГОСТ 30674-99 п.5.9', 'окна', 'Ручка закрывается с усилием или неплотно', 'minor'),
        # Двери
        ('СП 54.13330.2016 п.6.2', 'двери', 'Щель между полотном и коробкой более 4 мм', 'minor'),
        ('СП 54.13330.2016 п.6.3', 'двери', 'Дверь закрывается самопроизвольно', 'critical'),
        ('СП 54.13330.2016 п.6.5', 'двери', 'Отсутствие или неисправность замка', 'critical'),
        # Сантехника
        ('СП 73.13330.2016 п.6.4', 'сантехника', 'Подтекание воды под смесителем', 'critical'),
        ('СП 73.13330.2016 п.6.7', 'сантехника', 'Унитаз шатается или установлен неровно', 'critical'),
        ('СП 73.13330.2016 п.6.9', 'сантехника', 'Слив воды из бачка проходит с шумом', 'minor'),
        # Электрика
        ('СП 76.13330.2016 п.4.3', 'электрика', 'Розетка не фиксируется в подрозетнике', 'critical'),
        ('СП 76.13330.2016 п.4.5', 'электрика', 'Выключатель работает с искрением', 'critical'),
        ('ПУЭ 7.1.48', 'электрика', 'Отсутствует заземление розетки', 'critical'),
    ]
    
    cursor.executemany('''
        INSERT INTO snip_defects (code, category, description, severity)
        VALUES (?, ?, ?, ?)
    ''', snip_data)
    
    # Добавляем тестовые квартиры
    test_flats = [
        ('1', 'Корпус 1', 1, 1, 'in_progress'),
        ('2', 'Корпус 1', 1, 1, 'in_progress'),
        ('3', 'Корпус 1', 1, 2, 'in_progress'),
        ('5', 'Корпус 2', 1, 1, 'in_progress'),
        ('10', 'Корпус 2', 2, 3, 'in_progress'),
    ]
    
    cursor.executemany('''
        INSERT INTO flats (number, building, entrance, floor, status)
        VALUES (?, ?, ?, ?, ?)
    ''', test_flats)
    
    conn.commit()
    conn.close()
    print("База данных успешно создана!")
    print("Добавлено 5 квартир и 21 дефект по СНиП.")
    print("Теперь можно запускать python app.py")

if __name__ == '__main__':
    init_db()