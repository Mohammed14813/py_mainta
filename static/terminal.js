// static/terminal.js

// ========== اتصال WebSocket ==========
let socket = null;
let isConnected = false;
let botId = null;

function initTerminal(botIdParam) {
    botId = botIdParam;

    // إنشاء اتصال WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${protocol}${window.location.host}/socket.io/?EIO=4&transport=websocket`;

    socket = io({
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
    });

    // ===== أحداث الاتصال =====
    socket.on('connect', function() {
        isConnected = true;
        addTerminalLine('🟢 متصل بالمحطة', 'success');
        addTerminalLine('📌 جاهز لتشغيل البوت', 'info');
        updateConnectionStatus(true);
    });

    socket.on('disconnect', function() {
        isConnected = false;
        addTerminalLine('🔴 تم قطع الاتصال', 'error');
        updateConnectionStatus(false);
    });

    socket.on('connect_error', function() {
        addTerminalLine('❌ فشل الاتصال بالمحطة', 'error');
        updateConnectionStatus(false);
    });

    // ===== استقبال مخرجات المحطة =====
    socket.on('terminal_output', function(data) {
        addTerminalLine(data.message, data.type || 'output');

        // تحديث الحالة بناءً على الرسالة
        if (data.type === 'success' && data.message.includes('يعمل')) {
            updateBotStatus('running', '🟢 يعمل');
        } else if (data.type === 'error' && data.message.includes('فشل')) {
            updateBotStatus('error', '🔴 خطأ');
        } else if (data.type === 'warning' && data.message.includes('إيقاف')) {
            updateBotStatus('stopped', '⚪ متوقف');
        }
    });
}

// ========== إضافة سطر إلى المحطة ==========
function addTerminalLine(text, type = 'output') {
    const container = document.getElementById('terminalContent');
    if (!container) return;

    const line = document.createElement('div');
    line.className = 'terminal-line';

    const timestamp = new Date().toLocaleTimeString();

    switch (type) {
        case 'command':
            line.innerHTML = `<span class="prompt">$</span> <span class="command">${escapeHtml(text)}</span>`;
            break;
        case 'success':
            line.innerHTML = `<span class="success">✅ ${escapeHtml(text)}</span>`;
            break;
        case 'error':
            line.innerHTML = `<span class="error">❌ ${escapeHtml(text)}</span>`;
            break;
        case 'warning':
            line.innerHTML = `<span class="warning">⚠️ ${escapeHtml(text)}</span>`;
            break;
        case 'info':
            line.innerHTML = `<span class="info">ℹ️ ${escapeHtml(text)}</span>`;
            break;
        default:
            line.innerHTML = `<span class="output">${escapeHtml(text)}</span>`;
    }

    container.appendChild(line);

    // التمرير للأسفل
    const display = document.getElementById('terminalOutput');
    if (display) {
        display.scrollTop = display.scrollHeight;
    }
}

// ========== تخطي النصوص الخاصة ==========
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== تحديث حالة الاتصال ==========
function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        if (connected) {
            statusElement.textContent = '🟢 متصل';
            statusElement.style.color = '#00ff00';
        } else {
            statusElement.textContent = '🔴 غير متصل';
            statusElement.style.color = '#ff4444';
        }
    }
}

// ========== تحديث حالة البوت ==========
function updateBotStatus(status, label) {
    const badge = document.getElementById('statusBadge');
    if (badge) {
        badge.className = `status-badge ${status}`;
        badge.textContent = label;
    }
}

// ========== تشغيل البوت ==========
function startBot() {
    if (!isConnected) {
        addTerminalLine('❌ غير متصل بالمحطة', 'error');
        return;
    }

    if (!botId) {
        addTerminalLine('❌ معرف البوت غير موجود', 'error');
        return;
    }

    addTerminalLine('▶ جاري تشغيل البوت...', 'command');
    socket.emit('start_bot_terminal', { bot_id: botId });

    const btn = document.getElementById('btnStart');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ جاري...';
    }
}

// ========== إيقاف البوت ==========
function stopBot() {
    if (!isConnected) {
        addTerminalLine('❌ غير متصل بالمحطة', 'error');
        return;
    }

    if (!botId) {
        addTerminalLine('❌ معرف البوت غير موجود', 'error');
        return;
    }

    addTerminalLine('⏹ جاري إيقاف البوت...', 'command');
    socket.emit('stop_bot_terminal', { bot_id: botId });
}

// ========== إعادة تشغيل البوت ==========
function restartBot() {
    if (!isConnected) {
        addTerminalLine('❌ غير متصل بالمحطة', 'error');
        return;
    }

    if (!botId) {
        addTerminalLine('❌ معرف البوت غير موجود', 'error');
        return;
    }

    addTerminalLine('🔄 جاري إعادة تشغيل البوت...', 'command');

    // إيقاف ثم تشغيل
    socket.emit('stop_bot_terminal', { bot_id: botId });

    setTimeout(() => {
        socket.emit('start_bot_terminal', { bot_id: botId });
    }, 1000);
}

// ========== مسح المحطة ==========
function clearTerminal() {
    const container = document.getElementById('terminalContent');
    if (container) {
        container.innerHTML = '';
        addTerminalLine('🧹 تم مسح المحطة', 'info');
    }
}

// ========== تصدير الدوال للاستخدام العام ==========
window.initTerminal = initTerminal;
window.startBot = startBot;
window.stopBot = stopBot;
window.restartBot = restartBot;
window.clearTerminal = clearTerminal;
window.addTerminalLine = addTerminalLine;