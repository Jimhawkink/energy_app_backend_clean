from app import create_app, db
from app.models import initialize_db

app = create_app()

if __name__ == '__main__':
    # Initialize the database with default data
    initialize_db(app)
    
    # Run the Flask application
    # The host is set to '0.0.0.0' to make it accessible from outside the sandbox
    app.run(host='0.0.0.0', port=5000, debug=True)
