<?php
header('Content-Type: application/json');
$logDir = dirname(__DIR__) . '/logs';
if (!is_dir($logDir)) { mkdir($logDir, 0755, true); }
$logFile = $logDir . '/mpesa_' . date('Y-m-d') . '.log';
$input = file_get_contents('php://input');
file_put_contents($logFile, "TIMESTAMP: " . date('Y-m-d H:i:s') . " - " . $input . "\n", FILE_APPEND);
$mpesaResponse = json_decode($input, true);
if (!empty($mpesaResponse)) {
    $body = $mpesaResponse['Body']['stkCallback'] ?? [];
    $resultCode = $body['ResultCode'] ?? null;
    $transactionStatus = ($resultCode === 0) ? 'SUCCESS' : 'FAILED';
    $supabaseUrl = 'https://acqfnlizrkpfmogyxhtu.supabase.co/rest/v1';
    $supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjcWZubGl6cmtwZm1vZ3l4aHR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU0NjAxNTcsImV4cCI6MjA4MTAzNjE1N30.jOP8Hesw8ybi4ooRVgf8JiYyKsDtHTzDFuCfHS3PH6Y';
    $updateData = ['transaction_status' => $transactionStatus];
    $curl = curl_init($supabaseUrl . '/sales_records?id=eq.' . ($body['CheckoutRequestID'] ?? ''));
    curl_setopt_array($curl, [CURLOPT_RETURNTRANSFER => true, CURLOPT_CUSTOMREQUEST => 'PATCH', CURLOPT_POSTFIELDS => json_encode($updateData), CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'apikey: ' . $supabaseKey, 'Authorization: Bearer ' . $supabaseKey]]);
    curl_exec($curl);
    curl_close($curl);
}
http_response_code(200);
echo json_encode(['ResultCode' => 0]);
?>
