/* public/js/app.js */
document.addEventListener('DOMContentLoaded', () => {
    const fileGrid = document.querySelector('.file-grid');
    const searchInput = document.querySelector('.search-bar input');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadModal = document.getElementById('uploadModal');
    const closeModal = document.querySelector('.close-modal');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const loadingSpinner = document.querySelector('.loading-spinner');

    let files = [];
    let currentLang = 'en';

    const translations = {
        en: {
            logo: "Kakomon Portal",
            upload_btn: "+ Upload New",
            hero_title: "Find Past Tests",
            hero_desc: "Access the collection of past exams and practice materials.",
            search_placeholder: "Search for subjects, years, or professors...",
            upload_title: "Upload File",
            upload_desc: "Share your past exams with others.",
            upload_area: "Click to browse or drag file here",
            upload_note: "Supported: PDF, Images, ZIP",
            no_files: "No files found.",
            failed_load: "Failed to load files.",
            upload_success: "Upload successful!",
            upload_failed: "Upload failed: "
        },
        ja: {
            logo: "過去問ポータル",
            upload_btn: "+ 新規アップロード",
            hero_title: "過去問を探す",
            hero_desc: "過去の試験問題や練習資料のコレクションにアクセスできます。",
            search_placeholder: "科目名、年度、教授名で検索...",
            upload_title: "ファイルをアップロード",
            upload_desc: "過去問をみんなと共有しましょう。",
            upload_area: "クリックして選択、またはドラッグ＆ドロップ",
            upload_note: "対応形式: PDF, 画像, ZIP",
            no_files: "ファイルが見つかりません。",
            failed_load: "ファイルの読み込みに失敗しました。",
            upload_success: "アップロード成功！",
            upload_failed: "アップロード失敗: "
        }
    };

    function setLanguage(lang) {
        // Fallback to en if lang not supported
        if (!translations[lang]) lang = 'en';
        currentLang = lang;
        const t = translations[lang];

        // Update Text Content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (t[key]) el.textContent = t[key];
        });

        // Update Placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (t[key]) el.placeholder = t[key];
        });

        // Re-render files if they exist to update any dynamic text depending on lang?
        // Currently file rendering doesn't look like it uses specific lang text except maybe error/empty messages.
        // But if we want date formatting to match locale, we might need to handle that.
    }

    // Detect Language
    const browserLang = navigator.language.slice(0, 2);
    setLanguage(browserLang === 'ja' ? 'ja' : 'en');


    // --- Navigation & Modal ---
    uploadBtn.addEventListener('click', () => {
        uploadModal.classList.add('active');
    });

    closeModal.addEventListener('click', () => {
        uploadModal.classList.remove('active');
    });

    uploadModal.addEventListener('click', (e) => {
        if (e.target === uploadModal) {
            uploadModal.classList.remove('active');
        }
    });

    // --- File Fetching ---
    async function fetchFiles() {
        try {
            const response = await fetch('/api/files.php');
            files = await response.json();
            renderFiles(files);
        } catch (error) {
            console.error('Error fetching files:', error);
            const t = translations[currentLang];
            fileGrid.innerHTML = `<p style="grid-column: 1/-1; text-align: center;">${t.failed_load}</p>`;
        }
    }

    function renderFiles(filesToRender) {
        fileGrid.innerHTML = '';
        const t = translations[currentLang];
        if (filesToRender.length === 0) {
            fileGrid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: #666;">${t.no_files}</p>`;
            return;
        }

        filesToRender.forEach(file => {
            const card = document.createElement('div');
            card.className = 'file-card';

            // Determine icon based on extension
            let icon = '📄';
            const ext = file.name.split('.').pop().toLowerCase();
            if (['jpg', 'jpeg', 'png', 'gif'].includes(ext)) icon = '🖼️';
            else if (['pdf'].includes(ext)) icon = '📕';
            else if (['zip', 'rar'].includes(ext)) icon = '📦';

            card.innerHTML = `
                <div class="file-icon">${icon}</div>
                <div class="file-info">
                    <h3>${file.name}</h3>
                </div>
                <div class="file-meta">
                    <span>${formatSize(file.size)}</span>
                    <span>${file.date}</span>
                </div>
            `;

            card.addEventListener('click', () => {
                window.open(`/uploads/${file.name}`, '_blank');
            });

            fileGrid.appendChild(card);
        });
    }

    function formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    // --- Search ---
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = files.filter(file => file.name.toLowerCase().includes(query));
        renderFiles(filtered);
    });

    // --- Upload ---
    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleUpload(fileInput.files[0]);
        }
    });

    async function handleUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        loadingSpinner.style.display = 'block';
        uploadArea.style.opacity = '0.5';

        try {
            const response = await fetch('/api/upload.php', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            const t = translations[currentLang];

            if (result.success) {
                // Refresh list
                await fetchFiles();
                uploadModal.classList.remove('active');
                alert(t.upload_success);
            } else {
                alert(t.upload_failed + result.message);
            }
        } catch (error) {
            const t = translations[currentLang];
            alert(t.upload_failed + error.message);
        } finally {
            loadingSpinner.style.display = 'none';
            uploadArea.style.opacity = '1';
            fileInput.value = ''; // Reset input
        }
    }

    // Init
    fetchFiles();
});
