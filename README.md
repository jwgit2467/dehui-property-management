# 德汇创新中心物业管理小程序

基于 Flask + SQLite + H5 的轻量级物业管理系统。

## 技术栈

- **后端**：Python Flask + SQLite（轻量优先，快速可运行）
- **前端**：原生 HTML5 + JavaScript（响应式，适配浏览器和微信内置浏览器）
- **无外部依赖**：SQLite 为内置数据库，无需安装 MySQL/PostgreSQL

## 项目结构

```
workspace-dev/
├── app/
│   ├── __init__.py      # Flask 工厂函数
│   ├── db.py            # SQLite 数据库操作（连接、查询、初始化、种子数据）
│   └── api/
│       ├── common.py    # 概览统计 / 数据字典接口
│       ├── customers.py # 客户管理 API
│       ├── rent.py      # 租金收缴 API
│       ├── parking.py   # 停车位管理 API
│       └── repairs.py   # 报修管理 API
├── static/
│   ├── css/style.css    # 全局样式
│   ├── js/common.js     # 公共 JS 工具函数
│   ├── index.html       # 首页（系统概览）
│   ├── customers.html   # 客户管理页面
│   ├── rent.html        # 租金收缴页面
│   ├── parking.html     # 停车位管理页面
│   └── repairs.html     # 报修管理页面
├── data/                 # SQLite 数据库文件存放目录（自动创建）
├── schema.sql            # 数据库表结构（9张表）
├── run.py               # 启动脚本（自动初始化数据库）
├── requirements.txt     # Python 依赖
└── README.md
```

## 数据库结构（9张表）

| 表名 | 说明 | 主要关联 |
|---|---|---|
| `customers` | 客户档案（业主/租户） | → property_units, rent_bills, vehicles, repair_orders |
| `property_units` | 房屋/商铺台账 | → customers（业主/租户） |
| `rent_bills` | 租金账单 | → customers, property_units |
| `payment_records` | 支付记录 | → rent_bills, customers |
| `parking_spaces` | 停车位台账 | → customers, vehicles |
| `vehicles` | 车辆档案 | → customers |
| `parking_records` | 临停记录 | → parking_spaces |
| `repair_orders` | 报修单 | → customers, property_units |
| `repair_logs` | 报修处理记录 | → repair_orders |

> 初始化时自动插入 3 条客户、3 条房源、2 条账单、1 条支付记录、3 个车位、2 辆车辆、2 条临停记录、2 条报修单（带处理日志）的演示数据。

## 功能清单

### 1. 客户管理
- 客户列表 / 搜索 / 筛选（类型/状态）
- 新增客户（业主/租户、个人/企业）
- 编辑客户信息
- 关联房源绑定
- 查看客户详情（关联房源、账单、车辆、报修）

### 2. 租金收缴
- 账单列表 / 搜索
- **按面积×单价自动生成账单**（输入单价后实时预览金额）
- 缴费登记（自动更新账单状态和欠费金额）
- 支付记录查询
- 欠费账单列表 / 标记已提醒

### 3. 停车位管理
- 车位列表（支持搜索：编号/客户/车牌）
- 新增车位（支持固定/月租/临停/充电类型）
- **月租分配**（绑定客户+车辆+有效期+月租费）
- 临停登记（入场记录）
- **出场结算**（自动按 30分钟内免费、超时 5元/小时 计算费用）
- 车辆管理

### 4. 报修管理
- 报修列表 / 搜索
- 新增报修单（提交人/类型/优先级/描述）
- **工单详情页**（展示完整信息 + 处理记录时间线）
- **状态流转**（待受理→已派单→处理中→待确认→已完成→已关闭）
- 状态更新 + 操作记录自动写入日志

## 如何运行

### 前置条件
- Python 3.8+

### 步骤

```bash
# 1. 进入项目目录
cd /home/mdjw/.openclaw/workspace-dev/

# 2. 安装依赖（仅 Flask）
pip install -r requirements.txt

# 3. 运行（自动创建数据库并插入演示数据）
python run.py
```

运行后访问：**http://localhost:5000**

### 演示账号
系统无登录验证，演示数据如下：

| 客户 | 类型 | 说明 |
|---|---|---|
| 德汇资产管理有限公司 | 业主 | 示例业主 |
| 创新科技有限公司 | 租户 | 在租，含欠费账单 |
| 张晨 | 租户（个人） | 在租，含欠费账单 |

## 接口一览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/overview` | 概览统计数据 |
| GET | `/api/options` | 所有下拉选项字典 |
| GET | `/api/customers` | 客户列表 |
| POST | `/api/customers` | 新增客户 |
| GET | `/api/customers/<id>` | 客户详情（含关联） |
| PUT | `/api/customers/<id>` | 更新客户 |
| GET | `/api/customers/units` | 房源列表 |
| POST | `/api/customers/units` | 新增房源 |
| GET | `/api/rent/bills` | 账单列表 |
| POST | `/api/rent/bills` | 新增账单 |
| POST | `/api/rent/generate` | 按面积×单价生成账单 |
| GET | `/api/rent/payments` | 支付记录列表 |
| POST | `/api/rent/payments` | 缴费登记 |
| GET | `/api/rent/reminders` | 欠费提醒列表 |
| POST | `/api/rent/reminders/<id>` | 标记已提醒 |
| GET | `/api/parking/spaces` | 车位列表 |
| POST | `/api/parking/spaces` | 新增车位 |
| POST | `/api/parking/spaces/<id>/assign` | 分配车位 |
| GET | `/api/parking/vehicles` | 车辆列表 |
| POST | `/api/parking/vehicles` | 新增车辆 |
| GET | `/api/parking/records` | 临停记录列表 |
| POST | `/api/parking/records` | 临停登记（入场） |
| POST | `/api/parking/records/<id>/checkout` | 出场结算 |
| GET | `/api/repairs/orders` | 报修列表 |
| POST | `/api/repairs/orders` | 新增报修单 |
| GET | `/api/repairs/orders/<id>` | 报修详情（含日志） |
| POST | `/api/repairs/orders/<id>/status` | 更新工单状态 |

## 微信小程序 / 公众号适配说明

- 前端为纯 HTML5，可直接内嵌于微信内置浏览器
- 如需打包为微信小程序：可将 `/static/` 下的 HTML 文件转换为小程序 `WXML/WXSS/JS` 格式，API 接口保持不变
- 微信公众号：将 HTML 页面部署至域名为公众号安全域名即可通过菜单跳转访问

## 后续可扩展方向

- 登录与权限体系（管理员 / 财务 / 客服 / 业主 / 租户）
- 合同管理模块
- 物业费 / 水电费账单
- 微信模板消息推送（欠费提醒、报修进度）
- 财务报表导出（Excel/PDF）
- 数据分析看板
