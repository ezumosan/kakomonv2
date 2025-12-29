<?php
// public/api/upload.php
header('Content-Type: application/json');

$response = ['success' => false, 'message' => '', 'debug' => $_FILES];

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    $response['message'] = 'Invalid request method';
    echo json_encode($response);
    exit;
}

if (!isset($_FILES['file'])) {
    $response['message'] = 'No file uploaded';
    echo json_encode($response);
    exit;
}

$file = $_FILES['file'];
$uploadDir = '../uploads/';

// Validate errors
if ($file['error'] !== UPLOAD_ERR_OK) {
    $response['message'] = 'Upload error code: ' . $file['error'];
    echo json_encode($response);
    exit;
}

// Ensure directory exists
if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}

// Sanitize filename
$filename = basename($file['name']);
$filename = preg_replace('/[^a-zA-Z0-9._-]/', '', $filename);
$targetPath = $uploadDir . $filename;

// Check if file already exists
if (file_exists($targetPath)) {
    $pathInfo = pathinfo($filename);
    $filename = $pathInfo['filename'] . '_' . time() . '.' . $pathInfo['extension'];
    $targetPath = $uploadDir . $filename;
}

// Move file
if (move_uploaded_file($file['tmp_name'], $targetPath)) {
    $response['success'] = true;
    $response['message'] = 'File uploaded successfully';
    $response['file'] = $filename;
} else {
    $response['message'] = 'Failed to move uploaded file';
}

echo json_encode($response);
