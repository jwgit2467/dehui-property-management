from flask import Blueprint, jsonify, request
from ..db import execute, query_all, query_one

customers_bp = Blueprint('customers', __name__)


@customers_bp.route('', methods=['GET'])
def list_customers():
    keyword = request.args.get('keyword', '').strip()
    sql = '''
    SELECT c.*, p.unit_code, p.building_no
    FROM customers c
    LEFT JOIN property_units p ON p.owner_customer_id = c.id OR p.tenant_customer_id = c.id
    '''
    params = []
    if keyword:
        sql += '''
        WHERE c.name LIKE ? OR c.phone LIKE ? OR IFNULL(c.contact_person, '') LIKE ? OR IFNULL(p.unit_code, '') LIKE ?
        '''
        params = [f'%{keyword}%'] * 4
    sql += ' ORDER BY c.id DESC'
    return jsonify(query_all(sql, params))


@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = query_one('SELECT * FROM customers WHERE id = ?', (customer_id,))
    units = query_all('SELECT * FROM property_units WHERE owner_customer_id = ? OR tenant_customer_id = ?', (customer_id, customer_id))
    vehicles = query_all('SELECT * FROM vehicles WHERE customer_id = ?', (customer_id,))
    bills = query_all('SELECT * FROM rent_bills WHERE customer_id = ? ORDER BY id DESC', (customer_id,))
    repairs = query_all('SELECT * FROM repair_orders WHERE customer_id = ? ORDER BY id DESC', (customer_id,))
    return jsonify({'customer': customer, 'units': units, 'vehicles': vehicles, 'bills': bills, 'repairs': repairs})


@customers_bp.route('', methods=['POST'])
def create_customer():
    data = request.get_json()
    cur = execute(
        '''
        INSERT INTO customers (customer_type, subject_type, name, contact_person, phone, id_no, email, address, status, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data.get('customer_type'), data.get('subject_type'), data.get('name'), data.get('contact_person'),
            data.get('phone'), data.get('id_no'), data.get('email'), data.get('address'), data.get('status', '正常'), data.get('remark')
        )
    )

    if data.get('unit_id'):
        bind_customer_to_unit(data['unit_id'], cur.lastrowid, data.get('customer_type'))

    return jsonify({'message': '客户创建成功', 'id': cur.lastrowid})


@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json()
    execute(
        '''
        UPDATE customers
        SET customer_type=?, subject_type=?, name=?, contact_person=?, phone=?, id_no=?, email=?, address=?, status=?, remark=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        ''',
        (
            data.get('customer_type'), data.get('subject_type'), data.get('name'), data.get('contact_person'),
            data.get('phone'), data.get('id_no'), data.get('email'), data.get('address'), data.get('status'), data.get('remark'), customer_id
        )
    )

    if data.get('unit_id'):
        bind_customer_to_unit(data['unit_id'], customer_id, data.get('customer_type'))

    return jsonify({'message': '客户更新成功'})


@customers_bp.route('/units', methods=['GET'])
def list_units():
    units = query_all(
        '''
        SELECT p.*, o.name AS owner_name, t.name AS tenant_name
        FROM property_units p
        LEFT JOIN customers o ON p.owner_customer_id = o.id
        LEFT JOIN customers t ON p.tenant_customer_id = t.id
        ORDER BY p.id DESC
        '''
    )
    return jsonify(units)


@customers_bp.route('/units', methods=['POST'])
def create_unit():
    data = request.get_json()
    cur = execute(
        '''
        INSERT INTO property_units (unit_code, building_no, floor_no, unit_type, area, usable_area, owner_customer_id, tenant_customer_id, lease_status, delivery_status, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data.get('unit_code'), data.get('building_no'), data.get('floor_no'), data.get('unit_type'), data.get('area'), data.get('usable_area'),
            data.get('owner_customer_id'), data.get('tenant_customer_id'), data.get('lease_status'), data.get('delivery_status'), data.get('remark')
        )
    )
    return jsonify({'message': '房源创建成功', 'id': cur.lastrowid})


def bind_customer_to_unit(unit_id, customer_id, customer_type):
    if customer_type == '业主':
        execute('UPDATE property_units SET owner_customer_id = ?, updated_at=CURRENT_TIMESTAMP WHERE id = ?', (customer_id, unit_id))
    elif customer_type == '租户':
        execute('UPDATE property_units SET tenant_customer_id = ?, lease_status = ?, updated_at=CURRENT_TIMESTAMP WHERE id = ?', (customer_id, '已出租', unit_id))
