DROP TABLE IF EXISTS repair_logs;
DROP TABLE IF EXISTS repair_orders;
DROP TABLE IF EXISTS parking_records;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS parking_spaces;
DROP TABLE IF EXISTS payment_records;
DROP TABLE IF EXISTS rent_bills;
DROP TABLE IF EXISTS property_units;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_type TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT NOT NULL,
    id_no TEXT,
    email TEXT,
    address TEXT,
    status TEXT DEFAULT '正常',
    remark TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE property_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_code TEXT NOT NULL UNIQUE,
    building_no TEXT,
    floor_no TEXT,
    unit_type TEXT NOT NULL,
    area REAL DEFAULT 0,
    usable_area REAL DEFAULT 0,
    owner_customer_id INTEGER,
    tenant_customer_id INTEGER,
    lease_status TEXT DEFAULT '空置',
    delivery_status TEXT DEFAULT '未交付',
    remark TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_customer_id) REFERENCES customers(id),
    FOREIGN KEY (tenant_customer_id) REFERENCES customers(id)
);

CREATE TABLE rent_bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_no TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    unit_id INTEGER NOT NULL,
    bill_type TEXT NOT NULL,
    billing_period_start TEXT,
    billing_period_end TEXT,
    amount_receivable REAL DEFAULT 0,
    amount_received REAL DEFAULT 0,
    amount_outstanding REAL DEFAULT 0,
    due_date TEXT,
    status TEXT DEFAULT '待支付',
    payment_method TEXT,
    paid_at TEXT,
    reminder_status TEXT DEFAULT '未提醒',
    remark TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (unit_id) REFERENCES property_units(id)
);

CREATE TABLE payment_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    amount REAL DEFAULT 0,
    payment_method TEXT,
    voucher_url TEXT,
    payer_name TEXT,
    paid_at TEXT,
    operator_id TEXT,
    remark TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES rent_bills(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE parking_spaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parking_code TEXT NOT NULL UNIQUE,
    area_zone TEXT,
    parking_type TEXT NOT NULL,
    status TEXT DEFAULT '空闲',
    bind_customer_id INTEGER,
    bind_vehicle_id INTEGER,
    monthly_fee REAL DEFAULT 0,
    effective_start TEXT,
    effective_end TEXT,
    remark TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bind_customer_id) REFERENCES customers(id),
    FOREIGN KEY (bind_vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    plate_no TEXT NOT NULL UNIQUE,
    vehicle_type TEXT,
    color TEXT,
    status TEXT DEFAULT '正常',
    monthly_start TEXT,
    monthly_end TEXT,
    remark TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE parking_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_no TEXT NOT NULL,
    parking_space_id INTEGER,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    duration_minutes INTEGER,
    receivable_fee REAL DEFAULT 0,
    received_fee REAL DEFAULT 0,
    pay_status TEXT DEFAULT '未支付',
    pay_method TEXT,
    source TEXT DEFAULT '人工登记',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parking_space_id) REFERENCES parking_spaces(id)
);

CREATE TABLE repair_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_no TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    unit_id INTEGER,
    repair_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    image_urls TEXT,
    priority TEXT DEFAULT '中',
    status TEXT DEFAULT '待受理',
    source TEXT DEFAULT 'Web',
    reported_at TEXT,
    accepted_at TEXT,
    assigned_to TEXT,
    completed_at TEXT,
    customer_feedback TEXT,
    satisfaction_score INTEGER,
    close_reason TEXT,
    remark TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (unit_id) REFERENCES property_units(id)
);

CREATE TABLE repair_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    operator_id TEXT,
    operator_role TEXT,
    action_content TEXT,
    attachment_urls TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repair_id) REFERENCES repair_orders(id) ON DELETE CASCADE
);

CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_units_owner ON property_units(owner_customer_id);
CREATE INDEX idx_units_tenant ON property_units(tenant_customer_id);
CREATE INDEX idx_rent_bills_customer ON rent_bills(customer_id);
CREATE INDEX idx_parking_spaces_customer ON parking_spaces(bind_customer_id);
CREATE INDEX idx_vehicles_customer ON vehicles(customer_id);
CREATE INDEX idx_repair_orders_customer ON repair_orders(customer_id);
