import sqlite3
from pathlib import Path
from flask import g

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'property.db'
SCHEMA_PATH = BASE_DIR / 'schema.sql'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_all(sql, params=()):
    db = get_db()
    return [dict(row) for row in db.execute(sql, params).fetchall()]


def query_one(sql, params=()):
    db = get_db()
    row = db.execute(sql, params).fetchone()
    return dict(row) if row else None


def execute(sql, params=()):
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.execute('PRAGMA foreign_keys = ON')
    conn.commit()
    conn.close()


def seed_demo_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = OFF')
    has_customer = conn.execute('SELECT COUNT(1) AS c FROM customers').fetchone()['c']
    if has_customer:
        conn.close()
        return
    conn.executescript(
        """
        INSERT INTO customers (customer_type, subject_type, name, contact_person, phone, id_no, email, address, status, remark)
        VALUES
        ('业主', '企业', '德汇资产管理有限公司', '王敏', '13800000001', '91310100DEHUI001', 'owner@dehui.com', '上海市', '正常', '示例业主'),
        ('租户', '企业', '创新科技有限公司', '李强', '13800000002', '91310100CHUANGXIN002', 'tenant@tech.com', '上海市', '在租', '示例租户'),
        ('租户', '个人', '张晨', '', '13800000003', '310101199001011234', 'zhang@example.com', '上海市', '在租', '个人租户');

        INSERT INTO property_units (unit_code, building_no, floor_no, unit_type, area, usable_area, owner_customer_id, tenant_customer_id, lease_status, delivery_status, remark)
        VALUES
        ('A-101', 'A栋', '1F', '办公', 320.5, 280.0, 1, 2, '已出租', '已交付', '办公单元'),
        ('A-201', 'A栋', '2F', '办公', 180.0, 150.0, 1, 3, '已出租', '已交付', '小型办公室'),
        ('B-S01', 'B栋', '1F', '商铺', 95.0, 90.0, 1, NULL, '空置', '已交付', '临街商铺');

        INSERT INTO rent_bills (bill_no, customer_id, unit_id, bill_type, billing_period_start, billing_period_end, amount_receivable, amount_received, amount_outstanding, due_date, status, payment_method, reminder_status, remark)
        VALUES
        ('RB202604-001', 2, 1, '租金', '2026-04-01', '2026-04-30', 25640.00, 10000.00, 15640.00, '2026-04-10', '部分支付', '转账', '已提醒', '4月租金'),
        ('RB202604-002', 3, 2, '租金', '2026-04-01', '2026-04-30', 13500.00, 0.00, 13500.00, '2026-04-10', '已逾期', '', '未提醒', '4月租金');

        INSERT INTO payment_records (bill_id, customer_id, amount, payment_method, voucher_url, payer_name, paid_at, operator_id, remark)
        VALUES
        (1, 2, 10000.00, '转账', '', '创新科技有限公司', '2026-04-08 10:30:00', 'admin', '首笔付款');

        INSERT INTO vehicles (customer_id, plate_no, vehicle_type, color, status, monthly_start, monthly_end, remark)
        VALUES
        (2, '沪A12345', '新能源车', '白色', '正常', '2026-04-01', '2027-03-31', '月租车辆'),
        (3, '沪B55667', '燃油车', '黑色', '正常', '2026-04-01', '2026-09-30', '短租');

        INSERT INTO parking_spaces (parking_code, area_zone, parking_type, status, bind_customer_id, bind_vehicle_id, monthly_fee, effective_start, effective_end, remark)
        VALUES
        ('P1-001', '地下1层A区', '月租车位', '已分配', 2, 1, 800.00, '2026-04-01', '2027-03-31', '靠近电梯'),
        ('P1-002', '地下1层A区', '临停车位', '空闲', NULL, NULL, 0.00, NULL, NULL, ''),
        ('P2-015', '地下2层B区', '固定车位', '空闲', NULL, NULL, 1000.00, NULL, NULL, '标准车位');

        INSERT INTO parking_records (plate_no, parking_space_id, entry_time, exit_time, duration_minutes, receivable_fee, received_fee, pay_status, pay_method, source)
        VALUES
        ('沪C88888', 2, '2026-04-20 09:00:00', '2026-04-20 12:20:00', 200, 20.00, 20.00, '已支付', '扫码', '人工登记'),
        ('沪D66666', 2, '2026-04-20 14:00:00', NULL, NULL, 0.00, 0.00, '未支付', '', '人工登记');

        INSERT INTO repair_orders (repair_no, customer_id, unit_id, repair_type, title, content, image_urls, priority, status, source, reported_at, accepted_at, assigned_to, completed_at, customer_feedback, satisfaction_score, close_reason, remark)
        VALUES
        ('RP202604-001', 2, 1, '空调', '办公室空调不制冷', 'A-101 办公室空调运行异常，无法制冷。', '', '高', '处理中', 'Web', '2026-04-20 09:30:00', '2026-04-20 09:50:00', '工程班组-张工', NULL, '', NULL, '', '尽快处理'),
        ('RP202604-002', 3, 2, '水电', '插座无电', 'A-201 工位区插座突然断电。', '', '中', '待受理', '微信小程序', '2026-04-20 11:20:00', NULL, '', NULL, '', NULL, '', '');

        INSERT INTO repair_logs (repair_id, action, operator_id, operator_role, action_content, attachment_urls)
        VALUES
        (1, '提交', 'customer-2', '租户', '提交空调报修', ''),
        (1, '受理', 'service-01', '客服', '客服已受理，准备派单', ''),
        (1, '派单', 'service-01', '客服', '指派给工程班组-张工', ''),
        (2, '提交', 'customer-3', '租户', '提交插座断电报修', '');
        """
    )
    conn.execute('PRAGMA foreign_keys = ON')
    conn.commit()
    conn.close()
