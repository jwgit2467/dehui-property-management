from flask import Flask
from .db import init_db, seed_demo_data
from .api.customers import customers_bp
from .api.rent import rent_bp
from .api.parking import parking_bp
from .api.repairs import repairs_bp
from .api.common import common_bp


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['JSON_AS_ASCII'] = False

    app.register_blueprint(common_bp)
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(rent_bp, url_prefix='/api/rent')
    app.register_blueprint(parking_bp, url_prefix='/api/parking')
    app.register_blueprint(repairs_bp, url_prefix='/api/repairs')

    @app.route('/')
    def home():
        return app.send_static_file('index.html')

    @app.route('/customers')
    def customers_page():
        return app.send_static_file('customers.html')

    @app.route('/rent')
    def rent_page():
        return app.send_static_file('rent.html')

    @app.route('/parking')
    def parking_page():
        return app.send_static_file('parking.html')

    @app.route('/repairs')
    def repairs_page():
        return app.send_static_file('repairs.html')

    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        seed_demo_data()
        print('数据库初始化完成。')

    return app
