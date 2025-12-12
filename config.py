'''
import os

class Config:
    # Database Configuration
    # NOTE: The sandbox environment does not have a persistent MySQL server.
    # For demonstration, we will use a local SQLite database first,
    # but the models are designed for MySQL.
    # The user will need to replace this with their actual MySQL connection string.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///energy_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret Key for session management and security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key_for_development'
    
    # M-Pesa Simulation Settings (Placeholders)
    MPESA_TILL_NUMBER = '174379'
    MPESA_CONSUMER_KEY = 'mock_key'
    MPESA_CONSUMER_SECRET = 'mock_secret'
    MPESA_PASSKEY = 'mock_passkey'
    
    # Simulation delay for M-Pesa STK Push
    MPESA_SIMULATION_DELAY = 5 # seconds
'''
