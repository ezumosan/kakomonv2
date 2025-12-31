/* public/js/app.js */
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const fileGrid = document.querySelector('.file-grid');
    const searchInput = document.querySelector('.search-bar input');
    const tagButtons = document.querySelectorAll('.tag-filters .tag');

    // Upload Modal
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadModal = document.getElementById('uploadModal');
    const closeModal = document.querySelector('.close-modal');
    const uploadForm = document.getElementById('uploadForm');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const selectedFileName = document.getElementById('selectedFileName');

    // Sidebar
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    let files = [];
    let currentFilterTag = 'all';

    // --- State & i18n ---
    const translations = {
        en: {
            logo: "Kakomon",
            upload_btn: "+ Upload",
            hero_title: "Find Past Tests",
            hero_desc: "Access the collection of past exams and practice materials.",
            search_placeholder: "Search for subjects, years...",
            upload_title: "Upload File",
            upload_area: "Click to browse or drag file here",
            search_all: "All",
            search_japanese: "Japanese",
            search_english: "English",
            search_math: "Math",
            search_science: "Science",
            search_social: "Social Studies"
        },
        ja: {
            logo: "過去問",
            upload_btn: "+ アップロード",
            hero_title: "過去問を探す",
            hero_desc: "過去の試験問題や練習資料にアクセスしよう。",
            search_placeholder: "科目や年度を検索...",
            upload_title: "ファイルをアップロード",
            upload_area: "クリックしてファイルを選択",
            search_all: "すべて",
            search_japanese: "国語",
            search_english: "英語",
            search_math: "数学",
            search_science: "理科",
            search_social: "社会"
        }
    };

    const langSelect = document.getElementById('langSelect');

    function updateLanguage(lang) {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.dataset.i18n;
            if (translations[lang][key]) {
                el.textContent = translations[lang][key];
            }
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (translations[lang][key]) {
                el.placeholder = translations[lang][key];
            }
        });

        // Update tag filter text if they have specific mapping, or add data-i18n to them
        // For simplicity, let's just leave tags as is or assume they map to data-filter
    }

    langSelect.addEventListener('change', (e) => {
        updateLanguage(e.target.value);
    });

    // Detect language
    const userLang = navigator.language.startsWith('ja') ? 'ja' : 'en';
    langSelect.value = userLang;
    updateLanguage(userLang);

    // --- Sidebar Logic ---
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        sidebarOverlay.classList.toggle('active');
    }
    hamburgerBtn.addEventListener('click', toggleSidebar);
    sidebarOverlay.addEventListener('click', toggleSidebar);

    // --- Navigation & Modal ---
    uploadBtn.addEventListener('click', () => uploadModal.classList.add('active'));
    closeModal.addEventListener('click', () => uploadModal.classList.remove('active'));
    uploadModal.addEventListener('click', (e) => {
        if (e.target === uploadModal) uploadModal.classList.remove('active');
    });

    // --- File Fetching ---
    async function fetchFiles() {
        try {
            const response = await fetch('/api/files');
            files = await response.json();
            renderFiles();
        } catch (error) {
            console.error(error);
            fileGrid.innerHTML = '<p style="text-align:center; grid-column:1/-1">Failed to load files</p>';
        }
    }

    function renderFiles() {
        const query = searchInput.value.toLowerCase();

        const filtered = files.filter(file => {
            const matchesSearch = file.name.toLowerCase().includes(query);
            const matchesTag = currentFilterTag === 'all' || (file.tags && file.tags.includes(currentFilterTag));
            return matchesSearch && matchesTag;
        });

        fileGrid.innerHTML = '';
        if (filtered.length === 0) {
            fileGrid.innerHTML = '<p style="text-align:center; grid-column:1/-1; color:#888;">No matches found</p>';
            return;
        }

        filtered.forEach(file => {
            const card = document.createElement('div');
            card.className = 'file-card';

            let icon = '📄';
            if (file.name.endsWith('.pdf')) icon = '📕';
            if (file.name.match(/\.(jpg|png|jpeg)$/i)) icon = '🖼️';

            // Generate tags HTML
            const tagsHtml = file.tags && file.tags.length
                ? `<div class="file-tags">${file.tags.map(t => `<span class="file-tag-pill">${t}</span>`).join('')}</div>`
                : '';

            card.innerHTML = `
                <div class="file-icon">${icon}</div>
                <div class="file-info">
                    <h3>${file.name}</h3>
                </div>
                ${tagsHtml}
                <div style="font-size:0.75rem; color:#999; margin-top:5px;">${file.date}</div>
            `;

            card.onclick = () => window.open(`/uploads/${file.name}`, '_blank');
            fileGrid.appendChild(card);
        });
    }

    // --- Filtering ---
    tagButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update UI
            tagButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Filter
            currentFilterTag = btn.dataset.filter;
            renderFiles();
        });
    });

    searchInput.addEventListener('input', renderFiles);

    // --- Upload ---
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) selectedFileName.textContent = fileInput.files[0].name;
    });

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!fileInput.files.length) return alert('Please select a file');

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        // Collect tags
        const selectedTags = Array.from(document.querySelectorAll('input[name="tags"]:checked'))
            .map(cb => cb.value);
        if (selectedTags.length) formData.append('tags', selectedTags.join(','));

        try {
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            const result = await res.json();

            if (result.success) {
                alert('Uploaded!');
                uploadModal.classList.remove('active');
                uploadForm.reset();
                selectedFileName.textContent = '';
                fetchFiles();
            } else {
                alert('Failed');
            }
        } catch (err) {
            alert('Error uploading');
        }
    });

    // Init
    fetchFiles();
});
