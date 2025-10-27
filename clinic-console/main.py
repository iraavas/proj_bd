# main.py
#import psycopg2
import psycopg
import bcrypt
import redis
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from tabulate import tabulate
import uuid
     # =============================
# === ЗАГРУЗКА КОНФИГА ===
# =============================
load_dotenv()

PG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'db': os.getenv('POSTGRES_DB', 'mydb'),
    'user': os.getenv('POSTGRES_USER', 'pguser'),
    'password': os.getenv('POSTGRES_PASSWORD', 'pgpassword')
}

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

MONGO_DB_NAME = os.getenv('MONGO_DB', 'mydb')
MONGO_URI = f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT', 27017)}/{MONGO_DB_NAME}?authSource={MONGO_DB_NAME}"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB_NAME]
documents_collection = mongo_db.documents

# =============================
# === СПРАВОЧНИКИ ИЗ REDIS ===
# =============================
def get_role_name(role_id): return r.hget(f"roles:{role_id}", "name") or "—"
def get_clinic_name(clinic_id): return r.hget(f"clinics:{clinic_id}", "name") or "—"
def get_service_name(service_id): return r.hget(f"services:{service_id}", "name") or "—"
def get_doctor_name(doctor_id): return r.hget(f"doctors:{doctor_id}", "full_name") or "—"
def get_status_name(status_id): return r.hget(f"appointment_statuses:{status_id}", "name") or "—"
def get_document_type_name(type_id): return r.hget(f"document_types:{type_id}", "name") or "—"

def get_clinics(): return [r.hgetall(k) for k in r.keys("clinics:*")]
def get_services(): return [r.hgetall(k) for k in r.keys("services:*")]
def get_doctors(): return [r.hgetall(k) for k in r.keys("doctors:*")]

# =============================
# === ПОДКЛЮЧЕНИЕ К POSTGRES ===
# =============================
def get_pg_conn():
    return psycopg.connect(
        host=PG['host'],
        dbname=PG['db'],
        user=PG['user'],
        password=PG['password']
    )

# =============================
# === ВХОД В СИСТЕМУ ===
# =============================
def login():
    print("=== ВХОД В СИСТЕМУ ===")
    login_input = input("Логин: ").strip()
    password = input("Пароль: ").strip()

    if not login_input or not password:
        print("Логин и пароль обязательны!")
        return None

    try:
        conn = get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id, u.password_hash, p.full_name, u.role_id
                FROM users u
                LEFT JOIN profiles p ON p.user_id = u.id
                WHERE u.login = %s
            """, (login_input,))
            user = cur.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode(), user[1].encode()):
            role_name = get_role_name(user[3])
            print(f"Добро пожаловать, {user[2]}! Роль: {role_name}")
            return {'id': user[0], 'full_name': user[2], 'role_id': user[3], 'role': role_name}
        else:
            print("Неверный логин или пароль")
            return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

# =============================
# === МЕНЮ ПАЦИЕНТА ===
# =============================
def patient_menu(user):
    while True:
        print("\n" + "="*60)
        print("ПАЦИЕНТ: Личный кабинет")
        print("="*60)
        print("1. Создать запись")
        print("2. Мои записи")
        print("3. Просмотр заключений")
        print("0. Выход")
        choice = input("→ ").strip()

        # Создать запись
        if choice == "1":
            clinics = get_clinics()
            if not clinics:
                print("Клиники не найдены")
                continue
            print("\nВыберите клинику:")
            for i, c in enumerate(clinics, 1):
                print(f"  {i}. {c.get('name')} ({c.get('address')})")
            try:
                clinic_idx = int(input("№: ")) - 1
                clinic_id = r.keys("clinics:*")[clinic_idx].split(":", 1)[1]
            except:
                print("Ошибка ввода!")
                continue

            services = get_services()
            if not services:
                print("Услуги не найдены")
                continue
            print("\nВыберите услугу:")
            for i, s in enumerate(services, 1):
                print(f"  {i}. {s.get('name')} — {s.get('price')} руб.")
            try:
                service_idx = int(input("№: ")) - 1
                service_id = r.keys("services:*")[service_idx].split(":", 1)[1]
            except:
                print("Ошибка ввода!")
                continue

            doctors = get_doctors()
            if not doctors:
                print("Врачи не найдены")
                continue
            print("\nВыберите врача:")
            for i, d in enumerate(doctors, 1):
                print(f"  {i}. {d.get('full_name')} — {d.get('specialty')}")
            try:
                doctor_idx = int(input("№: ")) - 1
                doctor_id = r.keys("doctors:*")[doctor_idx].split(":", 1)[1]
            except:
                print("Ошибка ввода!")
                continue

            date_input = input("\nДата и время (ГГГГ-ММ-ДД ЧЧ:ММ): ").strip()
            try:
                datetime.strptime(date_input, "%Y-%m-%d %H:%M")
            except:
                print("Неверный формат!")
                continue

            try:
                conn = get_pg_conn()
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO appointments 
                        (user_id, clinic_id, service_id, doctor_id, appointment_date, status)
                        VALUES (%s, %s, %s, %s, %s, '1adcb519-1ce5-4689-8df0-96273cf94f48')
                        RETURNING id
                    """, (user['id'], clinic_id, service_id, doctor_id, date_input))
                    app_id = cur.fetchone()[0]
                conn.commit()
                conn.close()
                print(f"\nЗапись создана! ID: {app_id}")
            except Exception as e:
                print(f"Ошибка: {e}")

        # Мои записи
        elif choice == "2":
            conn = get_pg_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, clinic_id, service_id, doctor_id, appointment_date, status
                    FROM appointments WHERE user_id = %s ORDER BY appointment_date DESC
                """, (user['id'],))
                rows = cur.fetchall()
            conn.close()

            if not rows:
                print("\nНет записей")
                continue

            display = [[r[0], r[4].strftime("%Y-%m-%d %H:%M"),
                        get_status_name(r[5]),
                        get_clinic_name(r[1]), get_service_name(r[2]), get_doctor_name(r[3])]
                       for r in rows]
            print("\n" + tabulate(display, headers=["ID", "Дата", "Статус", "Клиника", "Услуга", "Врач"], tablefmt="grid"))

        # Просмотр заключений
        elif choice == "3":
            conn = get_pg_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, appointment_date, clinic_id, service_id, doctor_id
                    FROM appointments
                    WHERE user_id = %s AND status = %s
                    ORDER BY appointment_date DESC
                """, (user['id'], '6955d3f5-8d05-4935-bab7-49787bca093a'))
                completed = cur.fetchall()
            conn.close()

            if not completed:
                print("\nНет завершённых записей")
                continue

            print("\nЗавершённые записи:")
            app_map = {}
            for i, row in enumerate(completed, 1):
                app_id = row[0]
                app_map[i] = app_id
                print(f"  {i}. ID: {app_id} | Дата: {row[1].strftime('%Y-%m-%d %H:%M')}")
                print(f"     Клиника: {get_clinic_name(row[2])} | Услуга: {get_service_name(row[3])} | Врач: {get_doctor_name(row[4])}")

            try:
                idx = int(input("\n№ записи: "))
                app_id = app_map[idx]
            except:
                print("Неверный номер")
                continue

            doc = documents_collection.find_one({"metadata.appointment_id": app_id})
            if not doc:
                print(f"Заключение не найдено для ID {app_id}")
                continue

            type_id = doc['metadata'].get('document_type_id', '6fe99a26-5e07-45a0-b6c8-f6ca0187a411')
            print("\n" + "="*60)
            print(f"{get_document_type_name(type_id)} (ID записи: {app_id})")
            print("="*60)
            print(doc["content"])
            print("="*60)
            print(f"Создано: {doc['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"Файл: {doc['filename']}")

        elif choice == "0":
            print("До свидания!")
            break

# =============================
# === МЕНЮ ВРАЧА ===
# =============================
def doctor_menu(user):
    try:
        conn = get_pg_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM doctors WHERE user_id = %s", (user['id'],))
            doctor_uuid = cur.fetchone()
        conn.close()
        if not doctor_uuid:
            print("Вы не зарегистрированы как врач")
            return
        doctor_uuid = str(doctor_uuid[0])
    except Exception as e:
        print(f"Ошибка: {e}")
        return

    while True:
        print("\n" + "="*60)
        print("ВРАЧ: Записи пациентов")
        print("="*60)
        print("1. Записи на сегодня")
        print("2. Написать заключение")
        print("0. Выход")
        choice = input("→ ").strip()

        if choice == "1":
            today = datetime.now().strftime('%Y-%m-%d')
            conn = get_pg_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.id, p.full_name, a.appointment_date, a.clinic_id, a.service_id, a.status
                    FROM appointments a
                    JOIN users u ON a.user_id = u.id
                    JOIN profiles p ON p.user_id = u.id
                    WHERE a.doctor_id = %s AND DATE(a.appointment_date) = %s
                    ORDER BY a.appointment_date
                """, (doctor_uuid, today))
                rows = cur.fetchall()
            conn.close()

            if not rows:
                print("Нет записей на сегодня")
                continue

            display = [[r[0], r[1], r[2].strftime("%H:%M"),
                        get_clinic_name(r[3]), get_service_name(r[4]), get_status_name(r[5])]
                       for r in rows]
            print("\nЗаписи на сегодня:")
            print(tabulate(display, headers=["ID", "Пациент", "Время", "Клиника", "Услуга", "Статус"], tablefmt="grid"))

        elif choice == "2":
            conn = get_pg_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.id, p.full_name, a.appointment_date
                    FROM appointments a
                    JOIN users u ON a.user_id = u.id
                    JOIN profiles p ON p.user_id = u.id
                    WHERE a.doctor_id = %s AND a.status = %s
                    ORDER BY a.appointment_date DESC
                """, (doctor_uuid, '6955d3f5-8d05-4935-bab7-49787bca093a'))
                completed = cur.fetchall()
            conn.close()

            if not completed:
                print("Нет выполненных записей")
                continue

            print("\nВыполненные записи:")
            for i, row in enumerate(completed, 1):
                print(f"  {i}. ID: {row[0]} | Пациент: {row[1]} | Дата: {row[2].strftime('%Y-%m-%d %H:%M')}")

            try:
                idx = int(input("№ записи: ")) - 1
                app_id = completed[idx][0]
            except:
                print("Неверный номер")
                continue

            print("\nВведите текст заключения (пустая строка — завершить):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            conclusion = "\n".join(lines)

            if not conclusion.strip():
                print("Заключение пустое!")
                continue

            doc_uuid = str(uuid.uuid4())
            document = {
                "filename": f"{doc_uuid}.txt",
                "content": conclusion,
                "contentType": "text/plain",
                "uploaded_at": datetime.now(timezone.utc),
                "metadata": {
                    "appointment_id": app_id,
                    "doctor_id": doctor_uuid,
                    "document_type_id": "6fe99a26-5e07-45a0-b6c8-f6ca0187a411"
                }
            }
            result = documents_collection.insert_one(document)
            print(f"Заключение сохранено! Документ ID: {result.inserted_id}")

        elif choice == "0":
            print("До свидания!")
            break

# =============================
# === МЕНЮ АДМИНИСТРАТОРА ===
# =============================
def admin_menu(user):
    REFERENCE_BOOKS = {
        "1": {"name": "Клиники",           "pattern": "clinics:*",      "fields": ["name", "address"]},
        "2": {"name": "Услуги",            "pattern": "services:*",     "fields": ["name", "price"]},
        "3": {"name": "Врачи",             "pattern": "doctors:*",      "fields": ["full_name", "specialty", "user_id"]},
        "4": {"name": "Типы документов",   "pattern": "document_types:*", "fields": ["name", "description"]},
        "5": {"name": "Роли",              "pattern": "roles:*",        "fields": ["name", "description"]},
        "6": {"name": "Состояния записи",  "pattern": "appointment_statuses:*", "fields": ["name"]}
    }

    while True:
        print("\n" + "="*60)
        print("АДМИНИСТРАТОР: Справочники")
        print("="*60)
        print("1. Просмотр справочника")
        print("2. Добавить запись")
        print("0. Выход")
        choice = input("→ ").strip()

        if choice == "1":
            print("\nВыберите справочник:")
            for k, v in REFERENCE_BOOKS.items():
                print(f"  {k}. {v['name']}")
            ref_choice = input("№: ").strip()

            if ref_choice not in REFERENCE_BOOKS:
                print("Неверный выбор")
                continue

            ref = REFERENCE_BOOKS[ref_choice]
            keys = r.keys(ref["pattern"])
            if not keys:
                print(f"\nСправочник '{ref['name']}' пуст")
                continue

            print(f"\n{ref['name']}:")
            data = []
            for key in keys:
                uuid_val = key.split(":", 1)[1]
                values = r.hgetall(key)
                row = [uuid_val] + [values.get(f, "—") for f in ref["fields"]]
                data.append(row)
            headers = ["UUID"] + ref["fields"]
            print(tabulate(data, headers=headers, tablefmt="grid"))

        elif choice == "2":
            print("\nВыберите справочник для добавления:")
            for k, v in REFERENCE_BOOKS.items():
                print(f"  {k}. {v['name']}")
            ref_choice = input("№: ").strip()

            if ref_choice not in REFERENCE_BOOKS:
                print("Неверный выбор")
                continue

            ref = REFERENCE_BOOKS[ref_choice]
            new_uuid = str(uuid.uuid4())
            print(f"\nНовая запись в '{ref['name']}'")
            print(f"UUID: {new_uuid}")

            values = {}
            for field in ref["fields"]:
                if field == "price":
                    while True:
                        val = input(f"{field} (число): ").strip()
                        if val.isdigit():
                            values[field] = val
                            break
                        print("Введите число!")
                elif field == "user_id":
                    while True:
                        val = input(f"{field} (ID пользователя): ").strip()
                        if val.isdigit() or val == "":
                            values[field] = val
                            break
                        print("Только цифры или пусто")
                else:
                    val = input(f"{field}: ").strip()
                    if not val:
                        print("Поле обязательно!")
                        break
                    values[field] = val
            else:
                key = f"{ref['pattern'].split(':')[0]}:{new_uuid}"
                r.hset(key, mapping=values)
                print(f"Запись добавлена! UUID: {new_uuid}")

        elif choice == "0":
            print("До свидания!")
            break

# === ЗАПУСК ===
if __name__ == "__main__":
    user = login()
    if not user:
        exit()

    role_lower = user['role'].lower()
    if "пациент" in role_lower:
        patient_menu(user)
    elif "врач" in role_lower:
        doctor_menu(user)
    elif "админ" in role_lower or "администратор" in role_lower:
        admin_menu(user)
    else:
        print("Роль не поддерживается")