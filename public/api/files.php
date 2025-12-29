<?php
// public/api/files.php
header('Content-Type: application/json');

$directory = '../uploads';
$files = [];

if (is_dir($directory)) {
    $dirFiles = scandir($directory);
    foreach ($dirFiles as $file) {
        if ($file !== '.' && $file !== '..') {
            $filePath = $directory . '/' . $file;
            $files[] = [
                'name' => $file,
                'size' => filesize($filePath),
                'date' => date("Y-m-d H:i", filemtime($filePath))
            ];
        }
    }
}

// Sort by date descending (newest first)
usort($files, function($a, $b) {
    return strtotime($b['date']) - strtotime($a['date']);
});

echo json_encode($files);
