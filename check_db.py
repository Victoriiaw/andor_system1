import sqlite3

try:
    conn = sqlite3.connect('database.sqlite')
    cursor = conn.cursor()
    
    # Проверяем таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Таблицы в базе данных:")
    for table in tables:
        print(f"  - {table[0]}")
    
    if not tables:
        print("❌ Таблицы не найдены! Нужно запустить python init_db.py")
    else:
        # Проверяем количество записей
        if ('flats',) in tables:
            cursor.execute("SELECT COUNT(*) FROM flats")
            flats_count = cursor.fetchone()[0]
            print(f"\nКвартир: {flats_count}")
        
        if ('snip_defects',) in tables:
            cursor.execute("SELECT COUNT(*) FROM snip_defects")
            defects_count = cursor.fetchone()[0]
            print(f"СНиП дефектов: {defects_count}")
        
        if ('defects',) in tables:
            cursor.execute("SELECT COUNT(*) FROM defects")
            user_defects = cursor.fetchone()[0]
            print(f"Добавленных дефектов: {user_defects}")
    
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")