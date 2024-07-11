from os import environ
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask import jsonify, request

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///db.sqlite")
    app.config['SQLALCHEMY_POOL_SIZE'] = 500  # 设置连接池的大小为500，这也间接地设置了最大连接数
    
    from spamoverflow.models import db
    from spamoverflow.models.customer import Customers
    from spamoverflow.models.email_domains import EmailDomains
    from spamoverflow.models.emails import Emails

    db.init_app(app)

    # Create the database tables
    with app.app_context():    
        # db.session.expire_all()
        db.create_all()
        db.session.commit()

    from .views.routes import api
    app.register_blueprint(api)

    #     # 全局404错误处理器
    # @app.errorhandler(404)
    # def global_page_not_found(error):
    #     requested_url = request.url
    #     return jsonify({"error": "请求的资源未找到", "url": requested_url}), 404

    return app