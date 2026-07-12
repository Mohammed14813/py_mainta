// static/script.js

// ========== عرض رسائل منبثقة ==========
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ========== تأكيد الحذف ==========
function confirmDelete(message = 'هل أنت متأكد من حذف هذا العنصر؟') {
    return confirm(message);
}

// ========== تنسيق التاريخ ==========
function formatDate(dateString) {
    if (!dateString) return 'غير معروف';
    const date = new Date(dateString);
    return date.toLocaleString('ar-SA', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ========== الحصول على حجم الملف ==========
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ========== نسخ النص للحافظة ==========
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('✅ تم النسخ للحافظة', 'success');
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        showToast('✅ تم النسخ للحافظة', 'success');
    } catch (err) {
        showToast('❌ فشل النسخ', 'error');
    }
    document.body.removeChild(textarea);
}

// ========== إظهار/إخفاء تحميل ==========
function showLoading(buttonId, text = '⏳ جاري...') {
    const btn = document.getElementById(buttonId);
    if (btn) {
        btn.disabled = true;
        btn.dataset.originalText = btn.textContent;
        btn.textContent = text;
    }
}

function hideLoading(buttonId) {
    const btn = document.getElementById(buttonId);
    if (btn) {
        btn.disabled = false;
        if (btn.dataset.originalText) {
            btn.textContent = btn.dataset.originalText;
            delete btn.dataset.originalText;
        }
    }
}

// ========== إضافة تنسيق CSS للـ Toast ==========
(function addToastStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            animation: slideIn 0.5s ease;
            max-width: 400px;
            box-shadow: 0 5px 30px rgba(0,0,0,0.3);
        }
        .toast.success { background: #00c853; }
        .toast.error { background: #ff1744; }
        .toast.warning { background: #ffaa00; }
        .toast.info { background: #2979ff; }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
})();