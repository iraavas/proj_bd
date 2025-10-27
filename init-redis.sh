#!/bin/sh
# init-redis.sh

echo "Инициализация справочников в Redis..."

until redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Redis не готов, ждём..."
    sleep 2
done

# === РОЛИ ===
ROLE_PATIENT="6bdab82a-9afb-4511-9bdc-ae3dc72311ec"
ROLE_DOCTOR="83d4ea0f-e20b-4ff5-9afd-cc4336180d94"
ROLE_ADMIN="11e7b7dc-e847-4ceb-9ff9-0a1b9c0d5de2"

redis-cli -h redis HSET roles:$ROLE_PATIENT name "Пациент" description "Пациент"
redis-cli -h redis HSET roles:$ROLE_DOCTOR  name "Врач"      description "Врач"
redis-cli -h redis HSET roles:$ROLE_ADMIN   name "Администратор" description "Администратор"

# === СТАТУСЫ ЗАПИСЕЙ ===
STATUS_PLANNED="1adcb519-1ce5-4689-8df0-96273cf94f48"
STATUS_CANCELLED="39058f6e-4aaf-4eef-988a-734580796fa9"
STATUS_COMPLETED="6955d3f5-8d05-4935-bab7-49787bca093a"

redis-cli -h redis HSET appointment_statuses:$STATUS_PLANNED name "Запланирована"
redis-cli -h redis HSET appointment_statuses:$STATUS_CANCELLED name "Отменена"
redis-cli -h redis HSET appointment_statuses:$STATUS_COMPLETED name "Выполнена"

# === ТИПЫ ДОКУМЕНТОВ ===
DOC_TYPE_CONCLUSION="6fe99a26-5e07-45a0-b6c8-f6ca0187a411"
redis-cli -h redis HSET document_types:$DOC_TYPE_CONCLUSION name "Заключение" description "Медицинское заключение врача"

# === КЛИНИКИ ===
CLINIC1_UUID="4e1bdf84-c7f1-4222-a5bd-5dca4817d3f2"
CLINIC2_UUID="fc42f9fe-c03f-405a-a418-238bb1e67288"

redis-cli -h redis HSET clinics:$CLINIC1_UUID name "Городская поликлиника №1" address "ул. Ленина, 10"
redis-cli -h redis HSET clinics:$CLINIC2_UUID name "Кардиологический центр" address "пр. Мира, 25"

# === УСЛУГИ ===
SERVICE1_UUID="ce88634e-0e4b-44e4-b663-88d9e99fccea"
SERVICE2_UUID="2c5f80c3-1d8e-4998-a46b-ccde0085acd7"
SERVICE3_UUID="957f74fc-0732-4cd9-bed6-fbc1dbd1e9c3"

redis-cli -h redis HSET services:$SERVICE1_UUID name "Приём терапевта" price 1500
redis-cli -h redis HSET services:$SERVICE2_UUID name "Приём кардиолога" price 2500
redis-cli -h redis HSET services:$SERVICE3_UUID name "УЗИ сердца" price 3500

# === ВРАЧ ===
DOCTOR_UUID="a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1"
redis-cli -h redis HSET doctors:$DOCTOR_UUID full_name "Сидоров Пётр Алексеевич" specialty "Терапевт" user_id "2"

echo "Справочники инициализированы:"
echo "  Тип документа: Заключение = $DOC_TYPE_CONCLUSION"
echo "  Врач: $DOCTOR_UUID → user_id=2"