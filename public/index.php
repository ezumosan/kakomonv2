<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kakomon Portal</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    
    <div class="container">
        <header>
            <div class="logo">
                📚 <span data-i18n="logo">Kakomon Portal</span>
            </div>
            <button id="uploadBtn" class="btn-primary" data-i18n="upload_btn">
                + Upload New
            </button>
        </header>

        <section class="hero">
            <h1 data-i18n="hero_title">Find Past Tests</h1>
            <p data-i18n="hero_desc">Access the collection of past exams and practice materials.</p>
            
            <div class="search-bar">
                <input type="text" placeholder="Search for subjects, years, or professors..." data-i18n-placeholder="search_placeholder">
            </div>
        </section>

        <main class="file-grid">
            <!-- Files will be injected here by JS -->
        </main>
    </div>

    <!-- Upload Modal -->
    <div id="uploadModal" class="modal">
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <h2 style="margin-bottom: 1rem;" data-i18n="upload_title">Upload File</h2>
            <p style="color: #666; margin-bottom: 1rem;" data-i18n="upload_desc">Share your past exams with others.</p>
            
            <div id="uploadArea" class="upload-area">
                <p data-i18n="upload_area">Click to browse or drag file here</p>
                <input type="file" id="fileInput" hidden>
            </div>
            
            <div class="loading-spinner"></div>
            
            <p style="font-size: 0.8rem; color: #999; text-align: center;" data-i18n="upload_note">Supported: PDF, Images, ZIP</p>
        </div>
    </div>

    <script src="/js/app.js"></script>
</body>
</html>
