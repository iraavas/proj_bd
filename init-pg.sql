CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================
-- ТАБЛИЦА: Пользователи системы
-- ==============================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==============================
-- ТАБЛИЦА: Персональные данные
-- ==============================
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    birth_date DATE,
    phone VARCHAR(30),
    address TEXT,
    gender VARCHAR(10),
    insurance_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==============================
-- ТАБЛИЦА: Врачи
-- ==============================
CREATE TABLE IF NOT EXISTS doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    specialty VARCHAR(100),
    qualification VARCHAR(100),
    clinic_id UUID,
    experience_years INT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==============================
-- ТАБЛИЦА: Записи на приём
-- ==============================
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,         -- пациент (user_id)
    clinic_id UUID NOT NULL,
    service_id UUID NOT NULL,
    doctor_id UUID NOT NULL,
    appointment_date TIMESTAMP NOT NULL,
    status UUID DEFAULT '1adcb519-1ce5-4689-8df0-96273cf94f48', -- "Запланирована"
    document_ids TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==============================
-- ТЕСТОВЫЕ ДАННЫЕ
-- ==============================

-- Роли (пример UUID совпадает с Redis)
-- пациент: 6bdab82a-9afb-4511-9bdc-ae3dc72311ec
-- врач:    83d4ea0f-e20b-4ff5-9afd-cc4336180d94
-- админ:   11e7b7dc-e847-4ceb-9ff9-0a1b9c0d5de2

INSERT INTO users (login, password_hash, role_id) VALUES
  ('patient1', '$2b$12$gArjHCgtNVqcCnLb5E//FegKHYXFCe3f6GuFl4AG85AasDgip1zqu', '6bdab82a-9afb-4511-9bdc-ae3dc72311ec'),
  ('doctor1',  '$2b$12$gArjHCgtNVqcCnLb5E//FegKHYXFCe3f6GuFl4AG85AasDgip1zqu', '83d4ea0f-e20b-4ff5-9afd-cc4336180d94'),
  ('admin1',   '$2b$12$gArjHCgtNVqcCnLb5E//FegKHYXFCe3f6GuFl4AG85AasDgip1zqu', '11e7b7dc-e847-4ceb-9ff9-0a1b9c0d5de2')
ON CONFLICT DO NOTHING;

-- Профили пользователей
INSERT INTO profiles (user_id, full_name, email, birth_date)
SELECT id, 
       CASE login
            WHEN 'patient1' THEN 'Иванов Иван Иванович'
            WHEN 'doctor1'  THEN 'Петрова Анна Сергеевна'
            WHEN 'admin1'   THEN 'Сидоров Алексей Петрович'
        END AS full_name,
       CASE login
            WHEN 'patient1' THEN 'ivanov@example.com'
            WHEN 'doctor1'  THEN 'petrova@example.com'
            WHEN 'admin1'   THEN 'sidorov@example.com'
        END AS email,
       CASE login
            WHEN 'patient1' THEN '1985-03-15'::date
            WHEN 'doctor1'  THEN '1990-07-22'::date
            WHEN 'admin1'   THEN '1980-11-05'::date
        END AS birth_date
FROM users
ON CONFLICT DO NOTHING;

-- Врач (связь с пользователем)
INSERT INTO doctors (user_id, full_name, specialty, qualification, clinic_id, experience_years)
SELECT id, 'Петрова Анна Сергеевна', 'Терапевт', 'Врач высшей категории', '4e1bdf84-c7f1-4222-a5bd-5dca4817d3f2', 8
FROM users WHERE login = 'doctor1'
ON CONFLICT DO NOTHING;

-- Тестовые записи приёма
INSERT INTO appointments (user_id, clinic_id, service_id, doctor_id, appointment_date, status)
VALUES
  (
    (SELECT id FROM users WHERE login = 'patient1'),
    '4e1bdf84-c7f1-4222-a5bd-5dca4817d3f2',
    'ce88634e-0e4b-44e4-b663-88d9e99fccea',
    (SELECT id FROM doctors WHERE user_id = (SELECT id FROM users WHERE login = 'doctor1')),
    '2025-10-25 10:00:00',
    '1adcb519-1ce5-4689-8df0-96273cf94f48'  -- Запланирована
  ),
  (
    (SELECT id FROM users WHERE login = 'patient1'),
    'fc42f9fe-c03f-405a-a418-238bb1e67288',
    '2c5f80c3-1d8e-4998-a46b-ccde0085acd7',
    (SELECT id FROM doctors WHERE user_id = (SELECT id FROM users WHERE login = 'doctor1')),
    '2025-10-26 14:00:00',
    '39058f6e-4aaf-4eef-988a-734580796fa9'  -- Отменена
  ),
  (
    (SELECT id FROM users WHERE login = 'patient1'),
    '4e1bdf84-c7f1-4222-a5bd-5dca4817d3f2',
    'ce88634e-0e4b-44e4-b663-88d9e99fccea',
    (SELECT id FROM doctors WHERE user_id = (SELECT id FROM users WHERE login = 'doctor1')),
    '2025-10-24 09:00:00',
    '6955d3f5-8d05-4935-bab7-49787bca093a'  -- Выполнена
  )
ON CONFLICT DO NOTHING;
