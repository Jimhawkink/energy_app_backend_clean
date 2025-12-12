'''
from app import db, bcrypt
from datetime import datetime

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    mobile_no = db.Column(db.String(15), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('user_roles.role_id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    sales = db.relationship('SalesRecord', backref='attendant', lazy=True)
    opening_shifts = db.relationship('PumpShift', foreign_keys='PumpShift.opening_attendant_id', backref='opening_attendant', lazy=True)
    closing_shifts = db.relationship('PumpShift', foreign_keys='PumpShift.closing_attendant_id', backref='closing_attendant', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Pump(db.Model):
    __tablename__ = 'pumps'
    pump_id = db.Column(db.Integer, primary_key=True)
    pump_no = db.Column(db.String(10), unique=True, nullable=False)
    pump_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    shifts = db.relationship('PumpShift', backref='pump', lazy=True)
    sales = db.relationship('SalesRecord', backref='pump', lazy=True)

class Shift(db.Model):
    __tablename__ = 'shifts'
    shift_id = db.Column(db.Integer, primary_key=True)
    shift_name = db.Column(db.String(50), unique=True, nullable=False)
    
    pump_shifts = db.relationship('PumpShift', backref='shift', lazy=True)

class PumpShift(db.Model):
    __tablename__ = 'pump_shifts'
    pump_shift_id = db.Column(db.Integer, primary_key=True)
    pump_id = db.Column(db.Integer, db.ForeignKey('pumps.pump_id'), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.shift_id'), nullable=False)
    opening_attendant_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    opening_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    opening_meter_reading = db.Column(db.Numeric(10, 2), nullable=False)
    closing_attendant_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    closing_time = db.Column(db.DateTime, nullable=True)
    closing_meter_reading = db.Column(db.Numeric(10, 2), nullable=True)
    is_closed = db.Column(db.Boolean, default=False)
    
    sales = db.relationship('SalesRecord', backref='pump_shift', lazy=True)

class SalesRecord(db.Model):
    __tablename__ = 'sales_records'
    sale_id = db.Column(db.Integer, primary_key=True)
    sale_id_no = db.Column(db.String(50), unique=True, nullable=False)
    pump_shift_id = db.Column(db.Integer, db.ForeignKey('pump_shifts.pump_shift_id'), nullable=False)
    pump_id = db.Column(db.Integer, db.ForeignKey('pumps.pump_id'), nullable=False)
    attendant_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    sale_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    customer_mobile_no = db.Column(db.String(15), nullable=True)
    mpesa_transaction_code = db.Column(db.String(50), nullable=True)
    transaction_status = db.Column(db.String(50), nullable=False) # e.g., SUCCESS, PENDING, FAILED
    
    mpesa_transactions = db.relationship('MpesaTransaction', backref='sale', lazy=True)

class MpesaTransaction(db.Model):
    __tablename__ = 'mpesa_transactions'
    transaction_id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales_records.sale_id'), nullable=True)
    mobile_no = db.Column(db.String(15), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    request_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    checkout_request_id = db.Column(db.String(100), nullable=False)
    merchant_request_id = db.Column(db.String(100), nullable=False)
    response_code = db.Column(db.String(10), nullable=False)
    response_description = db.Column(db.Text)
    result_code = db.Column(db.String(10), nullable=True)
    result_description = db.Column(db.Text)
    mpesa_receipt_number = db.Column(db.String(50), nullable=True)

class Setting(db.Model):
    __tablename__ = 'settings'
    setting_key = db.Column(db.String(50), primary_key=True)
    setting_value = db.Column(db.String(255))

# Helper function to initialize the database with default data
def initialize_db(app):
    with app.app_context():
        db.create_all()
        
        # Check and insert default roles
        if not UserRole.query.filter_by(role_name='Admin').first():
            db.session.add_all([
                UserRole(role_name='Admin'),
                UserRole(role_name='Pump Attendant')
            ])
            db.session.commit()

        # Check and insert default shifts
        if not Shift.query.filter_by(shift_name='Day Shift').first():
            db.session.add_all([
                Shift(shift_name='Day Shift'),
                Shift(shift_name='Night Shift')
            ])
            db.session.commit()

        # Check and insert default pumps
        if not Pump.query.filter_by(pump_no='P1').first():
            db.session.add_all([
                Pump(pump_no='P1', pump_name='Pump One'),
                Pump(pump_no='P2', pump_name='Pump Two'),
                Pump(pump_no='P3', pump_name='Pump Three')
            ])
            db.session.commit()

        # Check and insert default Admin user
        if not User.query.filter_by(username='admin').first():
            admin_role = UserRole.query.filter_by(role_name='Admin').first()
            admin_user = User(
                full_name='System Administrator', 
                username='admin', 
                mobile_no='0700123456', 
                role_id=admin_role.role_id
            )
            admin_user.set_password('admin123') # Set a default password
            db.session.add(admin_user)
            db.session.commit()
            
        # Check and insert default Pump Attendant user
        if not User.query.filter_by(username='attendant1').first():
            attendant_role = UserRole.query.filter_by(role_name='Pump Attendant').first()
            attendant_user = User(
                full_name='John Doe', 
                username='attendant1', 
                mobile_no='0711223344', 
                role_id=attendant_role.role_id
            )
            attendant_user.set_password('pass123') # Set a default password
            db.session.add(attendant_user)
            db.session.commit()

        # Check and insert default settings
        default_settings = {
            'mpesa_till_number': '174379',
            'mpesa_consumer_key': 'mock_key',
            'mpesa_consumer_secret': 'mock_secret',
            'mpesa_passkey': 'mock_passkey'
        }
        for key, value in default_settings.items():
            if not Setting.query.filter_by(setting_key=key).first():
                db.session.add(Setting(setting_key=key, setting_value=value))
        db.session.commit()
'''
