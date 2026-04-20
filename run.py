from app import create_app
from app.db import close_db, init_db, seed_demo_data

app = create_app()
app.teardown_appcontext(close_db)

if __name__ == '__main__':
    init_db()
    seed_demo_data()
    app.run(host='0.0.0.0', port=5000, debug=False)
