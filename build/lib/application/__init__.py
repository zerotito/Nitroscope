from flask import Flask
from flask_login import LoginManager
from flask_session import Session

# Globally accessible libraries
login_manager = LoginManager()
sess = Session()

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)

    # Application Configuration
    app.config.from_object('application.config.Config')

    # Initialize Plugins
    #login_manager.init_app(app)
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
    sess.init_app(app)

    with app.app_context():
        # Importing Routes
        from application.projects.na import na_routes


        # Import parts of our application
        app.register_blueprint(na_routes.na_bp, url_prefix='/na')

        app.url_map
        return app
