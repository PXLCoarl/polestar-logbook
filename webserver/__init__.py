from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from utilities import logger
from dotenv import load_dotenv
import os, random, string



db = SQLAlchemy()



def initialisation() -> None:
    if not os.path.exists('.env'):
        with open('.env', 'w') as file:
            secret_key = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(50))
            file.write(f"SECRET_KEY = {secret_key}\n")
            file.write(f"DB_PATH = instance/app.db\n")
            file.write(f"DB_URI = sqlite:///app.db\n")
            file.write(f"WEBSERVER_PORT = 31777\n")
        load_dotenv()
        logger.info("Created default configuration.")
    else:
        load_dotenv()
        logger.info("Loaded configuration.")
    
    if not os.path.exists('./webserver/maps'):
        os.mkdir('./webserver/maps')
        logger.info("Created maps folder.")
    else:
        logger.info("Found maps folder.")
        
        
def webserver() -> Flask:
    initialisation()
    app = Flask(__name__)
    key = os.getenv("SECRET_KEY")
    if key is None:
        logger.error("SECRET_KEY not found in environment variables.")
        raise RuntimeError("SECRET_KEY not found in environment variables.")
    
    db_uri = os.getenv("DB_URI")
    if db_uri is None:
        logger.error("DB_URI not found in environment variables.")
        raise RuntimeError("DB_URI not found in environment variables.")
    
    port = int(os.getenv("WEBSERVER_PORT"))
    if port is None:
        logger.error("WEBSERVER_PORT not found in environment variables.")
        raise RuntimeError("WEBSERVER_PORT not found in environment variables.")
    
    app.config['SECRET_KEY'] = key
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    from webserver.auth import auth
    app.register_blueprint(auth)
    from webserver.routes import routes
    app.register_blueprint(routes)
    from webserver.api import api
    app.register_blueprint(api, url_prefix='/api')
    
    with app.app_context():
        db.create_all()
    
    logger.info("Finished startup.")
    return app