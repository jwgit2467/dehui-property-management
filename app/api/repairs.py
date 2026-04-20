from datetime import datetime
from flask import Blueprint, jsonify, request
from ..db import execute, query_all, query_one

repairs_bp = Blueprint('repairs', __name__)


@repairs_bp.route('/orders', methods=['GET'])
def list_orders():
    keyword = request.args.get('keyword', '').strip()
    sql = '''
    SELECT r.*, c.name AS customer_name, p.unit_code
    FROM repair_orders r
    LEFT JOIN customers c ON r.customer_id = c.id
    LEFT JOIN property_units p ON r.unit_id = p.id
    '''
    params = []
    if keyword:
        sql += ' WHERE r.repair_no LIKE ? OR r.title LIKE ? OR IFNULL(c.name, "") LIKE ? OR IFNULL(p.unit_code, "") LIKE ? '
        params = [f'%{keyword}%'] * 4
    sql += ' ORDER BY r.id DESC'
    return jsonify(query_all(sql, params))


@repairs_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    repair_no = data.get('repair_no') or f"RP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    cur = execute(
        '''
        INSERT INTO repair_orders (repair_no, customer_id, unit_id, repair_type, title, content, image_urls, priority, status, source,
        reported_at, accepted_at, assigned_to, completed_at, customer_feedback, satisfaction_score, close_reason, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            repair_no, data.get('customer_id'), data.get('unit_id'), data.get('repair_type'), data.get('title'), data.get('content'),
            data.get('image_urls', ''), data.get('priority', '中'), data.get('status', '待受理'), data.get('source', 'Web'),
            data.get('reported_at') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data.get('accepted_at'), data.get('assigned_to'),
            data.get('completed_at'), data.get('customer_feedback', ''), data.get('satisfaction_score'), data.get('close_reason', ''), data.get('remark', '')
        )
    )
    log_action(cur.lastrowid, '提交', data.get('operator_id', 'system'), data.get('operator_role', '客户'), data.get('content', '提交报修'))
    return jsonify({'message': '报修单创建成功', 'id': cur.lastrowid, 'repair_no': repair_no})


@repairs_bp.route('/orders/<int:repair_id>', methods=['GET'])
def get_order(repair_id):
    order = query_one('SELECT * FROM repair_orders WHERE id = ?', (repair_id,))
    logs = query_all('SELECT * FROM repair_logs WHERE repair_id = ? ORDER BY id ASC', (repair_id,))
    return jsonify({'order': order, 'logs': logs})


@repairs_bp.route('/orders/<int:repair_id>/status', methods=['POST'])
def update_status(repair_id):
    data = request.get_json()
    status = data.get('status')
    accepted_at = data.get('accepted_at')
    completed_at = data.get('completed_at')

    if status == '处理中' and not accepted_at:
        accepted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if status in ['已完成', '已关闭'] and not completed_at:
        completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    execute(
        '''
        UPDATE repair_orders
        SET status=?, accepted_at=COALESCE(?, accepted_at), assigned_to=COALESCE(?, assigned_to), completed_at=COALESCE(?, completed_at),
            customer_feedback=COALESCE(?, customer_feedback), satisfaction_score=COALESCE(?, satisfaction_score),
            close_reason=COALESCE(?, close_reason), remark=COALESCE(?, remark)
        WHERE id=?
        ''',
        (
            status, accepted_at, data.get('assigned_to'), completed_at, data.get('customer_feedback'),
            data.get('satisfaction_score'), data.get('close_reason'), data.get('remark'), repair_id
        )
    )
    log_action(repair_id, data.get('action', '更新'), data.get('operator_id', 'admin'), data.get('operator_role', '物业'), data.get('action_content', status))
    return jsonify({'message': '工单状态更新成功'})


@repairs_bp.route('/logs', methods=['POST'])
def add_log():
    data = request.get_json()
    log_id = log_action(data.get('repair_id'), data.get('action'), data.get('operator_id'), data.get('operator_role'), data.get('action_content'), data.get('attachment_urls', ''))
    return jsonify({'message': '处理记录添加成功', 'log_id': log_id})


@repairs_bp.route('/pending', methods=['GET'])
def pending_orders():
    rows = query_all("SELECT * FROM repair_orders WHERE status NOT IN ('已完成', '已关闭') ORDER BY reported_at ASC")
    return jsonify(rows)


def log_action(repair_id, action, operator_id, operator_role, action_content, attachment_urls=''):
    cur = execute(
        '''
        INSERT INTO repair_logs (repair_id, action, operator_id, operator_role, action_content, attachment_urls)
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (repair_id, action, operator_id, operator_role, action_content, attachment_urls)
    )
    return cur.lastrowid
