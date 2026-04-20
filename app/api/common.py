from flask import Blueprint, jsonify
from ..db import query_all

common_bp = Blueprint('common', __name__)


@common_bp.route('/api/overview')
def overview():
    customer_count = query_all('SELECT COUNT(*) AS total FROM customers')[0]['total']
    unit_count = query_all('SELECT COUNT(*) AS total FROM property_units')[0]['total']
    due_bills = query_all("SELECT COUNT(*) AS total FROM rent_bills WHERE amount_outstanding > 0")[0]['total']
    occupied_spaces = query_all("SELECT COUNT(*) AS total FROM parking_spaces WHERE status = '已分配'")[0]['total']
    open_repairs = query_all("SELECT COUNT(*) AS total FROM repair_orders WHERE status NOT IN ('已完成', '已关闭')")[0]['total']

    return jsonify({
        'customerCount': customer_count,
        'unitCount': unit_count,
        'dueBills': due_bills,
        'occupiedSpaces': occupied_spaces,
        'openRepairs': open_repairs,
    })


@common_bp.route('/api/options')
def options():
    return jsonify({
        'customerTypes': ['业主', '租户'],
        'subjectTypes': ['个人', '企业'],
        'customerStatuses': ['正常', '在租', '已退租', '失效'],
        'unitTypes': ['办公', '商铺', '其他'],
        'leaseStatuses': ['空置', '已出租', '自用', '停用'],
        'billStatuses': ['待支付', '部分支付', '已支付', '已逾期', '已核销'],
        'billTypes': ['租金', '押金', '停车费', '其他'],
        'paymentMethods': ['现金', '转账', '微信', '支付宝', '扫码', '其他'],
        'parkingTypes': ['固定车位', '月租车位', '临停车位', '充电车位'],
        'parkingStatuses': ['空闲', '已分配', '停用', '占用'],
        'vehicleTypes': ['燃油车', '新能源车', '其他'],
        'repairTypes': ['水电', '空调', '装修', '公共设施', '其他'],
        'repairPriorities': ['紧急', '高', '中', '低'],
        'repairStatuses': ['待受理', '已派单', '处理中', '待确认', '已完成', '已关闭'],
    })
