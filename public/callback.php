<?php
// M-Pesa STK Push Callback Handler
// This file receives callbacks from M-Pesa after STK Push transactions

header('Content-Type: application/json');
http_response_code(200);

// Log directory
$logDir = dirname(__DIR__) . '/logs';
if (!is_dir($logDir)) {
    mkdir($logDir, 0755, true);
}

$logFile = $logDir . '/mpesa_' . date('Y-m-d') . '.log';

// Get raw input from M-Pesa
$input = file_get_contents('php://input');

// Log the raw callback
file_put_contents($logFile, "\n" . str_repeat("=", 80) . "\n", FILE_APPEND);
file_put_contents($logFile, "TIMESTAMP: " . date('Y-m-d H:i:s') . "\n", FILE_APPEND);
file_put_contents($logFile, "RAW INPUT:\n" . $input . "\n", FILE_APPEND);

// Decode JSON
$mpesaResponse = json_decode($input, true);

if (!empty($mpesaResponse)) {
    try {
        // Extract callback data
        $body = $mpesaResponse['Body']['stkCallback'] ?? [];
        $resultCode = $body['ResultCode'] ?? null;
        $checkoutRequestID = $body['CheckoutRequestID'] ?? null;
        $merchantRequestID = $body['MerchantRequestID'] ?? null;
        
        file_put_contents($logFile, "PARSED DATA:\n", FILE_APPEND);
        file_put_contents($logFile, "  Result Code: $resultCode\n", FILE_APPEND);
        file_put_contents($logFile, "  Checkout Request ID: $checkoutRequestID\n", FILE_APPEND);
        
        // Determine transaction status
        $transactionStatus = 'PENDING';
        $mpesaReceiptNumber = null;
        $amount = null;
        $phoneNumber = null;
        
        if ($resultCode === 0) {
            $transactionStatus = 'SUCCESS';
            file_put_contents($logFile, "  Status: SUCCESS\n", FILE_APPEND);
            
            // Extract metadata
            $callbackMetadata = $body['CallbackMetadata']['Item'] ?? [];
            foreach ($callbackMetadata as $item) {
                $name = $item['Name'] ?? '';
                $value = $item['Value'] ?? '';
                
                if ($name === 'MpesaReceiptNumber') {
                    $mpesaReceiptNumber = $value;
                    file_put_contents($logFile, "  Receipt: $mpesaReceiptNumber\n", FILE_APPEND);
                } elseif ($name === 'Amount') {
                    $amount = $value;
                    file_put_contents($logFile, "  Amount: $amount\n", FILE_APPEND);
                } elseif ($name === 'PhoneNumber') {
                    $phoneNumber = $value;
                    file_put_contents($logFile, "  Phone: $phoneNumber\n", FILE_APPEND);
                }
            }
        } else {
            // Handle error codes
            switch ($resultCode) {
                case 1032:
                    $transactionStatus = 'CANCELLED';
                    file_put_contents($logFile, "  Status: CANCELLED by user\n", FILE_APPEND);
                    break;
                case 1037:
                    $transactionStatus = 'TIMEOUT';
                    file_put_contents($logFile, "  Status: TIMEOUT\n", FILE_APPEND);
                    break;
                case 1:
                    $transactionStatus = 'INSUFFICIENT_FUNDS';
                    file_put_contents($logFile, "  Status: INSUFFICIENT FUNDS\n", FILE_APPEND);
                    break;
                default:
                    $transactionStatus = 'FAILED';
                    file_put_contents($logFile, "  Status: FAILED\n", FILE_APPEND);
            }
        }
        
        // Update Supabase database
        $supabaseUrl = getenv('SUPABASE_URL') ?: 'https://acqfnlizrkpfmogyxhtu.supabase.co/rest/v1';
        $supabaseKey = getenv('SUPABASE_KEY') ?: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjcWZubGl6cmtwZm1vZ3l4aHR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU0NjAxNTcsImV4cCI6MjA4MTAzNjE1N30.jOP8Hesw8ybi4ooRVgf8JiYyKsDtHTzDFuCfHS3PH6Y';
        
        $updateData = [
            'transaction_status' => $transactionStatus,
            'mpesa_transaction_code' => $mpesaReceiptNumber ?? null,
            'checkout_request_id' => $checkoutRequestID
        ];
        
        // Make request to Supabase
        $url = "$supabaseUrl/sales_records?checkout_request_id=eq.$checkoutRequestID";
        
        $curl = curl_init();
        curl_setopt_array($curl, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CUSTOMREQUEST => 'PATCH',
            CURLOPT_POSTFIELDS => json_encode($updateData),
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'apikey: ' . $supabaseKey,
                'Authorization: Bearer ' . $supabaseKey,
                'Prefer: return=representation'
            ],
            CURLOPT_TIMEOUT => 10
        ]);
        
        $response = curl_exec($curl);
        $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        curl_close($curl);
        
        file_put_contents($logFile, "DATABASE UPDATE:\n", FILE_APPEND);
        file_put_contents($logFile, "  URL: $url\n", FILE_APPEND);
        file_put_contents($logFile, "  HTTP Code: $httpCode\n", FILE_APPEND);
        file_put_contents($logFile, "  Response: $response\n", FILE_APPEND);
        
    } catch (Exception $e) {
        file_put_contents($logFile, "ERROR: " . $e->getMessage() . "\n", FILE_APPEND);
    }
}

// Always return success to M-Pesa
file_put_contents($logFile, "RESPONSE: Sent success to M-Pesa\n", FILE_APPEND);
echo json_encode([
    'ResultCode' => 0,
    'ResultDesc' => 'Accepted'
]);
?>