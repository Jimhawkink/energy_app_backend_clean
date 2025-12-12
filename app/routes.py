from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import User, Pump, PumpShift, SalesRecord, MpesaTransaction, UserRole, Shift
from datetime import datetime
import uuid
import time
import random

main = Blueprint('main', __name__)

# --- Helper Functions ---

def get_current_shift(pump_id):
    """Finds the currently open shift for a given pump."""
    return PumpShift.query.filter_by(pump_id=pump_id, is_closed=False).order_by(PumpShift.opening_time.desc()).first()

def get_user_role(user_id):
    """Gets the role name for a given user ID."""
    user = User.query.get(user_id)
    if user:
        return user.role.role_name
    return None

# --- Authentication Routes ---

@main.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        role_name = get_user_role(user.user_id)
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'user': {
                'user_id': user.user_id,
                'full_name': user.full_name,
                'username': user.username,
                'role': role_name
            }
        }), 200
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

# --- Pump and Shift Management Routes (Admin/Attendant) ---

@main.route('/api/pumps', methods=['GET'])
def get_pumps():
    pumps = Pump.query.filter_by(is_active=True).all()
    result = []
    for pump in pumps:
        current_shift = get_current_shift(pump.pump_id)
        result.append({
            'pump_id': pump.pump_id,
            'pump_no': pump.pump_no,
            'pump_name': pump.pump_name,
            'is_shift_open': current_shift is not None,
            'current_shift_id': current_shift.pump_shift_id if current_shift else None
        })
    return jsonify(result), 200

@main.route('/api/shifts', methods=['GET'])
def get_shifts():
    shifts = Shift.query.all()
    result = [{'shift_id': s.shift_id, 'shift_name': s.shift_name} for s in shifts]
    return jsonify(result), 200

@main.route('/api/shift/open', methods=['POST'])
def open_shift():
    data = request.get_json()
    pump_id = data.get('pump_id')
    shift_id = data.get('shift_id')
    attendant_id = data.get('attendant_id')
    opening_meter_reading = data.get('opening_meter_reading')

    if get_current_shift(pump_id):
        return jsonify({'status': 'error', 'message': 'Shift is already open for this pump.'}), 400

    new_shift = PumpShift(
        pump_id=pump_id,
        shift_id=shift_id,
        opening_attendant_id=attendant_id,
        opening_meter_reading=opening_meter_reading
    )
    db.session.add(new_shift)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Shift opened successfully',
        'pump_shift_id': new_shift.pump_shift_id
    }), 201

@main.route('/api/shift/close', methods=['POST'])
def close_shift():
    data = request.get_json()
    pump_shift_id = data.get('pump_shift_id')
    closing_attendant_id = data.get('closing_attendant_id')
    closing_meter_reading = data.get('closing_meter_reading')

    shift = PumpShift.query.get(pump_shift_id)

    if not shift or shift.is_closed:
        return jsonify({'status': 'error', 'message': 'Shift not found or already closed.'}), 404

    shift.closing_attendant_id = closing_attendant_id
    shift.closing_time = datetime.utcnow()
    shift.closing_meter_reading = closing_meter_reading
    shift.is_closed = True
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Shift closed successfully'}), 200

# --- Sales and M-Pesa Simulation Routes ---

@main.route('/api/mpesa/stk_push', methods=['POST'])
def stk_push_simulation():
    data = request.get_json()
    mobile_no = data.get('mobile_no')
    amount = data.get('amount')
    sale_id_no = data.get('sale_id_no')
    pump_shift_id = data.get('pump_shift_id')
    attendant_id = data.get('attendant_id')

    if not all([mobile_no, amount, sale_id_no, pump_shift_id, attendant_id]):
        return jsonify({'status': 'error', 'message': 'Missing required fields for STK Push.'}), 400

    # 1. Simulate STK Push Request
    checkout_request_id = str(uuid.uuid4())
    merchant_request_id = str(uuid.uuid4())
    
    # Simulate a successful request to M-Pesa API
    response_code = '0'
    response_description = 'Success. Request accepted for processing.'

    # 2. Log the M-Pesa Transaction Request
    mpesa_req = MpesaTransaction(
        mobile_no=mobile_no,
        amount=amount,
        request_time=datetime.utcnow(),
        checkout_request_id=checkout_request_id,
        merchant_request_id=merchant_request_id,
        response_code=response_code,
        response_description=response_description
    )
    db.session.add(mpesa_req)
    db.session.commit()

    # 3. Simulate the M-Pesa Callback (Payment Confirmation)
    # This would normally be a separate endpoint, but for simulation, we'll run it inline after a delay.
    time.sleep(current_app.config['MPESA_SIMULATION_DELAY'])

    # Randomly determine transaction outcome for simulation
    outcome = random.choice(['SUCCESS', 'INSUFFICIENT_FUNDS', 'CANCELLED', 'OTHER_ERROR'])

    if outcome == 'SUCCESS':
        result_code = '0'
        result_description = 'The transaction was successful.'
        mpesa_receipt_number = 'NF' + str(random.randint(100000, 999999))
        transaction_status = 'SUCCESS'
    elif outcome == 'INSUFFICIENT_FUNDS':
        result_code = '1001'
        result_description = 'The customer has insufficient funds in Mpesa account.'
        mpesa_receipt_number = None
        transaction_status = 'FAILED'
    elif outcome == 'CANCELLED':
        result_code = '1032'
        result_description = 'Failed cancelled by customer.'
        mpesa_receipt_number = None
        transaction_status = 'FAILED'
    else: # OTHER_ERROR
        result_code = '1000'
        result_description = 'An error occurred during the transaction.'
        mpesa_receipt_number = None
        transaction_status = 'FAILED'

    # 4. Update M-Pesa Transaction Log
    mpesa_req.result_code = result_code
    mpesa_req.result_description = result_description
    mpesa_req.mpesa_receipt_number = mpesa_receipt_number
    db.session.commit()

    # 5. Create Sales Record
    pump_shift = PumpShift.query.get(pump_shift_id)
    if not pump_shift:
        return jsonify({'status': 'error', 'message': 'Invalid pump shift ID.'}), 400

    new_sale = SalesRecord(
        sale_id_no=sale_id_no,
        pump_shift_id=pump_shift_id,
        pump_id=pump_shift.pump_id,
        attendant_id=attendant_id,
        amount=amount,
        customer_mobile_no=mobile_no,
        mpesa_transaction_code=mpesa_receipt_number,
        transaction_status=transaction_status
    )
    db.session.add(new_sale)
    db.session.commit()
    
    # Link the Mpesa transaction to the sales record
    mpesa_req.sale_id = new_sale.sale_id
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'STK Push initiated and transaction simulated.',
        'transaction_status': transaction_status,
        'result_description': result_description,
        'sale_id': new_sale.sale_id,
        'mpesa_receipt_number': mpesa_receipt_number
    }), 200

# --- Admin and Reporting Routes ---

@main.route('/api/admin/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_users():
    # Simplified user management for demonstration
    if request.method == 'GET':
        users = User.query.all()
        result = []
        for user in users:
            result.append({
                'user_id': user.user_id,
                'full_name': user.full_name,
                'username': user.username,
                'mobile_no': user.mobile_no,
                'role': user.role.role_name,
                'is_active': user.is_active
            })
        return jsonify(result), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        role = UserRole.query.filter_by(role_name=data.get('role')).first()
        if not role:
            return jsonify({'status': 'error', 'message': 'Invalid role name.'}), 400
            
        new_user = User(
            full_name=data.get('full_name'),
            username=data.get('username'),
            mobile_no=data.get('mobile_no'),
            role_id=role.role_id
        )
        new_user.set_password(data.get('password'))
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User created successfully', 'user_id': new_user.user_id}), 201

    # PUT and DELETE methods would be implemented here for a full solution

    return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405

@main.route('/api/reports/sales', methods=['GET'])
def get_sales_records():
    # Filtering and searching logic
    pump_id = request.args.get('pump_id', type=int)
    attendant_id = request.args.get('attendant_id', type=int)
    mobile_no = request.args.get('mobile_no')
    shift_id = request.args.get('shift_id', type=int)
    
    query = SalesRecord.query.join(PumpShift).join(User, SalesRecord.attendant_id == User.user_id).join(Pump).join(Shift)

    if pump_id:
        query = query.filter(SalesRecord.pump_id == pump_id)
    if attendant_id:
        query = query.filter(SalesRecord.attendant_id == attendant_id)
    if mobile_no:
        # Search by mobile number (partial match)
        query = query.filter(SalesRecord.customer_mobile_no.like(f'%{mobile_no}%'))
    if shift_id:
        query = query.filter(PumpShift.shift_id == shift_id)

    sales = query.order_by(SalesRecord.sale_time.desc()).all()
    
    result = []
    for sale in sales:
        result.append({
            'sale_id': sale.sale_id,
            'sale_id_no': sale.sale_id_no,
            'amount': float(sale.amount),
            'sale_time': sale.sale_time.isoformat(),
            'customer_mobile_no': sale.customer_mobile_no,
            'mpesa_transaction_code': sale.mpesa_transaction_code,
            'transaction_status': sale.transaction_status,
            'pump_no': sale.pump.pump_no,
            'pump_name': sale.pump.pump_name,
            'shift_name': sale.pump_shift.shift.shift_name,
            'attendant_name': sale.attendant.full_name
        })
        
    return jsonify(result), 200

# --- Utility Routes ---

@main.route('/api/status', methods=['GET'])
def status():
    return jsonify({'status': 'ok', 'message': 'Energy App Backend is running'}), 200

@main.route('/api/filters', methods=['GET'])
def get_filters():
    # Get all unique attendants who have made sales
    attendants = db.session.query(User.user_id, User.full_name).join(SalesRecord, User.user_id == SalesRecord.attendant_id).distinct().all()
    attendant_list = [{'id': a.user_id, 'name': a.full_name} for a in attendants]
    
    # Get all pumps
    pumps = Pump.query.all()
    pump_list = [{'id': p.pump_id, 'name': p.pump_name, 'no': p.pump_no} for p in pumps]
    
    # Get all shifts
    shifts = Shift.query.all()
    shift_list = [{'id': s.shift_id, 'name': s.shift_name} for s in shifts]
    
    return jsonify({
        'attendants': attendant_list,
        'pumps': pump_list,
        'shifts': shift_list
    }), 200
