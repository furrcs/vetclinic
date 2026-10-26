DROP DATABASE IF EXISTS vetclinic;
CREATE DATABASE vetclinic ENCODING 'UTF8';

\c vetclinic

CREATE TABLE Breeds (
    breed_id SERIAL PRIMARY KEY,
    pet_type VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Services (
    service_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    price DECIMAL(10,2) NOT NULL
);

CREATE TABLE Suppliers (
    supplier_id SERIAL PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    address VARCHAR(200)
);

CREATE TABLE Medicines (
    medicine_id SERIAL PRIMARY KEY,
    supplier_id INT REFERENCES Suppliers(supplier_id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50),
    stock INT DEFAULT 0,
    UNIQUE (supplier_id, name)
);

CREATE TABLE Employees (
    employee_id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    surname VARCHAR(30) NOT NULL,
    third_name VARCHAR(30),
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    role VARCHAR(20) NOT NULL
);

CREATE TABLE Clients (
    client_id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    surname VARCHAR(30) NOT NULL,
    third_name VARCHAR(30),
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100)
);

CREATE TABLE Pets (
    pet_id SERIAL PRIMARY KEY,
    breed_id INT REFERENCES Breeds(breed_id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    color VARCHAR(50),
    birth_date DATE,
    CHECK (gender IN ('самец', 'самка'))
);

CREATE TABLE Client_pet (
    client_id INT REFERENCES Clients(client_id) ON DELETE CASCADE,
    pet_id INT REFERENCES Pets(pet_id) ON DELETE CASCADE,
    PRIMARY KEY (client_id, pet_id)
);

CREATE TABLE Appointments (
    appointment_id SERIAL PRIMARY KEY,
    pet_id INT REFERENCES Pets(pet_id) ON DELETE SET NULL,
    client_id INT REFERENCES Clients(client_id) ON DELETE SET NULL,
    employee_id INT REFERENCES Employees(employee_id) ON DELETE SET NULL,
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'запланирован',
    CHECK (status IN ('запланирован', 'завершён', 'отменён'))
);

CREATE TABLE Medical_records (
    record_id SERIAL PRIMARY KEY,
    appointment_id INT REFERENCES Appointments(appointment_id) ON DELETE CASCADE,
    reason TEXT,
    diagnosis TEXT,
    temperature DECIMAL(4,1),
    weight DECIMAL(5,2),
    recommendations TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (appointment_id)
);

CREATE TABLE Appointment_service (
    appointment_id INT REFERENCES Appointments(appointment_id) ON DELETE CASCADE,
    service_id INT REFERENCES Services(service_id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (appointment_id, service_id)
);

CREATE TABLE Appointment_medicine (
    appointment_id INT REFERENCES Appointments(appointment_id) ON DELETE CASCADE,
    medicine_id INT REFERENCES Medicines(medicine_id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1,
    dosage VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (appointment_id, medicine_id)
);

CREATE TABLE Payments (
    payment_id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES Employees(employee_id) ON DELETE SET NULL,
    client_id INT REFERENCES Clients(client_id) ON DELETE SET NULL,
    appointment_id INT REFERENCES Appointments(appointment_id),
    payment_date TIMESTAMP,
    payment_method VARCHAR(20),
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    UNIQUE (appointment_id),
    CHECK (amount >= 0),
    CHECK (status IN ('не оплачен', 'оплачен'))
);




INSERT INTO Breeds (pet_type, name) VALUES
('кошка',  'Британская короткошёрстная'),
('кошка',  'Мейн-кун'),
('кошка',  'Сфинкс'),
('кошка',  'Шотландская вислоухая'),
('собака', 'Лабрадор-ретривер'),
('собака', 'Немецкая овчарка'),
('собака', 'Йоркширский терьер'),
('собака', 'Хаски'),
('собака', 'Чихуахуа'),
('птица',  'Волнистый попугай'),
('грызун', 'Джунгарский хомяк');

INSERT INTO Services (name, price) VALUES
('Первичный приём',            800.00),
('Повторный приём',            500.00),
('Вакцинация',                1200.00),
('УЗИ',                       1800.00),
('Рентген',                   2200.00),
('Общий анализ крови',         900.00),
('Биохимический анализ крови',1500.00),
('Стрижка когтей',             300.00),
('Кастрация',                 5000.00),
('Стерилизация',              7000.00),
('Чистка зубов',              3500.00),
('Установка микрочипа',       1500.00);

INSERT INTO Suppliers (company_name, phone, email, address) VALUES
('ООО "ВетФарм"',   '+7-495-111-22-33', 'sales@vetfarm.ru', 'г. Москва, ул. Ленина, 15'),
('ЗАО "ЗооМед"',    '+7-812-444-55-66', 'info@zoomed.ru',   'г. Санкт-Петербург, пр. Мира, 8'),
('ИП Смирнов А.В.', '+7-903-777-88-99', 'smirnov@mail.ru',  'г. Казань, ул. Гагарина, 42'),
('ООО "ПетТовары"', '+7-499-222-33-44', NULL,               'г. Москва, ш. Энтузиастов, 100');

INSERT INTO Medicines (supplier_id, name, price, unit, stock) VALUES
(1, 'Амоксициллин 15%',        450.00, 'флакон 10 мл',    25),
(1, 'Новокаин 0.5%',           120.00, 'ампула 5 мл',    100),
(1, 'Дексаметазон',            280.00, 'ампула 2 мл',     40),
(2, 'Мелоксикам (Метакам)',    890.00, 'флакон 10 мл',    15),
(2, 'Фуросемид',                95.00, 'ампула 2 мл',     80),
(2, 'Тиамин (B1)',             150.00, 'ампула 1 мл',     60),
(3, 'Габапентин',              620.00, 'упаковка 30 капс.',20),
(3, 'Омепразол',               340.00, 'упаковка 30 капс.',30),
(4, 'Витамины VetLife',        550.00, 'флакон 50 мл',    50),
(4, 'Шампунь лечебный',        780.00, 'бутылка 250 мл',  12);

INSERT INTO Employees (name, surname, third_name, phone, email, role) VALUES
('Ольга',     'Иванова',  'Петровна',     '+7-901-100-10-10', 'ivanova@vetclinic.ru', 'admin'),
('Дмитрий',   'Соколов',  'Андреевич',    '+7-901-200-20-20', 'sokolov@vetclinic.ru', 'doctor'),
('Екатерина', 'Морозова', 'Сергеевна',    '+7-901-300-30-30', 'morozova@vetclinic.ru', 'doctor'),
('Артём',     'Кузнецов', 'Игоревич',     '+7-901-400-40-40', 'kuznetsov@vetclinic.ru', 'assistant'),
('Мария',     'Попова',   'Владимировна', '+7-901-500-50-50', 'popova@vetclinic.ru', 'receptionist'),
('Игорь',     'Лебедев',  NULL,           '+7-901-600-60-60', NULL, 'doctor');

INSERT INTO Clients (name, surname, third_name, phone, email) VALUES
('Анна',     'Петрова',  'Ивановна',     '+7-910-101-01-01', 'anna.p@mail.ru'),
('Сергей',   'Волков',   'Дмитриевич',   '+7-910-202-02-02', 'volkov@yandex.ru'),
('Елена',    'Зайцева',  NULL,           '+7-910-303-03-03', 'zaitseva@gmail.com'),
('Михаил',   'Орлов',    'Александрович','+7-910-404-04-04', NULL),
('Татьяна',  'Никитина', 'Юрьевна',      '+7-910-505-05-05', 'nikitina@mail.ru'),
('Андрей',   'Фёдоров',  'Олегович',     '+7-910-606-06-06', 'fedorov@bk.ru'),
('Светлана', 'Козлова',  'Михайловна',   '+7-910-707-07-07', 'kozlova@mail.ru');

INSERT INTO Pets (breed_id, name, gender, color, birth_date) VALUES
(1,  'Мурка',  'самка',  'серая',         '2021-05-10'),
(5,  'Барсик', 'самец',  'палевый',       '2020-03-15'),
(2,  'Симба',  'самец',  'рыжий',         '2022-07-01'),
(6,  'Рекс',   'самец',  'чёрный',        '2019-11-20'),
(7,  'Чип',    'самец',  'коричневый',    '2023-02-14'),
(3,  'Луна',   'самка',  'белый',         '2021-09-30'),
(10, 'Кеша',   'самец',  'зелёный',       '2022-04-12'),
(4,  'Плюша',  'самка',  'серо-белый',    '2020-12-25'),
(8,  'Найда',  'самка',  'серо-белый',    '2018-06-05'),
(9,  'Бублик', 'самец',  'бежевый',       '2023-01-08'),
(11, 'Хома',   'самец',  'рыже-серый',    '2023-03-20');

INSERT INTO Client_pet (client_id, pet_id) VALUES
(1, 1),  (1, 2),   -- Анна: Мурка, Барсик
(2, 3),  (2, 4),   -- Сергей: Симба, Рекс
(3, 5),  (3, 6),   -- Елена: Чип, Луна
(4, 7),            -- Михаил: Кеша
(5, 8),            -- Татьяна: Плюша
(6, 9),  (6, 10),  -- Андрей: Найда, Бублик
(7, 11);           -- Светлана: Хома

INSERT INTO Appointments (pet_id, client_id, employee_id, appointment_date, status) VALUES
(1, 1, 2, '2025-09-01 10:00:00', 'завершён'),
(3, 2, 3, '2025-09-01 11:30:00', 'завершён'),
(4, 2, 6, '2025-09-02 09:00:00', 'завершён'),
(2, 1, 2, '2025-09-03 14:00:00', 'завершён'),
(5, 3, 3, '2025-09-05 15:30:00', 'отменён'),
(7, 4, 3, '2025-09-07 12:00:00', 'завершён'),
(6, 3, 2, '2025-09-10 16:00:00', 'завершён'),
(8, 5, 6, '2025-09-12 10:30:00', 'завершён'),
(1, 1, 2, '2025-10-15 09:30:00', 'запланирован'),
(11,7, 3, '2025-10-16 11:00:00', 'запланирован');

INSERT INTO Medical_records (appointment_id, reason, diagnosis, temperature, weight, recommendations, description) VALUES
(1, 'Плановый осмотр',            'Здорова',                     38.5, 4.20, 'Повторный осмотр через год',       'Общее состояние удовлетворительное'),
(2, 'Кашель, вялость',            'Бронхит',                     39.2, 5.80, 'Антибиотики 7 дней, повтор через 5 дней', 'Хрипы в лёгких, назначено лечение'),
(3, 'Хромота на заднюю лапу',     'Растяжение связок',           38.7,28.50, 'Ограничить активность 2 недели',   'Рентген без переломов'),
(4, 'Вакцинация',                 'Здоров',                      38.4, 4.50, 'Следующая вакцинация через год',   'Привит от бешенства и комплексно'),
(6, 'Потеря аппетита',            'Гастрит',                     39.0, 0.05, 'Диета, омепразол 10 дней',         'Птица ослаблена, назначено лечение'),
(7, 'Плановый осмотр',            'Здорова',                     38.3, 3.80, 'Обработка от паразитов',           'Проблем не выявлено'),
(8, 'Расчёсы на боках',           'Аллергический дерматит',      38.6, 6.10, 'Гипоаллергенный корм, шампунь',    'Назначен лечебный шампунь');

INSERT INTO Appointment_service (appointment_id, service_id, quantity, price) VALUES
(1, 1,  1,  800.00),   -- Мурка: первичный приём
(1, 8,  1,  300.00),   -- Мурка: стрижка когтей
(2, 1,  1,  800.00),   -- Симба: первичный приём
(2, 5,  1, 2200.00),   -- Симба: рентген
(3, 1,  1,  800.00),   -- Рекс: первичный приём
(3, 5,  1, 2200.00),   -- Рекс: рентген
(4, 3,  1, 1200.00),   -- Барсик: вакцинация
(6, 1,  1,  800.00),   -- Кеша: первичный приём
(7, 1,  1,  800.00),   -- Луна: первичный приём
(7, 12, 1, 1500.00),   -- Луна: микрочип
(8, 1,  1,  800.00),   -- Плюша: первичный приём
(8, 4,  1, 1800.00);   -- Плюша: УЗИ

INSERT INTO Appointment_medicine (appointment_id, medicine_id, quantity, dosage, price) VALUES
(2, 1, 1, '1 мл 2 раза в день',             450.00),   -- Симба: Амоксициллин
(2, 8, 1, '1 капсула в день',               340.00),   -- Симба: Омепразол
(6, 8, 1, '1 капсула в день',               340.00),   -- Кеша: Омепразол
(8, 10,1, 'Наносить на поражённые участки', 780.00);   -- Плюша: Шампунь

INSERT INTO Payments (employee_id, client_id, appointment_id, payment_date, payment_method, amount, status) VALUES
(5, 1, 1, '2025-09-01 10:45:00', 'карта',    1100.00, 'оплачен'),   -- Мурка (800+300)
(5, 2, 2, '2025-09-01 12:30:00', 'наличные', 3790.00, 'оплачен'),   -- Симба (800+2200+450+340)
(5, 2, 3, '2025-09-02 10:00:00', 'карта',    3000.00, 'оплачен'),   -- Рекс (800+2200)
(5, 1, 4, '2025-09-03 14:30:00', 'карта',    1200.00, 'оплачен'),   -- Барсик (вакцинация)
(5, 4, 6, '2025-09-07 12:45:00', 'наличные', 1140.00, 'оплачен'),   -- Кеша (800+340)
(5, 3, 7, NULL,                  NULL,       2300.00, 'не оплачен'),-- Луна (800+1500) — долг
(5, 5, 8, NULL,                  NULL,       3380.00, 'не оплачен');-- Плюша (800+1800+780) — долг

COMMIT;