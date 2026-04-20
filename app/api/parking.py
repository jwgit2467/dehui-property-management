from datetime import datetime
from flask import Blueprint, jsonify, request
from ..db import execute, query_all, query_one

parking_bp = Blueprint('parking', __name__)


def calc_temp_fee(duration_minutes):
    if duration_minutes <= 30:
        return 0
    hours = (duration_minutes + 59) // 60
    return min(hours * 5, 60)


@parking_bp.route('/spaces', methods=['GET'])
def list_spaces():
    rows = query_all(
        '''
        SELECT s.*, c.name AS customer_name, v.plate_no
        FROM parking_spaces s
        LEFT JOIN customers c ON s.bind_customer_id = c.id
        LEFT JOIN vehicles v ON s.bind_vehicle_id = v.id
        ORDER BY s.id DESC
        '''
    )
    return jsonify(rows)


@parking_bp.route('/spaces', methods=['POST'])
def create_space():
    data = request.get_json()
    cur = execute(
        '''
        INSERT INTO parking_spaces (parking_code, area_zone, parking_type, status, bind_customer_id, bind_vehicle_id, monthly_fee, effective_start, effective_end, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data.get('parking_code'), data.get('area_zone'), data.get('parking_type'), data.get('status', '空闲'), data.get('bind_customer_id'),
            data.get('bind_vehicle_id'), data.get('monthly_fee', 0), data.get('effective_start'), data.get('effective_end'), data.get('remark')
        )
    )
    return jsonify({'message': '车位创建成功', 'id': cur.lastrowid})


@parking_bp.route('/spaces/<int:space_id>/assign', methods=['POST'])
def assign_space(space_id):
    data = request.get_json()
    execute(
        '''
        UPDATE parking_spaces
        SET bind_customer_id=?, bind_vehicle_id=?, monthly_fee=?, effective_start=?, effective_end=?, status='已分配', updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        ''',
        (data.get('bind_customer_id'), data.get('bind_vehicle_id'), data.get('monthly_fee', 0), data.get('effective_start'), data.get('effective_end'), space_id)
    )
    return jsonify({'message': '车位分配成功'})


@parking_bp.route('/vehicles', methods=['GET'])
def list_vehicles():
    rows = query_all(
        '''
        SELECT v.*, c.name AS customer_name
        FROM vehicles v
        LEFT JOIN customers c ON v.customer_id = c.id
        ORDER BY v.id DESC
        '''
    )
    return jsonify(rows)


@parking_bp.route('/vehicles', methods=['POST'])
def create_vehicle():
    data = request.get_json()
    cur = execute(
        '''
        INSERT INTO vehicles (customer_id, plate_no, vehicle_type, color, status, monthly_start, monthly_end, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data.get('customer_id'), data.get('plate_no'), data.get('vehicle_type'), data.get('color'), data.get('status', '正常'),
            data.get('monthly_start'), data.get('monthly_end'), data.get('remark')
        )
    )
    return jsonify({'message': '车辆创建成功', 'id': cur.lastrowid})


@parking_bp.route('/records', methods=['GET'])
def list_records():
    rows = query_all(
        '''
        SELECT r.*, s.parking_code
        FROM parking_records r
        LEFT JOIN parking_spaces s ON r.parking_space_id = s.id
        ORDER BY r.id DESC
        '''
    )
    return jsonify(rows)


@parking_bp.route('/records', methods=['POST'])
def create_record():
    data = request.get_json()
    entry_time = data.get('entry_time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur = execute(
        '''
        INSERT INTO parking_records (plate_no, parking_space_id, entry_time, exit_time, duration_minutes, receivable_fee, received_fee, pay_status, pay_method, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data.get('plate_no'), data.get('parking_space_id'), entry_time, data.get('exit_time'), data.get('duration_minutes'),
            data.get('receivable_fee', 0), data.get('received_fee', 0), data.get('pay_status', '未支付'), data.get('pay_method'), data.get('source', '人工登记')
        )
    )
    return jsonify({'message': '临停记录创建成功', 'id': cur.lastrowid})


@parking_bp.route('/records/<int:record_id>/checkout', methods=['POST'])
def checkout_record(record_id):
    data = request.get_json() or {}
    record = query_one('SELECT * FROM parking_records WHERE id = ?', (record_id,))
    if not record:
        return jsonify({'message': '临停记录不存在'}), 404

    exit_time = data.get('exit_time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry_dt = datetime.strptime(record['entry_time'], '%Y-%m-%d %H:%M:%S')
    exit_dt = datetime.strptime(exit_time, '%Y-%m-%d %H:%M:%S')
    duration_minutes = max(int((exit_dt - entry_dt).total_seconds() // 60), 0)
    receivable_fee = calc_temp_fee(duration_minutes)
    received_fee = float(data.get('received_fee', receivable_fee))
    pay_status = '已支付' if received_fee >= receivable_fee else '异常'

    execute(
        '''
        UPDATE parking_records
        SET exit_time=?, duration_minutes=?, receivable_fee=?, received_fee=?, pay_status=?, pay_method=?
        WHERE id=?
        ''',
        (exit_time, duration_minutes, receivable_fee, received_fee, pay_status, data.get('pay_method', '扫码'), record_id)
    )
    return jsonify({'message': '临停结算成功', 'duration_minutes': duration_minutes, 'receivable_fee': receivable_fee, 'pay_status': pay_status})
