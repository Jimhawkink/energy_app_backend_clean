--
-- Energy App Database Setup Script (MySQL)
--

-- 1. Database Creation
CREATE DATABASE IF NOT EXISTS Energy_db;
USE Energy_db;

-- 2. Table: user_roles (User Types)
-- Defines the different types of users in the system (e.g., Admin, Pump Attendant)
CREATE TABLE IF NOT EXISTS user_roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- Insert initial roles
INSERT INTO user_roles (role_name) VALUES
('Admin'),
('Pump Attendant');

-- 3. Table: users
-- Stores user information, linked to their role
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Store hashed passwords
    mobile_no VARCHAR(15) UNIQUE,
    role_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (role_id) REFERENCES user_roles(role_id)
);

-- Insert a default Admin user (password: admin123 - should be hashed in a real app)
-- For this setup script, we'll use a placeholder hash. In the Flask app, we'll use a proper hash.
INSERT INTO users (full_name, username, password_hash, mobile_no, role_id) VALUES
('System Administrator', 'admin', 'pbkdf2:sha256:600000$hV8zQ3yF$a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9', '0700123456', 1);

-- 4. Table: pumps
-- Stores information about each fuel pump
CREATE TABLE IF NOT EXISTS pumps (
    pump_id INT PRIMARY KEY AUTO_INCREMENT,
    pump_no VARCHAR(10) NOT NULL UNIQUE, -- e.g., P1, P2
    pump_name VARCHAR(50) NOT NULL, -- e.g., Pump One, Pump Two
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert initial pumps
INSERT INTO pumps (pump_no, pump_name) VALUES
('P1', 'Pump One'),
('P2', 'Pump Two'),
('P3', 'Pump Three');

-- 5. Table: shifts
-- Defines the types of shifts (Day/Night)
CREATE TABLE IF NOT EXISTS shifts (
    shift_id INT PRIMARY KEY AUTO_INCREMENT,
    shift_name VARCHAR(50) NOT NULL UNIQUE -- e.g., Day Shift, Night Shift
);

-- Insert initial shifts
INSERT INTO shifts (shift_name) VALUES
('Day Shift'),
('Night Shift');

-- 6. Table: pump_shifts
-- Records the opening and closing of shifts for each pump
CREATE TABLE IF NOT EXISTS pump_shifts (
    pump_shift_id INT PRIMARY KEY AUTO_INCREMENT,
    pump_id INT NOT NULL,
    shift_id INT NOT NULL,
    opening_attendant_id INT NOT NULL,
    opening_time DATETIME NOT NULL,
    opening_meter_reading DECIMAL(10, 2) NOT NULL,
    closing_attendant_id INT NULL,
    closing_time DATETIME NULL,
    closing_meter_reading DECIMAL(10, 2) NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (pump_id) REFERENCES pumps(pump_id),
    FOREIGN KEY (shift_id) REFERENCES shifts(shift_id),
    FOREIGN KEY (opening_attendant_id) REFERENCES users(user_id),
    FOREIGN KEY (closing_attendant_id) REFERENCES users(user_id)
);

-- 7. Table: sales_records
-- Main table for storing sales transactions
CREATE TABLE IF NOT EXISTS sales_records (
    sale_id INT PRIMARY KEY AUTO_INCREMENT,
    sale_id_no VARCHAR(50) NOT NULL UNIQUE, -- User-keyed or auto-generated sales ID
    pump_shift_id INT NOT NULL,
    pump_id INT NOT NULL,
    attendant_id INT NOT NULL,
    sale_time DATETIME NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    customer_mobile_no VARCHAR(15) NULL,
    mpesa_transaction_code VARCHAR(50) NULL,
    transaction_status VARCHAR(50) NOT NULL, -- e.g., SUCCESS, PENDING, FAILED
    FOREIGN KEY (pump_shift_id) REFERENCES pump_shifts(pump_shift_id),
    FOREIGN KEY (pump_id) REFERENCES pumps(pump_id),
    FOREIGN KEY (attendant_id) REFERENCES users(user_id)
);

-- 8. Table: settings
-- For general application settings (e.g., M-Pesa API configuration)
CREATE TABLE IF NOT EXISTS settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(255)
);

-- Insert placeholder settings for M-Pesa simulation
INSERT INTO settings (setting_key, setting_value) VALUES
('mpesa_till_number', '174379'),
('mpesa_consumer_key', 'mock_key'),
('mpesa_consumer_secret', 'mock_secret'),
('mpesa_passkey', 'mock_passkey');

-- 9. Table: mpesa_transactions
-- Detailed log of M-Pesa STK Push attempts
CREATE TABLE IF NOT EXISTS mpesa_transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    sale_id INT NULL,
    mobile_no VARCHAR(15) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    request_time DATETIME NOT NULL,
    checkout_request_id VARCHAR(100) NOT NULL,
    merchant_request_id VARCHAR(100) NOT NULL,
    response_code VARCHAR(10) NOT NULL,
    response_description TEXT,
    result_code VARCHAR(10) NULL,
    result_description TEXT NULL,
    mpesa_receipt_number VARCHAR(50) NULL,
    FOREIGN KEY (sale_id) REFERENCES sales_records(sale_id)
);
