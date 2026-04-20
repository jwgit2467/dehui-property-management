from datetime import datetime
from flask import Blueprint, jsonify, request
from ..db import execute, query_all, query_one

rent_bp = Blueprint('rent', __name__)


def compute_bill_status(receivable, received, due_date):
    outstanding = round(float(receivable or 0) - float(received or 0), 2)
    today = datetime.now().date()
    due = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else today
    if outstanding <= 0:
        return '已支付', 0
    if received > 0:
        return '部分支付', outstanding
    if due < today:
        return '已逾期', outstanding
    return '待支付', outstanding


@rent_bp.route('/bills', methods=['GET'])
def list_bills():
    keyword = request.args.get('keyword', '').strip()
    sql = '''
    SELECT b.*, c.name AS customer_name, p.unit_code
    FROM rent_bills b
    LEFT JOIN customers c ON b.customer_id = c.id
    LEFT JOIN property_units p ON b.unit_id = p.id
    '''
    params = []
    if keyword:
        sql += ' WHERE b.bill_no LIKE ? OR c.name LIKE ? OR IFNULL(p.unit_code, "") LIKE ? '
        params = [f'%{keyword}%'] * 3
    sql += ' ORDER BY b.id DESC'
    return jsonify(query_all(sql, params))


@rent_bp.route('/bills', methods=['POST'])
def create_bill():
    data = request.get_json()
    receivable = float(data.get('amount_receivable', 0))
    received = float(data.get('amount_received', 0))
    status, outstanding = compute_bill_status(receivable, received, data.get('due_date'))
    cur = execute(
        '''
        INSERT INTO rent_bills (bill_no, customer_id, unit_id, bill_type, billing_period_start, billing_period_end,
        amount_receivable, amount_received, amount_outstanding, due_date, status, payment_method, paid_at, reminder_status, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data.get('bill_no'), data.get('customer_id'), data.get('unit_id'), data.get('bill_type', '租金'),
            data.get('billing_period_start'), data.get('billing_period_end'), receivable, received, outstanding,
            data.get('due_date'), status, data.get('payment_method', ''), data.get('paid_at'), data.get('reminder_status', '未提醒'), data.get('remark')
        )
    )
    return jsonify({'message': '账单创建成功', 'id': cur.lastrowid, 'status': status})


@rent_bp.route('/generate', methods=['POST'])
def generate_bill():
    data = request.get_json()
    unit = query_one('SELECT * FROM property_units WHERE id = ?', (data.get('unit_id'),))
    if not unit:
        return jsonify({'message': '房源不存在'}), 404

    area = float(unit.get('area') or 0)
    unit_price = float(data.get('unit_price') or 0)
    receivable = round(area * unit_price, 2)
    due_date = data.get('due_date')
    status, outstanding = compute_bill_status(receivable, 0, due_date)
    bill_no = data.get('bill_no') or f"RB{datetime.now().strftime('%Y%m%d%H%M%S')}"

    cur = execute(
        '''
        INSERT INTO rent_bills (bill_no, customer_id, unit_id, bill_type, billing_period_start, billing_period_end,
        amount_receivable, amount_received, amount_outstanding, due_date, status, reminder_status, remark)
        VALUES (?, ?, ?, '租金', ?, ?, ?, 0, ?, ?, ?, '未提醒', ?)
        ''',
        (
            bill_no, data.get('customer_id'), data.get('unit_id'), data.get('billing_period_start'), data.get('billing_period_end'),
            receivable, outstanding, due_date, status, f'按面积 {area}㎡ × 单价 {unit_price} 元/㎡ 自动生成'
        )
    )
    return jsonify({'message': '账单生成成功', 'id': cur.lastrowid, 'bill_no': bill_no, 'amount_receivable': receivable})


@rent_bp.route('/payments', methods=['GET'])
def list_payments():
    rows = query_all(
        '''
        SELECT p.*, b.bill_no, c.name AS customer_name
        FROM payment_records p
        LEFT JOIN rent_bills b ON p.bill_id = b.id
        LEFT JOIN customers c ON p.customer_id = c.id
        ORDER BY p.id DESC
        '''
    )
    return jsonify(rows)


@rent_bp.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    bill = query_one('SELECT * FROM rent_bills WHERE id = ?', (data.get('bill_id'),))
    if not bill:
        return jsonify({'message': '账单不存在'}), 404

    amount = float(data.get('amount', 0))
    cur = execute(
        '''
        INSERT INTO payment_records (bill_id, customer_id, amount, payment_method, voucher_url, payer_name, paid_at, operator_id, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data.get('bill_id'), bill['customer_id'], amount, data.get('payment_method'), data.get('voucher_url'), data.get('payer_name'),
            data.get('paid_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data.get('operator_id', 'admin'), data.get('remark')
        )
    )

    total_received = float(bill['amount_received']) + amount
    status, outstanding = compute_bill_status(bill['amount_receivable'], total_received, bill['due_date'])
    execute(
        '''
        UPDATE rent_bills
        SET amount_received=?, amount_outstanding=?, status=?, payment_method=?, paid_at=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        ''',
        (total_received, outstanding, status, data.get('payment_method'), data.get('paid_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data.get('bill_id'))
    )
    return jsonify({'message': '缴费登记成功', 'payment_id': cur.lastrowid, 'bill_status': status, 'outstanding': outstanding})


@rent_bp.route('/reminders', methods=['GET'])
def list_reminders():
    rows = query_all(
        '''
        SELECT b.id, b.bill_no, c.name AS customer_name, p.unit_code, b.amount_outstanding, b.due_date, b.reminder_status
        FROM rent_bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        LEFT JOIN property_units p ON b.unit_id = p.id
        WHERE b.amount_outstanding > 0
        ORDER BY b.due_date ASC
        '''
    )
    return jsonify(rows)


@rent_bp.route('/reminders/<int:bill_id>', methods=['POST'])
def mark_reminder(bill_id):
    execute("UPDATE rent_bills SET reminder_status='已提醒', updated_at=CURRENT_TIMESTAMP WHERE id = ?", (bill_id,))
    return jsonify({'message': '提醒状态已更新'})
