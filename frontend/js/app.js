// 脉衡界 前端应用
const app = {
    user: null,
    sessionId: null,
    apiBase: 'http://localhost:5000/api',
    currentUploadType: null,
    currentPage: 'chat',
    quizData: [],
    quizAnswers: [],
    quizIndex: 0,
    mentalQuizData: null,
    mentalQuizAnswers: [],
    mentalQuizIndex: 0,
    currentFeedCategory: 'all',
    caseLibraryData: [],
    caseLibraryCategories: [],

    // 初始化
init() {
        this.sessionId = this.generateId();
        const saved = localStorage.getItem('zhiyi_user');
        if (saved) {
            this.user = JSON.parse(saved);
            this.showMainPage();
        }
        this.initBMIGenderSelector();
        // 初始化主题
        this.initTheme();
        // 启动人物形象待机动画（每隔几秒随机切换 idle/thinking，让人物"活"起来）
        this.startMascotIdleAnimation();
        // 初始化背景粒子动画
        this.initBackgroundParticles();
        // 启动语音功能
        this.initSpeechRecognition();
        // 检查每日打卡提醒
        this.checkDailyCheckin();
        // 初始化饮食记录
        this.initDietLog();
    },

    // 初始化背景粒子动画
    initBackgroundParticles() {
        const container = document.getElementById('particles-container');
        if (!container) return;

        const colors = ['#3b82f6', '#f97316', '#10b981', '#ec4899', '#6366f1'];
        const particleCount = 15;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle p-blue';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animationDelay = (Math.random() * 15).toFixed(1) + 's';
            particle.style.animationDuration = (12 + Math.random() * 8).toFixed(1) + 's';
            container.appendChild(particle);
        }

        // 生成一个较大的浮动光斑
        const blob = document.createElement('div');
        blob.className = 'blob-blue';
        blob.style.left = (Math.random() * 50 + 30) + '%';
        blob.style.top = (Math.random() * 30 + 10) + '%';
        blob.style.animationDelay = (Math.random() * 20).toFixed(1) + 's';
        container.appendChild(blob);
    },

    // 检查每日打卡提醒
    checkDailyCheckin() {
        const lastCheckin = localStorage.getItem('zhy_last_checkin');
        if (!lastCheckin) {
            this.remindCheckin();
            return;
        }
        
        const last = new Date(lastCheckin);
        const now = new Date();
        const diffHours = (now - last) / (1000 * 60 * 60);
        
        // 超过12小时未打卡则提醒
        if (diffHours > 12) {
            this.remindCheckin();
        }
    },

    // 打卡提醒
    remindCheckin() {
        // 只有在非聊天主页才显示提醒
        if (this.currentPage === 'rewards' || this.currentPage === 'chat') return;
        
        const toast = document.createElement('div');
        toast.id = 'checkin-reminder';
        toast.style.cssText = `
            position: fixed;
            bottom: 90px;
            right: 24px;
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: white;
            padding: 14px 20px;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(59, 130, 246, 0.4);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            max-width: 280px;
        `;
        toast.innerHTML = `
            <div style="display:flex;align-items:center;gap:12px;">
                <i class="fas fa-calendar-check" style="font-size:24px;"></i>
                <div>
                    <div style="font-weight:600;">每日健康打卡</div>
                    <div style="font-size:12px;opacity:0.9;">记录今天的健康状态，赚积分！</div>
                </div>
            </div>
            <button onclick="app.switchPage('rewards');document.getElementById('checkin-reminder').remove()" 
                    style="background:rgba(255,255,255,0.2);border:none;border-radius:8px;padding:6px 12px;color:white;font-size:12px;cursor:pointer;">
                去打卡
            </button>
        `;
        document.body.appendChild(toast);
        
        // 自动消失
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 10000);
    },

    // 初始化BMI性别选择器
    initBMIGenderSelector() {
        const updateGenderVisual = () => {
            document.querySelectorAll('.bmi-gender-option').forEach(label => {
                const input = label.querySelector('input');
                const isChecked = input && input.checked;
                if (isChecked) {
                    label.classList.add('active');
                    label.classList.remove('inactive');
                } else {
                    label.classList.remove('active');
                    label.classList.add('inactive');
                }
            });
        };
        document.querySelectorAll('.bmi-gender-option').forEach(label => {
            label.addEventListener('click', (e) => {
                const input = label.querySelector('input');
                if (input && !input.checked) {
                    input.checked = true;
                    updateGenderVisual();
                    input.dispatchEvent(new Event('change'));
                }
            });
        });
        document.querySelectorAll('input[name="bmi-gender"]').forEach(radio => {
            radio.addEventListener('change', updateGenderVisual);
        });
        updateGenderVisual();
    },

    // 初始化主题
    initTheme() {
        const savedTheme = localStorage.getItem('zhy_theme') || 'light';
        document.body.classList.toggle('dark-theme', savedTheme === 'dark');
        
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        if (themeIcon) {
            themeIcon.innerHTML = savedTheme === 'dark' 
                ? '<i class="fas fa-sun" style="color:white;"></i>' 
                : '<i class="fas fa-moon" style="color:white;"></i>';
        }
        if (themeText) {
            themeText.textContent = savedTheme === 'dark' ? '浅色模式' : '暗色模式';
        }
    },

    generateId() {
        return 'sess_' + Math.random().toString(36).substr(2, 9);
    },

    // ========== Toast 通知 ==========
    toast(message, type = 'info') {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#6366f1'
        };
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        const toast = document.createElement('div');
        toast.style.cssText = `position:fixed;top:20px;left:50%;transform:translateX(-50%) translateY(-100px);
            background:rgba(22,27,34,0.95);backdrop-filter:blur(16px);color:var(--text);padding:14px 24px;border-radius:12px;
            box-shadow:0 10px 25px rgba(0,0,0,0.4);z-index:9999;display:flex;align-items:center;gap:10px;
            font-size:14px;font-weight:500;transition:transform 0.3s cubic-bezier(0.34,1.56,0.64,1);
            border:1px solid var(--border);border-left:4px solid ${colors[type]};max-width:90%;`;
        toast.innerHTML = `<i class="fas ${icons[type]}" style="color:${colors[type]};font-size:18px;"></i><span>${message}</span>`;
        document.body.appendChild(toast);
        requestAnimationFrame(() => { toast.style.transform = 'translateX(-50%) translateY(0)'; });
        setTimeout(() => {
            toast.style.transform = 'translateX(-50%) translateY(-100px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // ========== 登录 ==========
    async login() {
        const studentId = document.getElementById('login-student-id').value.trim();
        const username = document.getElementById('login-username').value.trim();

        if (!studentId) {
            this.toast('请输入学号', 'warning');
            return;
        }

        try {
            const res = await fetch(`${this.apiBase}/auth/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({student_id: studentId, username: username || `用户${studentId}`})
            });
            const data = await res.json();

            if (data.success) {
                this.user = data.user;
                localStorage.setItem('zhiyi_user', JSON.stringify(this.user));
                this.showMainPage();
                this.toast('欢迎回来，' + (this.user.username || '同学') + '！', 'success');
            }
        } catch (e) {
            console.error('登录失败:', e);
            this.user = {
                student_id: studentId,
                username: username || `用户${studentId}`,
                total_points: 0
            };
            localStorage.setItem('zhiyi_user', JSON.stringify(this.user));
            this.showMainPage();
            this.toast('演示模式登录', 'info');
        }
    },

    showMainPage() {
        document.getElementById('login-page').classList.remove('active');
        document.getElementById('main-page').classList.add('active');
        document.body.classList.add('main-active');

        document.getElementById('user-name').textContent = this.user.username;
        document.getElementById('user-points').textContent = this.user.total_points + ' 积分';

        const avatarText = this.user.username ? this.user.username.charAt(0) : '用';
        const avatarEl = document.getElementById('user-avatar-text');
        if (avatarEl) avatarEl.textContent = avatarText;

        this.updateMobilePoints();
        this.loadRewardsStats();
        this.loadHealthFeed();
    },

    updateMobilePoints() {
        const el = document.getElementById('mobile-user-points');
        if (el) {
            el.querySelector('span').textContent = this.user.total_points || 0;
        }
    },

    // ========== 页面切换 ==========
    switchPage(page) {
        this.currentPage = page;

        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');

        document.querySelectorAll('.bottom-nav-item').forEach(el => el.classList.remove('active'));
        const bottomItem = document.querySelector(`.bottom-nav-item[data-page="${page}"]`);
        if (bottomItem) bottomItem.classList.add('active');

        document.querySelectorAll('.content-page').forEach(el => el.classList.remove('active'));
        const targetPage = document.getElementById(`page-${page}`);
        if (targetPage) targetPage.classList.add('active');

        // 切换页面时人物形象短暂展示"指引"动作，1.5秒后回到待机
        this.setMascotPose('guide', 1500);

        this.closeSidebar();
        document.querySelector('.main-content')?.scrollTo(0, 0);

        // 控制浮动按钮显示（聊天页和体质辨识问卷页隐藏）
        const fab = document.getElementById('floating-avatar');
        const hideFabPages = ['chat', 'tcm'];
        if (fab) fab.style.display = hideFabPages.includes(page) ? 'none' : 'flex';

        if (page === 'rewards') {
            this.loadRewardsStats();
            this.loadRewardsHistory();
            this.loadLeaderboard();
            this.loadShopItems();
            this.loadCheckinStatus();
            this.loadAchievements();
            this.loadRewardActions();
        } else if (page === 'community') {
            this.loadHealthFeed();
        } else if (page === 'diagnosis') {
            this.loadHealthSummary();
        } else if (page === 'mental') {
            this.loadMentalHistory();
        } else if (page === 'privacy') {
            this.loadPrivacySettings();
        } else if (page === 'tcm') {
            // 体质辨识页面无需额外加载
        } else if (page === 'diet') {
            this.loadDietHistory();
            this.loadDietLogs();
            this.loadCaloriesChart(7);
            this.loadNightAnalysis();
        }
    },

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const backdrop = document.querySelector('.sidebar-backdrop');
        sidebar.classList.toggle('open');
        if (backdrop) backdrop.classList.toggle('show');
    },

    closeSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const backdrop = document.querySelector('.sidebar-backdrop');
        if (sidebar) sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('show');
    },

    // 主题切换
    toggleTheme() {
        const current = localStorage.getItem('zhy_theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        localStorage.setItem('zhy_theme', next);
        document.body.classList.toggle('dark-theme', next === 'dark');
        
        // 更新图标和文本
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        if (themeIcon) {
            themeIcon.innerHTML = next === 'dark' 
                ? '<i class="fas fa-sun" style="color:white;"></i>' 
                : '<i class="fas fa-moon" style="color:white;"></i>';
        }
        if (themeText) {
            themeText.textContent = next === 'dark' ? '浅色模式' : '暗色模式';
        }
        
        // 提示
        this.toast(`已切换到${next === 'dark' ? '暗色' : '浅色'}模式`, 'info');
    },

    toggleMoreMenu() {
        const menu = document.getElementById('more-menu');
        const overlay = document.getElementById('more-menu-overlay');
        if (!menu || !overlay) return;

        const isOpen = menu.classList.contains('show');
        if (isOpen) {
            menu.classList.remove('show');
            overlay.classList.remove('show');
        } else {
            menu.classList.add('show');
            overlay.classList.add('show');
        }
    },

    // ========== DOM元素缓存 ==========
    // 常用元素缓存，提高性能和可维护性
    qs(selector, context=document) {
        return context.querySelector(selector);
    },
    qsa(selector, context=document) {
        return context.querySelectorAll(selector);
    },
    // 元素快捷引用
    get chatInput() { return this.qs('#chat-input'); },
    get micButton() { return this.qs('#mic-button'); },
    get userNameEl() { return this.qs('#user-name'); },
    get userPointsEl() { return this.qs('#user-points'); },
    get chatMessages() { return this.qs('#chat-messages'); },
    get sidebar() { return this.qs('.sidebar'); },
    get bottomNav() { return this.qs('.bottom-nav'); },
    get fab() { return this.qs('#floating-avatar'); },
    get sidebarBackdrop() { return this.qs('.sidebar-backdrop'); },
    get moreMenu() { return this.qs('#more-menu'); },
    get moreMenuOverlay() { return this.qs('#more-menu-overlay'); },
    get caseModal() { return this.qs('#case-modal'); },
    get feedModal() { return this.qs('#feed-modal'); },
    get loadingOverlay() { return this.qs('#loading-overlay'); },
    get emojiPicker() { return this.qs('#emoji-picker'); },
    get healthSummary() { return this.qs('#health-summary'); },
    get mobileUserPoints() { return this.qs('#mobile-user-points'); },
    // 初始化语音识别
    initSpeechRecognition() {
        const supported = this.getSpeechSupport();
        const micBtn = document.getElementById('mic-button');
        if (micBtn) {
            micBtn.style.display = supported ? 'flex' : 'none';
            if (!supported) {
                this.toast('当前浏览器不支持语音输入', 'warning');
            }
        }
    },
    // 语音输入按钮点击
    async onMicClick() {
        if (!this.getSpeechSupport()) {
            this.toast('当前浏览器不支持语音输入', 'warning');
            return;
        }
        this.toggleListening();
    },
    // 切录听状态
    toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    },
    // 开始监听
    startListening() {
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new Recognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'zh-CN';

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById('chat-input').value = transcript;
            this.sendMessage();
        };

        this.recognition.onerror = (event) => {
            console.error('语音识别错误:', event.error);
            this.toast('语音识别失败，请重试', 'warning');
            this.stopListening();
        };

        this.isListening = true;
        this.recognition.start();
        this.toast('正在监听...', 'info');
    },
    // 停止监听
    stopListening() {
        if (this.recognition) {
            this.recognition.stop();
        }
        this.isListening = false;
        this.toast('已停止监听', 'info');
    },
    // 语音输出（TTS）
    speakText(text) {
        // 取消任何正在进行的语音
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
        
        if (!text || !('speechSynthesis' in window)) {
            // 如果不支持，隐藏指示器
            const indicator = document.getElementById('speech-indicator');
            if (indicator) indicator.style.display = 'none';
            return;
        }
        
        // 显示语音播放状态
        const indicator = document.getElementById('speech-indicator');
        if (indicator) {
            indicator.style.display = 'flex';
        }
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'zh-CN';
        utterance.rate = 0.9;
        utterance.pitch = 1;
        
        utterance.onend = () => {
            // 播放结束后隐藏指示器
            if (indicator) {
                setTimeout(() => {
                    indicator.style.display = 'none';
                }, 500);
            }
        };
        
        utterance.onerror = () => {
            if (indicator) {
                indicator.style.display = 'none';
            }
        };
        
        speechSynthesis.speak(utterance);
    },

    // 停止语音播放
    stopSpeech() {
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
        const indicator = document.getElementById('speech-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    },
    // 切换侧边栏后重新检查语音支持
    init() {
        this.initBMIGenderSelector();
        // 启动人物形象待机动画
        this.startMascotIdleAnimation();
        // 初始化语音功能
        this.initSpeechRecognition();
    },

// ========== 聊天功能 ==========
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message) return;

        // 隐藏快捷回复按钮
        const quickReplies = document.querySelector('#chat-messages .quick-replies');
        if (quickReplies) quickReplies.style.display = 'none';

        input.value = '';
        input.style.height = 'auto';
        this.addMessage('user', message);
        this.showLoading(true);

        // 直接走普通 fetch /api/chat：最稳，规避所有 SSE buffer 解析问题
        // 打字机效果由 _typeWriterEffect 实现（前端逐字渲染已拿到的完整回复）
        if (!this.user) {
            this.user = { student_id: 'guest', username: '游客', total_points: 0 };
        }
        // 兜底 sessionId：init 未执行或被重置时也能正常发消息
        if (!this.sessionId) {
            this.sessionId = this.generateId();
        }

        let data;
        try {
            const res = await fetch(`${this.apiBase}/chat`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    message: message,
                    session_id: this.sessionId
                })
            });

            if (!res.ok) {
                // HTTP 4xx/5xx：明确告诉用户原因，不再笼统说"网络错误"
                let detail = '';
                try { detail = (await res.text()).slice(0, 200); } catch (_) {}
                throw new Error(`HTTP ${res.status}${detail ? ' - ' + detail : ''}`);
            }

            data = await res.json();
        } catch (e) {
            console.error('sendMessage fetch 失败:', e);
            this.showLoading(false);
            this.addMessage('assistant',
                `⚠️ 连接后端失败：${e.message}\n\n请确认：\n1. 后端服务已启动（终端能看到 "✅ AI 服务可用" 提示）\n2. 浏览器能访问 http://localhost:5000`);
            this.toast('网络连接失败', 'error');
            return;
        }

        // 拿到响应（可能是 AI 回复，也可能是 [LLM错误]/[系统错误] 兜底）
        const content = data.content || data.answer || '';
        if (!content) {
            this.showLoading(false);
            this.addMessage('assistant', '⚠️ AI 未返回任何内容，请稍后重试。');
            return;
        }

        // 打字机效果逐字渲染（保持"流式"的视觉感受，但不依赖 SSE）
        await this._typeWriterEffect('assistant', content, 'chat-messages');

        // 语音输出
        this.speakText(content);

        // 渲染医案参考资料卡片
        if (data.references && data.references.length > 0) {
            this.showReferences(data.references, 'chat-messages');
        }
        if (data.mental_assessment) {
            this.showMentalScore(data.mental_assessment, 'chat-messages');
        }
        if (data.alert_triggered) {
            this.showAlert(data.alert_triggered, 'chat-messages');
        }
        if (this.user) {
            this.user.total_points = (this.user.total_points || 0) + 1;
            document.getElementById('user-points').textContent = this.user.total_points + ' 积分';
            this.updateMobilePoints();
        }

        // 膳食意图检测：自动提示跳转膳食推荐
        if (this.detectDietIntent(message)) {
            this.addMessage('assistant', '检测到膳食相关问题，已为你准备好智能膳食推荐。正在跳转...', 'chat-messages');
            setTimeout(() => {
                this.switchPage('tcm');
                // 将用户的问题填入备注
                const notesInput = document.getElementById('diet-notes');
                if (notesInput) notesInput.value = message;
            }, 1200);
        }

        this.showLoading(false);
    },

    // 打字机效果：逐字渲染消息，保留"流式"视觉感受但不需要 SSE
    async _typeWriterEffect(role, content, containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            this.addMessage(role, content, containerId);
            return;
        }

        // 先创建空气泡
        const div = document.createElement('div');
        div.className = `message ${role}`;
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.textContent = '';
        div.appendChild(bubble);
        container.appendChild(div);

        // 简单转义 + 换行处理（最终再用 addMessage 覆盖以支持 markdown）
        const escapeHtml = (s) => s
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        const total = content.length;
        // 总时长约 1.5~3s，自适应长度
        const step = Math.max(1, Math.floor(total / 80));
        const delay = total < 50 ? 25 : (total < 200 ? 12 : 6);

        for (let i = 0; i < total; i += step) {
            const chunk = content.slice(0, i + step);
            bubble.innerHTML = escapeHtml(chunk).replace(/\n/g, '<br>');
            container.scrollTop = container.scrollHeight;
            await new Promise(r => setTimeout(r, delay));
        }

        // 最终用 addMessage 覆盖（支持 markdown 渲染、医案卡片等）
        div.remove();
        this.addMessage(role, content, containerId);
    },

    // ========== 聊天SSE流式响应 ==========
    // 注意: EventSource不支持POST参数，改用fetch+ReadableStream方案
    sendMessageStreaming(message) {
        return new Promise((resolve, reject) => {
            // 显示流式状态
            this._showStreamingStatus(true);
            
            fetch(`${this.apiBase}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    message: message,
                    session_id: this.sessionId
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullContent = '';
                let buffer = '';
                
                const container = document.getElementById('chat-messages');
                let assistantMsg = null;
                
                let finalData = {};     // 保存末帧元数据（references/mental_assessment 等）
                const readStream = () => {
                    return reader.read().then(({ done, value }) => {
                        if (done) {
                            // 流结束
                            this._showStreamingStatus(false);
                            if (fullContent) {
                                // 调用 addMessage 完成完整渲染
                                this._finalizeStreamingMessage(assistantMsg, fullContent, finalData);
                            }
                            resolve(fullContent);
                            return;
                        }

                        buffer += decoder.decode(value, { stream: true });

                        // 处理SSE数据块
                        const lines = buffer.split('\n\n');
                        buffer = lines.pop() || ''; // 保留最后一个可能不完整的数据块

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));

                                    if (data.error) {
                                        this._showStreamingStatus(false);
                                        reject(new Error(data.error));
                                        return;
                                    }

                                    if (data.chunk && !data.done) {
                                        fullContent += data.chunk;
                                        // 显示累积内容
                                        if (!assistantMsg) {
                                            const div = document.createElement('div');
                                            div.className = 'message assistant';
                                            div.innerHTML = '<div class="message-bubble"></div>';
                                            container.appendChild(div);
                                            assistantMsg = div;
                                        }
                                        const bubble = assistantMsg.querySelector('.message-bubble');
                                        if (bubble) {
                                            bubble.textContent = fullContent || '小艺正在思考...';
                                        }
                                        container.scrollTop = container.scrollHeight;
                                    } else if (data.done) {
                                        // 末帧：保存元数据，流结束后用于渲染卡片
                                        finalData = data;
                                        if (data.full_content && !fullContent) {
                                            fullContent = data.full_content;
                                        }
                                    }
                                } catch (e) {
                                    // 忽略解析错误，继续处理
                                }
                            }
                        }

                        return readStream();
                    });
                };
                
                readStream().catch(err => {
                    this._showStreamingStatus(false);
                    reject(err);
                });
            })
            .catch(error => {
                this._showStreamingStatus(false);
                console.error('SSE流式失败:', error);
                reject(error);
            });
        });
    },
    
    // 显示/隐藏流式状态指示器
    _showStreamingStatus(showing) {
        const container = document.getElementById('chat-messages');
        if (!container) return;
        
        if (showing) {
            // 添加一个临时的思考气泡
            let thinkingBubble = container.querySelector('.message.assistant.thinking');
            if (!thinkingBubble) {
                const div = document.createElement('div');
                div.className = 'message assistant thinking';
                div.innerHTML = '<div class="message-bubble">🧠 <span style="opacity:0.7">正在思考...</span></div>';
                container.appendChild(div);
            }
        } else {
            // 移除思考气泡
            const thinkingBubble = container.querySelector('.message.assistant.thinking');
            if (thinkingBubble) {
                thinkingBubble.remove();
            }
        }
        
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    },
    
    // 完成流式消息渲染
    _finalizeStreamingMessage(assistantMsg, content, finalData) {
        const container = document.getElementById('chat-messages');
        if (!container) return;
        
        // 移除思考气泡
        const thinkingBubble = container.querySelector('.message.assistant.thinking');
        if (thinkingBubble) {
            thinkingBubble.remove();
        }
        
        // 添加完整格式化消息
        this.addMessage('assistant', content, 'chat-messages');
        
        // 处理附加数据
        if (finalData.references && finalData.references.length > 0) {
            this.showReferences(finalData.references, 'chat-messages');
        }
        
        if (finalData.mental_assessment) {
            this.showMentalScore(finalData.mental_assessment, 'chat-messages');
        }
        
        if (finalData.alert_triggered) {
            this.showAlert(finalData.alert_triggered, 'chat-messages');
        }
        
        // 自动朗读
        this.speakText(content || '');
    },

    // 导出诊断报告
    exportDiagnosisReport(content, answers = {}) {
        if (!this.user) {
            this.toast('请先登录', 'warning');
            return;
        }
        
        this.toast('正在生成报告...', 'info');
        
        fetch(`${this.apiBase}/diagnosis/export`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                student_id: this.user.student_id,
                message: '',
                session_id: this.sessionId,
                content: content,
                answers: answers
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success && data.report_html) {
                const printWindow = window.open('', '_blank');
                printWindow.document.write(data.report_html);
                printWindow.document.title = '脉衡界诊断报告';
                printWindow.focus();
                setTimeout(() => {
                    printWindow.print();
                }, 500);
                this.toast('报告已生成，正在打印...', 'success');
            } else {
                this.toast('导出失败，请稍后重试', 'error');
            }
        })
        .catch(err => {
            console.error('导出失败:', err);
            this.toast('导出失败，请检查网络', 'error');
        });
    },

addMessage(role, content, containerId = 'chat-messages') {
        const container = document.getElementById(containerId);
        if (!container) return;
        const div = document.createElement('div');
        div.className = `message ${role}`;

        let html = content
            .replace(/&/g, '&')
            .replace(/</g, '<')
            .replace(/>/g, '>')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/(?:\[)?医案\s*(C\d{3})(?:\])?/g, '<span class="case-ref" onclick="app.openCaseModal(\'$1\')" style="color:var(--primary-lighter);cursor:pointer;text-decoration:underline;font-weight:600;">[医案 $1] <i class="fas fa-external-link-alt" style="font-size:11px;"></i></span>');

        // 如果是助手消息，添加“人类触感”装饰
        if (role === 'assistant') {
            html = this._addHumanTouch(html);
        }

        div.innerHTML = `<div class="message-bubble">${html}</div>`;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },

    // 新增：添加“人类触感”装饰 - 让消息不那么机械，更有温度
    _addHumanTouch(text) {
        let result = text;
        
        // 确保文本以温暖的方式结尾（如果还没有跟进问题）
        const warmEndings = ['吗？', '呢', '！', '。', '，'];
        const lastChar = text.trim().slice(-1);
        // 只在文本还没结尾，且最后不是已经是温暖标点时添加
        if (!warmEndings.some(end => text.endsWith(end)) && lastChar !== '<' && lastChar !== '>') {
            // 在内容末尾的合适位置添加温暖的跟进（不破坏已有结构）
            // 找到最后一个有内容的div/bubble结尾前插入
            result = text.replace('</div>', '</div><div style="font-size:12px;color:var(--text-light);margin-top:4px;opacity:0.8;">小艺在想...</div>');
        }
        
        // 为常见的健康关键词添加同理心前缀（仅在文本开头的显示文本中）
        // 通过检测气泡内容来微调显示
        const medicalEmpathyOpening = '我能理解你的感受';
        
        // 检查是否为结构化诊断格式（有特定的标题）
        const structuredIndicators = ['症状分析:', '处理建议:', '就医提示:'];
        const isStructured = structuredIndicators.some(ind => text.includes(ind));
        
        // 非结构化的健康建议文本才添加同理心开场
        if (!isStructured) {
            // 简单检查是否包含常见健康关键词
            const healthKeywords = ['疼痛', '发烧', '咳嗽', '头痛', '胃痛', '疲劳', '焦虑', '失眠'];
            const hasHealthKeyword = healthKeywords.some(kw => text.includes(kw));
            if (hasHealthKeyword && !text.startsWith(healthKeywords.join('|'))) {
                // 在气泡内容最前面温和插入同理心开场
                const firstContentMatch = text.match(/>(.+?)</);
                if (firstContentMatch) {
                    const before = firstContentMatch[1].substring(0, 50);
                    result = text.replace(firstContentMatch[0], `>${medicalEmpathyOpening}，${before}<`);
                } else {
                    result = `<div style="color:var(--text-secondary);font-size:13px;margin-bottom:8px;">${medicalEmpathyOpening}</div>${text}`;
                }
            }
        }
        
        return result;
    },

    // 新增：格式化结构化诊断输出
    _formatStructuredDiagnosis(text) {
        // 匹配结构化诊断格式：关键字: 内容 的多行格式
        // 例如：症状分析: ... / 处理建议: ... 等
        const lines = text.split('<br>');
        const structuredSections = {
            '症状分析': { class: 'symptom-analysis', important: true },
            '处理建议': { class: 'treatment-suggestion', important: true },
            '就医提示': { class: 'medical-visit', important: true },
            '风险等级': { class: 'risk-level', important: true },
            '推荐科室': { class: 'recommended-dept', important: true },
            '下一步行动': { class: 'next-action', important: true },
            '就诊摘要': { class: 'consult-summary', important: false }  // 医生用，患者可隐藏
        };
        
        // 检测是否为结构化诊断格式
        const detectedSections = {};
        let isStructured = false;
        
        for (const line of lines) {
            const trimmed = line.trim().replace(/<[^>]+>/g, '').trim();
            for (const [key, info] of Object.entries(structuredSections)) {
                if (trimmed.startsWith(key + ':') || trimmed.startsWith(key)) {
                    isStructured = true;
                    detectedSections[key] = trimmed.substring(key.length).trim();
                    break;
                }
            }
        }
        
        // 如果检测到结构化格式，美化渲染
        if (isStructured) {
            let result = '';
            const showPatientSections = ['症状分析', '处理建议', '就医提示', '风险等级', '推荐科室', '下一步行动'];
            const doctorOnlySections = ['就诊摘要'];
            
            for (const line of lines) {
                const cleaned = line.replace(/<[^>]+>/g, '').trim();
                if (!cleaned) continue;
                
                let added = false;
                for (const [key, info] of Object.entries(structuredSections)) {
                    if (cleaned.startsWith(key + ':')) {
                        const value = cleaned.substring(key.length).trim();
                        const displayKey = key.replace('诊', '').replace('析', '') + ':';
                        
                        if (info.important || showPatientSections.includes(key)) {
                            // 患者可见的关键信息
                            result += `<div style="margin:12px 0;padding:12px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);">
                                <div style="font-weight:600;font-size:13px;color:var(--primary-lighter);margin-bottom:6px;">${displayKey}</div>
                                <div style="font-size:14px;color:var(--text);line-height:1.5;">${value}</div>
                            </div>`;
                        }
                        added = true;
                        break;
                    }
                }
                
                // 如果不是识别出的结构化键，且是结构化格式，则隐藏“就诊摘要”部分
                if (!added && isStructured && doctorOnlySections.some(k => cleaned.startsWith(k))) {
                    // 收集医生专用部分，稍后单独显示或不显示
                }
            }
            
            // 如果有医生专用部分，可以在底部添加可折叠的“显示给医生查看”
            // 这里简化处理，直接返回已格式化的内容
            return result;
        }
        
        // 非结构化格式，原有处理
        return text;
    },

    // 插入表情
    insertEmoji(emoji) {
        const input = document.getElementById('chat-input');
        if (!input) return;
        const start = input.selectionStart;
        const end = input.selectionEnd;
        const text = input.value;
        input.value = text.slice(0, start) + emoji + text.slice(end);
        input.setSelectionRange(start + emoji.length, start + emoji.length);
        // 自动聚焦保持输入
        input.focus();
    },

    handleKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    },

    autoResize(e) {
        const ta = e.target;
        ta.style.height = 'auto';
        ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
    },

    clearChat() {
        const container = document.getElementById('chat-messages');
        container.innerHTML = `
            <div class="message system">
                <div class="message-bubble">
                    <p>对话已清空。我是AI小艺，有什么可以帮你的吗？</p>
                </div>
            </div>
            <div class="quick-replies">
                <button class="quick-reply-btn" onclick="app.quickReply('我最近压力很大，有点焦虑')">
                    <i class="fas fa-brain"></i> 心理压力
                </button>
                <button class="quick-reply-btn" onclick="app.quickReply('我是什么体质？如何调理？')">
                    <i class="fas fa-leaf"></i> 中医体质
                </button>
                <button class="quick-reply-btn" onclick="app.quickReply('最近感冒了怎么办')">
                    <i class="fas fa-stethoscope"></i> 健康问诊
                </button>
                <button class="quick-reply-btn" onclick="app.quickReply('推荐一份适合学生的健康食谱')">
                    <i class="fas fa-utensils"></i> 食疗推荐
                </button>
            </div>
        `;
        this.sessionId = this.generateId();
        this.toast('对话已清空', 'info');
    },

    // ========== 快捷回复 ==========
    quickReply(text) {
        const quickReplies = document.querySelector('.quick-replies');
        if (quickReplies) quickReplies.style.display = 'none';
        document.getElementById('chat-input').value = text;
        this.sendMessage();
    },

    // ========== 心理疏导 ==========
    async sendMentalMessage() {
        const input = document.getElementById('mental-input');
        const message = input.value.trim();
        if (!message) return;

        input.value = '';
        input.style.height = 'auto';
        this.addMessage('user', message, 'mental-messages');
        this.showLoading(true);

        try {
            const res = await fetch(`${this.apiBase}/chat`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    message: message,
                    session_id: this.sessionId + '_mental',
                    force_intent: 'mental'
                })
            });
            const data = await res.json();
            this.addMessage('assistant', data.content || '小艺在倾听...', 'mental-messages');
            // 语音输出：自动朗读助手回复
            this.speakText(data.content || '小艺在倾听...');

            if (data.mental_assessment) {
                this.showMentalScore(data.mental_assessment, 'mental-messages');
            }

            if (data.alert_triggered) {
                this.showAlert(data.alert_triggered, 'mental-messages');
            }
        } catch (e) {
            this.addMessage('assistant', '我理解你的感受，愿意继续倾听。请稍后再试。', 'mental-messages');
            this.toast('网络连接失败', 'error');
        }

        this.showLoading(false);
    },

    handleMentalKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMentalMessage();
        }
    },

    showMentalScore(assessment, containerId = 'chat-messages') {
        const score = assessment.overall_score;
        let color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';

        const html = `
            <div style="margin-top:10px;padding:14px;background:rgba(13,148,136,0.06);border-radius:10px;border:1px solid var(--border);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-weight:600;font-size:13px;color:var(--text-secondary);">心理状态评分</span>
                    <span style="font-size:26px;font-weight:800;color:${color};">${score}</span>
                </div>
                <div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;">
                    <div style="width:${score}%;height:100%;background:${color};transition:width 0.6s cubic-bezier(0.4,0,0.2,1);border-radius:4px;"></div>
                </div>
                <div style="display:flex;gap:10px;margin-top:10px;font-size:12px;color:var(--text-light);flex-wrap:wrap;">
                    <span>焦虑 ${assessment.anxiety_score ?? '-'}</span>
                    <span>抑郁 ${assessment.depression_score ?? '-'}</span>
                    <span>压力 ${assessment.stress_score ?? '-'}</span>
                </div>
            </div>
        `;

        const container = document.getElementById(containerId);
        if (!container) return;
        const lastMsg = container.lastElementChild;
        if (lastMsg) {
            const bubble = lastMsg.querySelector('.message-bubble');
            if (bubble && !bubble.innerHTML.includes('心理状态评分')) {
                bubble.innerHTML += html;
            }
            container.scrollTop = container.scrollHeight;
        }
    },

    showAlert(alert, containerId = 'chat-messages') {
        const container = document.getElementById(containerId);
        if (!container) return;
        const div = document.createElement('div');
        div.className = 'message system';
        div.innerHTML = `
            <div class="message-bubble" style="border-color:rgba(239,68,68,0.3);background:rgba(239,68,68,0.08);">
                <i class="fas fa-exclamation-triangle" style="color:#ef4444;margin-right:8px;"></i>
                ${alert.message || '系统检测到你需要关注心理健康'}
            </div>
        `;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },

    // ========== 医案参考资料卡片 ==========
    showReferences(references, containerId = 'chat-messages') {
        const container = document.getElementById(containerId);
        if (!container || !references.length) return;

        const div = document.createElement('div');
        div.className = 'message assistant';
        div.innerHTML = `
            <div class="message-bubble" style="padding:0;overflow:hidden;">
                <div style="padding:12px 16px;background:rgba(13,148,136,0.08);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;">
                    <i class="fas fa-book-medical" style="color:var(--primary-lighter);"></i>
                    <span style="font-weight:600;font-size:13px;color:var(--primary-lighter);">参考资料 · 医案溯源</span>
                </div>
                <div style="padding:12px 16px;display:flex;flex-direction:column;gap:10px;">
                    ${references.map(ref => `
                        <div class="ref-card" onclick="app.openCaseModal('${ref.case_id}')" style="padding:12px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;transition:all 0.25s;">
                            <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px;">
                                <div style="flex:1;">
                                    <div style="font-weight:700;font-size:13px;color:var(--primary-lighter);margin-bottom:4px;">[医案 ${ref.case_id}]</div>
                                    <div style="font-size:13px;color:var(--text);font-weight:500;margin-bottom:4px;">${ref.title || '医案详情'}</div>
                                    ${ref.disease ? `<div style="font-size:12px;color:var(--text-light);"><i class="fas fa-tag" style="font-size:10px;"></i> ${ref.disease}${ref.syndrome ? ' · ' + ref.syndrome : ''}</div>` : ''}
                                </div>
                                <i class="fas fa-chevron-right" style="color:var(--text-muted);font-size:12px;margin-top:4px;"></i>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },

    async loadMentalHistory() {
        try {
            const res = await fetch(`${this.apiBase}/mental/assessments?student_id=${this.user.student_id}`);
            const data = await res.json();
            this.renderMentalChart(data.assessments || []);
        } catch (e) {
            console.log('加载心理历史失败');
        }
    },

    renderMentalChart(assessments) {
        const canvas = document.getElementById('mental-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth || 300;
        canvas.height = 200;

        if (assessments.length === 0) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#6e7681';
            ctx.font = '14px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('暂无评估数据', canvas.width / 2, canvas.height / 2);
            return;
        }

        const scores = assessments.slice(-7).map(a => a.overall_score);
        const max = 100;
        const min = 0;
        const range = max - min;

        ctx.strokeStyle = 'rgba(255,255,255,0.05)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = 20 + (i / 4) * (canvas.height - 50);
            ctx.beginPath();
            ctx.moveTo(20, y);
            ctx.lineTo(canvas.width - 10, y);
            ctx.stroke();
        }

        ctx.strokeStyle = '#14b8a6';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        scores.forEach((score, i) => {
            const x = (i / (scores.length - 1 || 1)) * (canvas.width - 40) + 20;
            const y = canvas.height - 30 - ((score - min) / range) * (canvas.height - 60);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        ctx.lineTo((scores.length - 1) / (scores.length - 1 || 1) * (canvas.width - 40) + 20, canvas.height - 30);
        ctx.lineTo(20, canvas.height - 30);
        ctx.closePath();
        ctx.fillStyle = 'rgba(20, 184, 166, 0.1)';
        ctx.fill();

        scores.forEach((score, i) => {
            const x = (i / (scores.length - 1 || 1)) * (canvas.width - 40) + 20;
            const y = canvas.height - 30 - ((score - min) / range) * (canvas.height - 60);
            ctx.fillStyle = '#14b8a6';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#0a0e14';
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, Math.PI * 2);
            ctx.fill();
        });
    },

    // ========== 多模态上传 ==========
    triggerUpload(type) {
        this.currentUploadType = type;
        document.getElementById('upload-input').click();
    },

    async handleUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 16 * 1024 * 1024) {
            this.toast('图片不能超过16MB', 'error');
            e.target.value = '';
            return;
        }

        const uploadFromPage = this.currentPage;

        this.showLoading(true);
        this.toast('正在上传分析...', 'info');

        const formData = new FormData();
        formData.append('image', file);
        formData.append('image_type', this.currentUploadType);
        formData.append('student_id', this.user.student_id);
        formData.append('session_id', this.sessionId);

        try {
            const res = await fetch(`${this.apiBase}/upload/image`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.error) {
                this.toast(data.error, 'error');
                this.showLoading(false);
                e.target.value = '';
                return;
            }

            const resultDiv = document.getElementById(`${this.currentUploadType}-result`);
            if (resultDiv) {
                const analysis = data.attachments?.image_analysis || {};
                resultDiv.innerHTML = `
                    <img src="${this.apiBase.replace('/api', '')}${data.image_path}" class="image-preview">
                    <div style="margin-top:12px;">${this.formatContent(data.content)}</div>
                `;
                resultDiv.classList.add('show');
            }

            if (uploadFromPage === 'tcm') {
                this.toast('分析完成，请查看下方结果', 'success');
            } else {
                this.addMessage('user', `[上传了${this.currentUploadType === 'tongue' ? '舌象' : '餐食'}照片]`);
                this.addMessage('assistant', data.content || '分析完成');
                this.toast('分析完成', 'success');
            }
        } catch (err) {
            this.toast('上传失败: ' + err.message, 'error');
        }

        this.showLoading(false);
        e.target.value = '';
    },

    // ========== 食疗推荐 ==========
    async recommendFood() {
        // Legacy function - redirects to new diet page
        this.switchPage('tcm');
    },

    // ========== 膳食推荐 ==========
    async syncBmiToDiet() {
        try {
            const res = await fetch(`${this.apiBase}/diet/bmi-sync`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ student_id: this.user.student_id })
            });
            const data = await res.json();
            if (data.success) {
                const info = data.data;
                document.getElementById('diet-bmi-height').textContent = info.height || '-';
                document.getElementById('diet-bmi-weight').textContent = info.weight || '-';
                document.getElementById('diet-bmi-value').textContent = info.bmi ? Number(info.bmi).toFixed(1) : '-';
                document.getElementById('diet-bmi-category').textContent = info.bmi_category || '-';
                document.getElementById('diet-bmi-info').style.display = 'block';
                this.toast('BMI数据同步成功', 'success');
            } else {
                this.toast(data.message || '同步失败', 'warning');
            }
        } catch (e) {
            this.toast('同步失败，请稍后重试', 'error');
        }
    },

    async getDietRecommendation(type) {
        const goal = document.getElementById('diet-goal').value;
        const constitution = document.getElementById('diet-constitution').value;
        const notes = document.getElementById('diet-notes').value.trim();
        const tagCheckboxes = document.querySelectorAll('#diet-tags input:checked');
        const tags = Array.from(tagCheckboxes).map(cb => cb.value);

        this.showLoading(true);

        try {
            const endpoint = type === 'ai' ? '/diet/recommend/ai' : '/diet/recommend';
            const res = await fetch(`${this.apiBase}${endpoint}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    goal: goal,
                    constitution: constitution,
                    tags: tags,
                    notes: notes,
                    use_bmi_data: true
                })
            });
            const data = await res.json();

            if (data.success) {
                this.renderDietResult(data.plan, type);
                this.loadDietHistory();
                this.toast(type === 'ai' ? 'AI精细推荐已生成' : '算法推荐已生成', 'success');
            } else {
                this.toast(data.message || '推荐失败', 'error');
            }
        } catch (e) {
            this.toast('请求失败，请稍后重试', 'error');
        }

        this.showLoading(false);
    },

    renderDietResult(plan, type) {
        const resultDiv = document.getElementById('diet-result');
        resultDiv.style.display = 'block';

        // 热量概览
        const calSummary = document.getElementById('diet-calories-summary');
        calSummary.innerHTML = `
            <div class="diet-cal-item"><div class="value">${Math.round(plan.target_calories || 0)}</div><div class="label">目标热量 kcal</div></div>
            <div class="diet-cal-item"><div class="value">${Math.round(plan.breakfast_calories || 0)}</div><div class="label">早餐 kcal</div></div>
            <div class="diet-cal-item"><div class="value">${Math.round(plan.lunch_calories || 0)}</div><div class="label">午餐 kcal</div></div>
            <div class="diet-cal-item"><div class="value">${Math.round(plan.dinner_calories || 0)}</div><div class="label">晚餐 kcal</div></div>
            <div class="diet-cal-item"><div class="value">${Math.round(plan.snack_calories || 0)}</div><div class="label">加餐 kcal</div></div>
        `;

        // 渲染各餐
        const renderMeal = (items, containerId, calId) => {
            const container = document.getElementById(containerId);
            const calEl = document.getElementById(calId);
            if (!items || items.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted);font-size:13px;">暂无推荐</div>';
                calEl.textContent = '';
                return;
            }
            const totalCal = items.reduce((s, it) => s + (it.calories || 0), 0);
            calEl.textContent = `~${Math.round(totalCal)} kcal`;
            container.innerHTML = items.map(it => `
                <div class="diet-food-item">
                    <div class="diet-food-dot"></div>
                    <div>
                        <div class="diet-food-name">${it.name || ''}</div>
                        ${it.reason ? `<div class="diet-food-reason">${it.reason}</div>` : ''}
                    </div>
                    <div class="diet-food-cal">${Math.round(it.calories || 0)} kcal</div>
                </div>
            `).join('');
        };

        renderMeal(plan.breakfast, 'diet-breakfast-items', 'diet-breakfast-cal');
        renderMeal(plan.lunch, 'diet-lunch-items', 'diet-lunch-cal');
        renderMeal(plan.dinner, 'diet-dinner-items', 'diet-dinner-cal');
        renderMeal(plan.snack, 'diet-snack-items', 'diet-snack-cal');

        // AI精细推荐额外内容
        const aiExtra = document.getElementById('diet-ai-extra');
        const aiContent = document.getElementById('diet-ai-content');
        if (type === 'ai' && plan.ai_recommendation) {
            aiExtra.style.display = 'block';
            const ai = plan.ai_recommendation;
            let html = '';
            if (ai.adjustments) {
                html += `<div class="diet-ai-section"><h5>调整说明</h5><p>${ai.adjustments}</p></div>`;
            }
            if (ai.tcm_advice) {
                html += `<div class="diet-ai-section"><h5>中医食疗建议</h5><p>${ai.tcm_advice}</p></div>`;
            }
            if (ai.precautions) {
                html += `<div class="diet-ai-section"><h5>注意事项</h5><p>${ai.precautions}</p></div>`;
            }
            if (!html && ai.raw_response) {
                html = `<div class="diet-ai-section"><h5>AI建议</h5><p>${ai.raw_response}</p></div>`;
            }
            aiContent.innerHTML = html || '<p style="color:var(--text-muted);">暂无额外建议</p>';
        } else {
            aiExtra.style.display = 'none';
        }

        // 滚动到结果
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    async loadDietHistory() {
        try {
            const res = await fetch(`${this.apiBase}/diet/history?student_id=${this.user.student_id}&limit=10`);
            const data = await res.json();
            const container = document.getElementById('diet-history');
            if (!data.success || !data.history || data.history.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:24px;font-size:14px;">暂无推荐记录</div>';
                return;
            }
            container.innerHTML = data.history.map(h => `
                <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-light);">
                    <div style="width:36px;height:36px;border-radius:50%;background:var(--primary-light);display:flex;align-items:center;justify-content:center;color:white;font-size:14px;">
                        <i class="fas fa-${h.recommendation_type === 'ai' ? 'robot' : 'magic'}"></i>
                    </div>
                    <div style="flex:1;">
                        <div style="font-size:14px;font-weight:500;">${h.user_goal || '均衡饮食'} · ${h.constitution || '未指定'}体质</div>
                        <div style="font-size:12px;color:var(--text-muted);">${h.created_at ? new Date(h.created_at).toLocaleDateString() : ''} · ${Math.round(h.target_calories || 0)} kcal</div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            // silent
        }
    },

    // ========== 聊天意图检测：自动跳转膳食推荐 ==========
    detectDietIntent(message) {
        const keywords = ['吃什么', '食谱', '膳食', '推荐菜', '饮食建议', '营养', '减脂餐', '增肌餐', '养生餐', '食疗', '一日三餐', '三餐', '早餐吃什么', '午餐吃什么', '晚餐吃什么'];
        return keywords.some(kw => message.includes(kw));
    },

    // ========== BMI分析 ==========
    async analyzeBMI() {
        const height = parseFloat(document.getElementById('bmi-height').value);
        const weight = parseFloat(document.getElementById('bmi-weight').value);
        const gender = document.querySelector('input[name="bmi-gender"]:checked')?.value || 'male';

        if (!height || !weight) {
            this.toast('请输入身高和体重', 'warning');
            return;
        }

        if (height < 50 || height > 250 || weight < 10 || weight > 300) {
            this.toast('请输入合理的数值', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            const res = await fetch(`${this.apiBase}/diagnosis/bmi`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    height: height,
                    weight: weight,
                    gender: gender,
                    session_id: this.sessionId
                })
            });
            const data = await res.json();

            const resultDiv = document.getElementById('bmi-result');
            if (data.success) {
                const color = data.color || '#10b981';
                const tips = [
                    { icon: 'utensils', title: '饮食建议', content: data.diet_tip, color: '#10b981' },
                    { icon: 'running', title: '运动建议', content: data.exercise_tip, color: '#f59e0b' },
                    { icon: 'bed', title: '生活建议', content: data.lifestyle_tip, color: '#6366f1' }
                ].filter(t => t.content);

                const bmiVal = data.bmi_value != null ? Number(data.bmi_value).toFixed(1) : '-';
                const categoryLabel = data.bmi_category_label || '正常';
                const genderLabel = data.gender === 'female' ? '女' : '男';
                const genderIcon = data.gender === 'female' ? 'venus' : 'mars';

                resultDiv.innerHTML = `
                    <div class="bmi-result-card" style="background:linear-gradient(135deg, rgba(13,148,136,0.08), rgba(20,184,166,0.04));border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;">
                        <div style="padding:24px 20px;text-align:center;border-bottom:1px solid var(--border);">
                            <div style="font-size:13px;color:var(--text-light);margin-bottom:8px;letter-spacing:1px;">您的BMI指数</div>
                            <div style="font-size:52px;font-weight:800;color:${color};line-height:1;letter-spacing:-1px;">${bmiVal}</div>
                            <div style="margin-top:12px;display:inline-flex;align-items:center;gap:6px;padding:6px 18px;background:${color}1a;border:1px solid ${color}40;border-radius:999px;">
                                <span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;"></span>
                                <span style="font-weight:700;color:${color};font-size:14px;">${categoryLabel}</span>
                            </div>
                            <div style="margin-top:14px;display:flex;justify-content:center;gap:20px;font-size:12px;color:var(--text-light);">
                                <span><i class="fas fa-${genderIcon}" style="margin-right:4px;"></i>${genderLabel}</span>
                                <span><i class="fas fa-ruler-vertical" style="margin-right:4px;"></i>${data.height || height} cm</span>
                                <span><i class="fas fa-weight" style="margin-right:4px;"></i>${data.weight || weight} kg</span>
                            </div>
                        </div>
                        ${data.description ? `
                        <div style="padding:16px 20px;font-size:14px;line-height:1.7;color:var(--text-secondary);">
                            <i class="fas fa-info-circle" style="color:var(--primary-lighter);margin-right:6px;"></i>${data.description}
                        </div>` : ''}
                        ${tips.length > 0 ? `
                        <div style="padding:16px 20px;display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:12px;">
                            ${tips.map(t => `
                                <div style="padding:14px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);">
                                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                                        <div style="width:30px;height:30px;border-radius:8px;background:${t.color}1a;display:flex;align-items:center;justify-content:center;">
                                            <i class="fas fa-${t.icon}" style="color:${t.color};font-size:13px;"></i>
                                        </div>
                                        <span style="font-weight:700;font-size:13px;color:var(--text);">${t.title}</span>
                                    </div>
                                    <div style="font-size:13px;color:var(--text-light);line-height:1.6;">${t.content}</div>
                                </div>
                            `).join('')}
                        </div>` : ''}
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `<div style="padding:16px;color:var(--text-muted);text-align:center;">${data.message || '分析失败，请稍后重试'}</div>`;
            }
            resultDiv.classList.add('show');
        } catch (e) {
            const bmi = (weight / ((height / 100) ** 2)).toFixed(1);
            const resultDiv = document.getElementById('bmi-result');
            let category, color;
            if (bmi < 18.5) { category = '偏瘦'; color = '#f59e0b'; }
            else if (bmi < 24) { category = '正常'; color = '#10b981'; }
            else if (bmi < 28) { category = '超重'; color = '#f59e0b'; }
            else { category = '肥胖'; color = '#ef4444'; }
            resultDiv.innerHTML = `
                <div style="padding:24px 20px;text-align:center;background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);border-radius:var(--radius);">
                    <div style="font-size:48px;font-weight:800;color:${color};line-height:1;">${bmi}</div>
                    <div style="margin-top:10px;display:inline-flex;align-items:center;gap:6px;padding:6px 16px;background:${color}1a;border:1px solid ${color}40;border-radius:999px;">
                        <span style="font-weight:700;color:${color};font-size:14px;">${category}</span>
                    </div>
                    <div style="margin-top:12px;font-size:13px;color:var(--text-light);">${this.formatContent('【演示模式】连接服务器失败，以上为本地计算结果。')}</div>
                </div>
            `;
            resultDiv.classList.add('show');
            this.toast('网络连接失败，显示本地结果', 'warning');
        }

        this.showLoading(false);
    },

    // ========== 症状自查 ==========
    async checkSymptoms() {
        const symptoms = document.getElementById('symptom-input').value.trim();
        if (!symptoms) {
            this.toast('请描述症状', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            const res = await fetch(`${this.apiBase}/chat`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    message: '我有以下症状：' + symptoms,
                    session_id: this.sessionId
                })
            });
            const data = await res.json();

            const resultDiv = document.getElementById('symptom-result');
            resultDiv.innerHTML = this.formatContent(data.content);
            resultDiv.classList.add('show');
        } catch (e) {
            this.toast('请求失败，请稍后重试', 'error');
        }

        this.showLoading(false);
    },

    // ========== 场景问答 ==========
    async askScene(question) {
        this.switchPage('chat');
        await new Promise(r => setTimeout(r, 100));
        document.getElementById('chat-input').value = question;
        await this.sendMessage();
    },

    // ========== 健康资讯Feed ==========
    feedCategories: [
        { id: 'all', name: '全部', icon: 'fa-th-large' },
        { id: 'seasonal', name: '季节养生', icon: 'fa-leaf' },
        { id: 'prevention', name: '疾病预防', icon: 'fa-shield-heart' },
        { id: 'nutrition', name: '营养饮食', icon: 'fa-utensils' },
        { id: 'exercise', name: '运动健身', icon: 'fa-dumbbell' },
        { id: 'mental', name: '心理健康', icon: 'fa-brain' },
        { id: 'culture', name: '中医文化', icon: 'fa-yin-yang' }
    ],

    feedData: [
        { id: 1, category: 'seasonal', title: '立秋养生：润肺防燥正当时', icon: 'fa-leaf', color: '#10b981', body: '立秋后气候逐渐干燥，中医认为"秋气通于肺"，此时养生应以润肺生津为主。建议多食银耳、百合、雪梨、蜂蜜等滋阴润肺之品，少食辛辣燥热食物。晨起可做深呼吸练习，助肺气宣发肃降。', date: '2026-08-05', source: '中医养生科' },
        { id: 2, category: 'prevention', title: '秋季感冒预防指南', icon: 'fa-shield-heart', color: '#3b82f6', body: '夏秋交替是感冒高发期。建议：1.早晚及时增减衣物；2.保持室内通风每日2次，每次30分钟；3.勤洗手，用流动水和肥皂；4.适当锻炼增强免疫力；5.保证充足睡眠7-8小时。', date: '2026-08-04', source: '校医院' },
        { id: 3, category: 'nutrition', title: '大学生均衡膳食金字塔', icon: 'fa-utensils', color: '#f59e0b', body: '每日膳食应包含：谷物200-300g（粗细搭配）、蔬菜300-500g（深色过半）、水果200-350g、奶及奶制品300ml、鱼禽蛋肉120-200g、大豆及坚果25-35g。减少油炸食品和含糖饮料摄入。', date: '2026-08-03', source: '营养科' },
        { id: 4, category: 'exercise', title: '适合大学生的5种居家运动', icon: 'fa-dumbbell', color: '#ef4444', body: '1.开合跳：每组30个，做3组；2.平板支撑：每次30秒起步，逐步延长；3.深蹲：每组15个，做3组；4.瑜伽拉伸：每次15分钟；5.跳绳：每次10分钟。每周至少运动3-5次，每次30分钟以上。', date: '2026-08-02', source: '体育部' },
        { id: 5, category: 'mental', title: '考试焦虑的自我调节方法', icon: 'fa-brain', color: '#8b5cf6', body: '考试前感到焦虑是正常反应。尝试：1.腹式呼吸法——吸气4秒、屏息4秒、呼气6秒；2.正念冥想——每天10分钟专注当下；3.合理规划——分解复习任务到每天；4.积极暗示——"我已尽力准备"；5.寻求支持——与朋友或心理咨询师倾诉。', date: '2026-08-01', source: '心理咨询中心' },
        { id: 6, category: 'culture', title: '中医四诊：望闻问切的智慧', icon: 'fa-yin-yang', color: '#6366f1', body: '中医诊断疾病依靠"望闻问切"四诊合参。望诊观察面色、舌象；闻诊听声音、嗅气味；问诊询问症状、病史；切诊把脉、按诊。四诊相互补充，不可偏废。大学生了解四诊基础知识，有助于更好地理解中医整体观念和辨证论治思想，在日常生活中也能初步判断自身健康状况。', date: '2026-07-31', source: '中医科' },
        { id: 7, category: 'seasonal', title: '夏季防中暑：这些信号要警惕', icon: 'fa-sun', color: '#f97316', body: '中暑先兆包括头晕、口渴、多汗、四肢无力。发现后应立即：1.转移到阴凉通风处；2.解开衣扣，平躺休息；3.饮用淡盐水或运动饮料；4.用湿毛巾擦拭身体降温。若出现高热、意识模糊，应立即就医。', date: '2026-07-30', source: '急诊科' },
        { id: 8, category: 'nutrition', title: '熬夜后的饮食补救方案', icon: 'fa-moon', color: '#6366f1', body: '熬夜后身体需要恢复：1.早餐必吃——鸡蛋+全麦面包+牛奶；2.补充维生素B族——粗粮、坚果；3.多喝水——至少2000ml；4.午餐增加深色蔬菜；5.避免高糖高脂零食。建议午间小憩20分钟补充精力。', date: '2026-07-29', source: '营养科' },
        { id: 9, category: 'mental', title: '社交恐惧还是内向？如何区分', icon: 'fa-users', color: '#ec4899', body: '内向是性格特点，享受独处但不怕社交；社交恐惧症则是对社交场合产生强烈的、不合理的恐惧。如果社交恐惧影响到日常生活、学习或人际关系，建议寻求专业帮助。学校心理咨询中心提供免费咨询服务。', date: '2026-07-28', source: '心理咨询中心' },
        { id: 10, category: 'exercise', title: '跑步膝痛？可能是这3个原因', icon: 'fa-person-running', color: '#14b8a6', body: '1.跑姿不正确——脚跟着地冲击大，建议前脚掌或全脚掌着地；2.跑鞋不合适——选择有缓冲的跑鞋，每500-800公里更换；3.训练过量——遵循"10%原则"，每周跑量增加不超过上周的10%。疼痛持续应就医。', date: '2026-07-27', source: '运动医学科' },
        { id: 11, category: 'culture', title: '九种体质自查：你属于哪一种', icon: 'fa-yin-yang', color: '#0d9488', body: '中医将体质分为九种：平和质（最健康）、气虚质（易疲劳）、阳虚质（怕冷）、阴虚质（怕热）、痰湿质（易肥胖）、湿热质（易长痘）、血瘀质（易瘀斑）、气郁质（情绪低落）、特禀质（过敏体质）。了解自己的体质类型，才能针对性养生。', date: '2026-07-26', source: '中医科' },
        { id: 12, category: 'prevention', title: '久坐危害有多大？每天坐8小时缩短寿命', icon: 'fa-chair', color: '#ef4444', body: '研究表明，每天久坐超过8小时与吸烟、肥胖一样危害健康。久坐会导致：1.心血管疾病风险增加147%；2.糖尿病风险增加112%；3.腰椎间盘突出；4.下肢静脉血栓。建议每30分钟起身活动2分钟，做伸展运动或散步。', date: '2026-07-25', source: '骨科' },
        { id: 13, category: 'nutrition', title: '这5种食物帮你提高免疫力', icon: 'fa-shield-heart', color: '#10b981', body: '1.西兰花——富含维生素C和抗氧化物质；2.酸奶——益生菌调节肠道免疫；3.大蒜——大蒜素具有天然抗菌作用；4.蘑菇——含β-葡聚糖增强免疫细胞活性；5.柑橘类水果——维生素C促进白细胞生成。日常饮食中多摄入这些食物，能有效提升身体抵抗力。', date: '2026-07-24', source: '营养科' },
        { id: 14, category: 'mental', title: '失眠三天了怎么办？睡眠卫生七法则', icon: 'fa-bed', color: '#6366f1', body: '1.固定作息——每天同一时间上床和起床；2.睡前1小时远离手机和电脑；3.卧室温度保持18-22°C；4.睡前避免咖啡因和酒精；5.白天午睡不超过30分钟；6.睡前可泡脚或热水澡；7.如果躺下20分钟仍无法入睡，起身做安静的活动。持续失眠超过两周建议就医。', date: '2026-07-23', source: '心理咨询中心' },
        { id: 15, category: 'seasonal', title: '三伏天养生：冬病夏治正当时', icon: 'fa-sun', color: '#f97316', body: '三伏天是一年中最热的时期，也是中医"冬病夏治"的最佳时机。三伏贴疗法利用阳气最盛之时，将辛温药物贴敷于特定穴位，治疗冬季易发作的慢性疾病如哮喘、慢性支气管炎、风湿性关节炎等。日常应注意：1.避免贪凉饮冷；2.适度出汗排毒；3.饮食清淡易消化；4.午休30分钟养心。', date: '2026-07-22', source: '中医针灸科' },
        { id: 16, category: 'exercise', title: '每天一万步真的科学吗？', icon: 'fa-shoe-prints', color: '#3b82f6', body: '"日行万步"源自1960年代日本营销口号，并非严格科学标准。最新研究表明：每天7000-8000步即可获得最大健康收益，超过10000步后收益递减。关键不在于步数，而在于运动强度——建议每天至少有30分钟中等强度快走（心率达到最大心率的60-70%）。体质较弱者可从3000步开始逐步增加。', date: '2026-07-21', source: '体育部' },
        { id: 17, category: 'prevention', title: '手机看多了眼睛干？护眼指南请收好', icon: 'fa-eye', color: '#06b6d4', body: '长时间使用电子产品易导致干眼症和视疲劳。护眼建议：1.遵循20-20-20法则——每20分钟看20英尺(6米)外20秒；2.屏幕亮度与环境光协调；3.屏幕距离眼睛50-70cm；4.有意识多眨眼；5.使用人工泪液缓解干涩；6.定期做眼保健操。出现视力下降、眼痛应到眼科就诊。', date: '2026-07-20', source: '眼科' },
        { id: 18, category: 'nutrition', title: '减肥不吃主食？小心这些危害', icon: 'fa-exclamation-triangle', color: '#f59e0b', body: '完全不吃主食（碳水化合物）减肥危害大：1.大脑缺乏葡萄糖，导致注意力下降、头晕；2.肌肉分解供能，基础代谢降低；3.酮体堆积增加肝肾负担；4.情绪暴躁、易怒；5.恢复饮食后极易反弹。科学减肥应保证每天至少130g碳水化合物，优选全谷物、薯类等低GI主食，配合蛋白质和蔬菜。', date: '2026-07-19', source: '营养科' },
        { id: 19, category: 'mental', title: '如何帮助身边情绪低落的朋友', icon: 'fa-hand-holding-heart', color: '#ec4899', body: '1.倾听不评判——给对方表达的空间，不要急于给建议；2.表达关心——"我在这里陪你"比"别想太多"更有力量；3.鼓励专业求助——建议联系心理咨询中心或热线；4.保持联系——定期问候，让对方感到被惦记；5.注意警示信号——如提到自伤、绝望感，应立即通知学校或家属。记住：你是朋友不是治疗师，专业的事交给专业的人。', date: '2026-07-18', source: '心理咨询中心' },
        { id: 20, category: 'culture', title: '办公室微运动：工间操八段锦', icon: 'fa-spa', color: '#0d9488', body: '八段锦是传统养生功法，动作简单易学，适合办公室练习。八式口诀：1.两手托天理三焦；2.左右开弓似射雕；3.调理脾胃须单举；4.五劳七伤往后瞧；5.摇头摆尾去心火；6.两手攀足固肾腰；7.攒拳怒目增气力；8.背后七颠百病消。每天练习10-15分钟，能舒展筋骨、调节气血、缓解颈肩腰背疲劳。', date: '2026-07-17', source: '中医科' },
        { id: 21, category: 'exercise', title: '运动后肌肉酸痛怎么办？', icon: 'fa-dumbbell', color: '#ef4444', body: '运动后24-72小时出现的肌肉酸痛（DOMS）是正常生理反应。缓解方法：1.轻度有氧运动——慢走或游泳促进血液循环；2.泡沫轴放松——每个部位滚动30-60秒；3.冷热交替浴——冷热水交替冲洗酸痛部位；4.补充蛋白质——运动后30分钟内摄入20-30g蛋白质；5.充足睡眠——肌肉修复主要在深度睡眠期进行。如果疼痛剧烈或持续超过5天，应就医排查损伤。', date: '2026-07-16', source: '运动医学科' },
        { id: 22, category: 'seasonal', title: '白露时节：防寒保暖养正气', icon: 'fa-snowflake', color: '#3b82f6', body: '白露是秋季第三个节气，气温骤降，露凝而白。养生要点：1."白露身不露"——不再赤膊露体，注意保暖；2."春捂秋冻"要适度——体质弱者不宜过度秋冻；3.饮食温润——多食山药、莲子、银耳，少食寒凉瓜果；4.预防秋燥——室内可放水盆或使用加湿器；5.早睡早起——与日同步，收敛神气。', date: '2026-07-15', source: '中医养生科' },
        { id: 11, category: 'prevention', title: '诺如病毒高发期防护要点', icon: 'fa-virus', color: '#dc2626', body: '诺如病毒主要通过污染的食物和水传播。预防：1.饭前便后认真洗手；2.水果蔬菜彻底清洗；3.不喝生水；4.食物彻底煮熟；5.出现呕吐腹泻及时补液。校园内发现病例应及时报告。', date: '2026-07-26', source: '疾控科' },
        { id: 12, category: 'culture', title: '舌苔的秘密：从舌象看健康', icon: 'fa-heart-pulse', color: '#0d9488', body: '中医望舌可辨体质：淡红舌薄白苔为正常；舌淡白多为气血不足或阳虚；舌红少苔多为阴虚；舌暗紫有瘀斑多为血瘀；舌苔厚腻多为痰湿。建议在自然光下观察，晨起空腹最佳。可上传舌象照片让AI帮你分析。', date: '2026-07-25', source: '中医科' },
        { id: 13, category: 'seasonal', title: '三伏天末伏养生：健脾祛湿是关键', icon: 'fa-seedling', color: '#10b981', body: '末伏天气依然闷热，湿气易困脾胃。建议饮食以清淡易消化为主，多食薏米、赤小豆、山药、冬瓜等健脾祛湿之品，少食生冷瓜果和冰饮。避免长时间待在空调房，适当出汗有助排湿。每晚可用温水泡脚15分钟，促进气血运行。', date: '2026-07-24', source: '中医养生科' },
        { id: 14, category: 'prevention', title: '夏季肠道传染病预防手册', icon: 'fa-shield-virus', color: '#3b82f6', body: '夏季是肠道传染病高发期，常见有细菌性痢疾、感染性腹泻等。预防关键在于"管住嘴"：1.不喝生水，不吃变质食物；2.凉拌菜现做现吃；3.海鲜肉类彻底煮熟；4.餐具定期消毒；5.出现腹泻发热及时就医并补液，切勿自行滥用抗生素。', date: '2026-07-23', source: '传染科' },
        { id: 15, category: 'nutrition', title: '健脑食物清单：吃什么提升记忆力', icon: 'fa-bowl-food', color: '#f59e0b', body: '备考期间大脑需要充足营养。推荐健脑食物：1.深海鱼——富含DHA，每周吃2-3次；2.坚果——核桃、杏仁每天一小把；3.鸡蛋——含卵磷脂，每天1-2个；4.蓝莓——抗氧化护脑；5.全谷物——稳定血糖供能。搭配充足睡眠效果更佳，避免过度依赖咖啡因提神。', date: '2026-07-22', source: '营养科' },
        { id: 16, category: 'exercise', title: '宿舍拉伸操：久坐族的救星', icon: 'fa-child-reaching', color: '#ef4444', body: '长时间上课或自习易导致颈肩腰背酸痛。推荐5个宿舍拉伸动作：1.颈部环绕——缓慢左右各5圈；2.肩部上提——每次保持5秒，做10次；3.扩胸伸展——保持15秒；4.坐姿体前屈——拉伸腰背；5.踮脚提踵——促进下肢血液循环。每学习1小时做一组，预防肌肉劳损。', date: '2026-07-21', source: '康复科' },
        { id: 17, category: 'mental', title: '拖延症背后的心理真相', icon: 'fa-clock', color: '#8b5cf6', body: '拖延不全是懒，常与完美主义、恐惧失败有关。破解方法：1.番茄工作法——专注25分钟休息5分钟；2."两分钟原则"——能两分钟做完的事立刻做；3.分解任务——把大目标拆成小步骤；4.降低预期——"先完成再完美"；5.自我奖励——完成阶段性目标后给自己小奖励。必要时可寻求心理咨询帮助。', date: '2026-07-20', source: '心理咨询中心' },
        { id: 18, category: 'culture', title: '经络养生：常用保健穴位图解', icon: 'fa-hand-holding-medical', color: '#0d9488', body: '中医经络穴位是养生瑰宝。推荐三个日常保健穴：1.足三里——外膝眼下四横指，按压可健脾胃、增强免疫；2.合谷穴——虎口处，缓解头痛牙痛；3.涌泉穴——脚底前三分之一凹陷处，搓热可改善睡眠。每穴按压3-5分钟，力度以酸胀为度，长期坚持受益良多。', date: '2026-07-19', source: '针灸推拿科' },
        { id: 19, category: 'seasonal', title: '长夏湿气重，这些信号别忽视', icon: 'fa-droplet', color: '#ec4899', body: '中医称夏末秋初为"长夏"，湿气最盛。湿气重的表现：1.晨起困倦乏力；2.大便黏腻不爽；3.面部出油多；4.舌苔厚腻；5.四肢沉重。祛湿建议：饮食少甜腻，多食茯苓、芡实、扁豆；运动微微出汗；避免淋雨和久居潮湿环境；可用藿香、佩兰泡水代茶饮。', date: '2026-07-18', source: '中医科' },
        { id: 20, category: 'prevention', title: '宿舍卫生防病指南：远离常见病菌', icon: 'fa-spray-can-sparkles', color: '#6366f1', body: '集体宿舍易滋生细菌，做好卫生可有效防病：1.每周清洗床单被套，阳光暴晒杀菌；2.垃圾桶每日清理，避免异味；3.卫生间保持干燥通风，定期用消毒液清洁；4.不共用毛巾、水杯等个人物品；5.开窗通风每日至少2次。良好卫生习惯是预防传染病的第一道防线。', date: '2026-07-17', source: '校医院' }
    ],

    async loadHealthFeed(category) {
        const listEl = document.getElementById('feed-list');
        const catEl = document.getElementById('feed-categories');
        if (!listEl) return;

        if (category !== undefined) {
            this.currentFeedCategory = category;
        }

        // 渲染分类按钮
        if (catEl) {
            catEl.innerHTML = this.feedCategories.map(cat => `
                <button class="feed-category-btn ${cat.id === this.currentFeedCategory ? 'active' : ''}" onclick="app.filterFeed('${cat.id}')">
                    <i class="fas ${cat.icon}"></i> ${cat.name}
                </button>
            `).join('');
        }

        // 过滤资讯数据
        const filtered = this.currentFeedCategory === 'all'
            ? this.feedData
            : this.feedData.filter(item => item.category === this.currentFeedCategory);

        // 渲染资讯列表
        if (filtered.length === 0) {
            listEl.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-inbox" style="font-size:32px;opacity:0.5;"></i><p style="margin-top:8px;">该分类暂无内容</p></div>';
            return;
        }

        listEl.innerHTML = filtered.map(item => `
            <div class="feed-item">
                <div class="feed-item-header">
                    <div class="feed-item-icon" style="background:${item.color};">
                        <i class="fas ${item.icon}"></i>
                    </div>
                    <div>
                        <div class="feed-item-category">${this.feedCategories.find(c => c.id === item.category)?.name || ''}</div>
                        <div class="feed-item-title">${item.title}</div>
                    </div>
                </div>
                <div class="feed-item-summary">${item.body}</div>
                <div class="feed-item-footer">
                    <span><i class="fas fa-hospital"></i> ${item.source}</span>
                    <span><i class="far fa-calendar"></i> ${item.date}</span>
                </div>
            </div>
        `).join('');
    },

    filterFeed(category) {
        this.currentFeedCategory = category;
        this.loadHealthFeed();
    },

    async openFeedArticle(feedId) {
        const modal = document.getElementById('feed-modal');
        const content = document.getElementById('feed-modal-content');
        if (!modal || !content) return;

        content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:24px;"></i><p style="margin-top:8px;">加载中...</p></div>';
        modal.classList.add('show');

        try {
            const res = await fetch(`${this.apiBase}/community/feed/${feedId}?student_id=${this.user.student_id}`);
            const data = await res.json();

            if (data.success) {
                const article = data.article;
                content.innerHTML = `
                    <div class="feed-modal-header">
                        <div>
                            <div style="font-size:12px;color:var(--accent-light);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">${article.category}</div>
                            <div class="feed-modal-title">${article.title}</div>
                        </div>
                        <button class="feed-modal-close" onclick="app.closeFeedModal()"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="feed-modal-meta">
                        <span><i class="fas fa-user-edit"></i> ${article.source}</span>
                        <span><i class="fas fa-tags"></i> ${(article.tags || []).join(' · ')}</span>
                    </div>
                    <div class="feed-modal-body">${(article.content || '').replace(/\n/g, '<br>')}</div>
                `;
            } else {
                content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><p>加载失败</p></div>';
            }
        } catch (e) {
            content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><p>网络错误</p></div>';
        }
    },

    closeFeedModal(event) {
        if (event && event.target.id !== 'feed-modal') return;
        document.getElementById('feed-modal')?.classList.remove('show');
    },

    // ========== 中医体质辨识 ==========
    async startConstitutionQuiz() {
        document.getElementById('constitution-intro').style.display = 'none';
        document.getElementById('constitution-result').style.display = 'none';
        document.getElementById('constitution-quiz').style.display = 'block';

        this.showLoading(true);
        try {
            const res = await fetch(`${this.apiBase}/tcm/constitution/quiz`);
            const data = await res.json();
            this.quizData = data.quiz || [];
            this.quizAnswers = new Array(this.quizData.length).fill(null);
            this.quizIndex = 0;
            this.renderQuizQuestion();
        } catch (e) {
            this.toast('加载问卷失败', 'error');
            document.getElementById('constitution-intro').style.display = 'block';
            document.getElementById('constitution-quiz').style.display = 'none';
        }
        this.showLoading(false);
    },

    renderQuizQuestion() {
        const q = this.quizData[this.quizIndex];
        if (!q) return;

        const markers = ['A', 'B', 'C', 'D'];
        const progress = ((this.quizIndex + 1) / this.quizData.length) * 100;

        document.getElementById('quiz-progress-fill').style.width = progress + '%';
        document.getElementById('quiz-progress-text').textContent = `${this.quizIndex + 1} / ${this.quizData.length}`;
        document.getElementById('quiz-question').textContent = q.question;

        const optionsEl = document.getElementById('quiz-options');
        optionsEl.innerHTML = q.options.map((opt, i) => {
            const isSelected = this.quizAnswers[this.quizIndex] === i;
            return `
                <div class="quiz-option ${isSelected ? 'selected' : ''}" onclick="app.selectQuizOption(${i})">
                    <span class="option-marker">${markers[i]}</span>
                    <span>${opt.text || opt}</span>
                </div>
            `;
        }).join('');

        // 上一题按钮
        document.getElementById('quiz-prev-btn').style.display = this.quizIndex > 0 ? 'inline-flex' : 'none';

        // 下一题/提交按钮
        const nextBtn = document.getElementById('quiz-next-btn');
        const isLast = this.quizIndex === this.quizData.length - 1;
        nextBtn.innerHTML = isLast
            ? '<i class="fas fa-check"></i> 提交测评'
            : '下一题 <i class="fas fa-arrow-right"></i>';
    },

    selectQuizOption(index) {
        this.quizAnswers[this.quizIndex] = index;
        this.renderQuizQuestion();
    },

    prevQuizQuestion() {
        if (this.quizIndex > 0) {
            this.quizIndex--;
            this.renderQuizQuestion();
        }
    },

    async nextQuizQuestion() {
        if (this.quizAnswers[this.quizIndex] === null) {
            this.toast('请选择一个选项', 'warning');
            return;
        }

        if (this.quizIndex < this.quizData.length - 1) {
            this.quizIndex++;
            this.renderQuizQuestion();
        } else {
            await this.submitQuiz();
        }
    },

    async submitQuiz() {
        // 检查是否所有题目都答了
        if (this.quizAnswers.some(a => a === null)) {
            this.toast('请完成所有题目', 'warning');
            return;
        }

        this.showLoading(true);

        // 构建答案数据（后端 assess_constitution 期望 question_id + option_index）
        const answers = this.quizData.map((q, i) => ({
            question_id: q.id,
            option_index: this.quizAnswers[i]
        }));

        try {
            const res = await fetch(`${this.apiBase}/tcm/constitution/assess`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    answers: answers,
                    session_id: this.sessionId
                })
            });
            const data = await res.json();

            if (data.success) {
                this.renderConstitutionResult(data);
            } else {
                this.toast(data.message || '分析失败，请重试', 'error');
            }
        } catch (e) {
            this.toast('网络错误，请稍后重试', 'error');
        }

        this.showLoading(false);
    },

    renderConstitutionResult(data) {
        document.getElementById('constitution-quiz').style.display = 'none';
        const resultEl = document.getElementById('constitution-result');
        resultEl.style.display = 'block';

        const suggestions = data.suggestions || {};
        const risks = data.risks || [];
        const recommendedFoods = data.recommended_foods || [];
        const avoidFoods = data.avoid_foods || [];

        // 九体质占比图：按百分比降序排序，默认显示前2，点击展开看全部
        const constLabels = {pinghe:'平和质', qixu:'气虚质', yangxu:'阳虚质', yinxu:'阴虚质', tanshi:'痰湿质', shire:'湿热质', xueyu:'血瘀质', qiyu:'气郁质', tebin:'特禀质'};
        const percentages = data.percentages || {};
        const constSorted = Object.entries(percentages)
            .map(([k, v]) => ({label: constLabels[k] || k, value: Number(v) || 0}))
            .sort((a, b) => b.value - a.value);
        const constTop2 = constSorted.slice(0, 2);
        const constRest = constSorted.slice(2);
        const constBarHtml = (item, color) => `
                <div style="margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px;">
                        <span style="color:var(--text-secondary);">${item.label}</span>
                        <span style="font-weight:700;color:${color};">${item.value}%</span>
                    </div>
                    <div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;">
                        <div style="width:${item.value}%;height:100%;background:${color};border-radius:4px;transition:width 0.8s cubic-bezier(0.4,0,0.2,1);"></div>
                    </div>
                </div>`;
        const constChartHtml = constSorted.length > 0 ? `
                <div style="padding:16px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:20px;">
                    <div style="font-size:14px;font-weight:700;color:var(--text);margin-bottom:12px;"><i class="fas fa-chart-pie" style="color:var(--primary-lighter);margin-right:6px;"></i>九种体质占比</div>
                    ${constTop2.map((item, i) => constBarHtml(item, i === 0 ? 'var(--primary-lighter)' : 'var(--accent-light)')).join('')}
                    ${constRest.length > 0 ? `
                    <div id="const-chart-extra" style="display:none;margin-top:8px;padding-top:8px;border-top:1px dashed var(--border);">
                        ${constRest.map(item => constBarHtml(item, 'var(--text-light)')).join('')}
                    </div>
                    <button class="btn-secondary" style="width:100%;margin-top:8px;font-size:12px;" onclick="app.toggleChartExpand('const-chart-extra', this, '查看全部9种体质')">
                        <i class="fas fa-chevron-down"></i> 查看全部9种体质
                    </button>` : ''}
                </div>` : '';

        resultEl.innerHTML = `
            <div class="card constitution-result">
                <div class="constitution-type-badge">${data.primary_type || '未知'}</div>
                ${data.secondary_type ? `<p style="color:var(--text-light);font-size:14px;margin-bottom:12px;">兼有 <strong style="color:var(--accent-light);">${data.secondary_type}</strong> 倾向</p>` : ''}
                <div class="constitution-score">${data.score || 0}<span style="font-size:20px;color:var(--text-light);">%</span></div>
                <p style="color:var(--text-light);font-size:13px;margin-bottom:20px;">体质匹配度</p>
                <div class="constitution-desc">${data.description || ''}</div>

                ${constChartHtml}

                ${risks.length > 0 ? `
                <div style="padding:16px;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);border-radius:var(--radius);margin-bottom:20px;">
                    <div style="font-size:14px;font-weight:700;color:var(--danger);margin-bottom:8px;"><i class="fas fa-exclamation-triangle"></i> 易患疾病风险</div>
                    <div style="display:flex;flex-wrap:wrap;gap:8px;">
                        ${risks.map(r => `<span class="food-tag avoid">${r}</span>`).join('')}
                    </div>
                </div>` : ''}

                <div class="constitution-suggestions">
                    ${suggestions.diet ? `
                    <div class="suggestion-card">
                        <h4><i class="fas fa-utensils"></i> 饮食建议</h4>
                        <p>${suggestions.diet}</p>
                    </div>` : ''}
                    ${suggestions.exercise ? `
                    <div class="suggestion-card">
                        <h4><i class="fas fa-running"></i> 运动建议</h4>
                        <p>${suggestions.exercise}</p>
                    </div>` : ''}
                    ${suggestions.lifestyle ? `
                    <div class="suggestion-card">
                        <h4><i class="fas fa-bed"></i> 起居建议</h4>
                        <p>${suggestions.lifestyle}</p>
                    </div>` : ''}
                    ${suggestions.emotion ? `
                    <div class="suggestion-card">
                        <h4><i class="fas fa-heart"></i> 情志调摄</h4>
                        <p>${suggestions.emotion}</p>
                    </div>` : ''}
                </div>

                ${recommendedFoods.length > 0 || avoidFoods.length > 0 ? `
                <div style="margin-top:20px;">
                    <h4 style="font-size:15px;font-weight:700;color:var(--text);margin-bottom:12px;"><i class="fas fa-apple-alt" style="color:var(--primary-lighter);"></i> 食材推荐</h4>
                    ${recommendedFoods.length > 0 ? `
                    <div style="margin-bottom:10px;">
                        <span style="font-size:13px;color:var(--text-light);">推荐食用：</span>
                        <div class="constitution-foods">
                            ${recommendedFoods.map(f => `<span class="food-tag recommended"><i class="fas fa-check"></i> ${f}</span>`).join('')}
                        </div>
                    </div>` : ''}
                    ${avoidFoods.length > 0 ? `
                    <div>
                        <span style="font-size:13px;color:var(--text-light);">建议少食：</span>
                        <div class="constitution-foods">
                            ${avoidFoods.map(f => `<span class="food-tag avoid"><i class="fas fa-times"></i> ${f}</span>`).join('')}
                        </div>
                    </div>` : ''}
                </div>` : ''}

                <div style="margin-top:24px;display:flex;gap:12px;justify-content:center;">
                    <button class="btn-secondary" onclick="app.restartQuiz()">
                        <i class="fas fa-redo"></i> 重新测评
                    </button>
                    <button class="btn-primary" style="max-width:200px;" onclick="app.switchPage('chat')">
                        <i class="fas fa-comments"></i> 咨询AI小艺
                    </button>
                </div>
            </div>
        `;
    },

    restartQuiz() {
        document.getElementById('constitution-result').style.display = 'none';
        document.getElementById('constitution-intro').style.display = 'block';
        this.quizData = [];
        this.quizAnswers = [];
        this.quizIndex = 0;
    },

    // ========== 心理状态测评 ==========
    async startMentalQuiz() {
        const intro = document.getElementById('mental-quiz-intro');
        const result = document.getElementById('mental-quiz-result');
        const quiz = document.getElementById('mental-quiz-container');
        if (intro) intro.style.display = 'none';
        if (result) result.style.display = 'none';
        if (quiz) quiz.style.display = 'block';

        this.showLoading(true);
        try {
            const res = await fetch(`${this.apiBase}/mental/quiz`);
            const data = await res.json();
            this.mentalQuizData = data.quiz || data.questions || [];
            this.mentalQuizAnswers = new Array(this.mentalQuizData.length).fill(null);
            this.mentalQuizIndex = 0;
            if (this.mentalQuizData.length === 0) {
                this.toast('问卷内容为空', 'warning');
            }
            this.renderMentalQuizQuestion();
        } catch (e) {
            this.toast('加载问卷失败', 'error');
            if (intro) intro.style.display = 'block';
            if (quiz) quiz.style.display = 'none';
        }
        this.showLoading(false);
    },

    renderMentalQuizQuestion() {
        if (!this.mentalQuizData || this.mentalQuizData.length === 0) return;
        const q = this.mentalQuizData[this.mentalQuizIndex];
        if (!q) return;

        const markers = ['A', 'B', 'C', 'D', 'E'];
        const progress = ((this.mentalQuizIndex + 1) / this.mentalQuizData.length) * 100;
        const questionText = q.question || q.text || '';
        const options = q.options || [];

        const progressFill = document.getElementById('mental-quiz-progress-fill');
        const progressText = document.getElementById('mental-quiz-progress-text');
        const questionEl = document.getElementById('mental-quiz-question');
        const optionsEl = document.getElementById('mental-quiz-options');
        const prevBtn = document.getElementById('mental-quiz-prev-btn');
        const nextBtn = document.getElementById('mental-quiz-next-btn');

        if (progressFill) progressFill.style.width = progress + '%';
        if (progressText) progressText.textContent = `${this.mentalQuizIndex + 1} / ${this.mentalQuizData.length}`;
        if (questionEl) questionEl.textContent = questionText;

        if (optionsEl) {
            optionsEl.innerHTML = options.map((opt, i) => {
                const isSelected = this.mentalQuizAnswers[this.mentalQuizIndex] === i;
                const label = typeof opt === 'string' ? opt : (opt.text || opt.label || '');
                return `
                    <div class="quiz-option ${isSelected ? 'selected' : ''}" onclick="app.selectMentalQuizOption(${i})">
                        <span class="option-marker">${markers[i] || (i + 1)}</span>
                        <span>${label}</span>
                    </div>
                `;
            }).join('');
        }

        if (prevBtn) prevBtn.style.display = this.mentalQuizIndex > 0 ? 'inline-flex' : 'none';

        if (nextBtn) {
            const isLast = this.mentalQuizIndex === this.mentalQuizData.length - 1;
            nextBtn.innerHTML = isLast
                ? '<i class="fas fa-check"></i> 提交测评'
                : '下一题 <i class="fas fa-arrow-right"></i>';
        }
    },

    selectMentalQuizOption(index) {
        this.mentalQuizAnswers[this.mentalQuizIndex] = index;
        this.renderMentalQuizQuestion();
        // 自动跳到下一题（最后一题除外）
        // 用 timer 管理，防止与手动"下一题"按钮冲突导致跳题
        if (this.mentalQuizIndex < this.mentalQuizData.length - 1) {
            if (this._mentalAutoNextTimer) clearTimeout(this._mentalAutoNextTimer);
            const curIdx = this.mentalQuizIndex;
            this._mentalAutoNextTimer = setTimeout(() => {
                this._mentalAutoNextTimer = null;
                // 仅在用户没有手动切换时才自动跳转
                if (this.mentalQuizIndex === curIdx) {
                    this.mentalQuizIndex++;
                    this.renderMentalQuizQuestion();
                }
            }, 300);
        }
    },

    prevMentalQuizQuestion() {
        if (this._mentalAutoNextTimer) { clearTimeout(this._mentalAutoNextTimer); this._mentalAutoNextTimer = null; }
        if (this.mentalQuizIndex > 0) {
            this.mentalQuizIndex--;
            this.renderMentalQuizQuestion();
        }
    },

    async nextMentalQuizQuestion() {
        // 取消待执行的自动跳转，避免重复跳题
        if (this._mentalAutoNextTimer) { clearTimeout(this._mentalAutoNextTimer); this._mentalAutoNextTimer = null; }
        if (this.mentalQuizAnswers[this.mentalQuizIndex] === null) {
            this.toast('请选择一个选项', 'warning');
            return;
        }
        if (this.mentalQuizIndex < this.mentalQuizData.length - 1) {
            this.mentalQuizIndex++;
            this.renderMentalQuizQuestion();
        } else {
            await this.submitMentalQuiz();
        }
    },

    async submitMentalQuiz() {
        if (this.mentalQuizAnswers.some(a => a === null)) {
            this.toast('请完成所有题目', 'warning');
            return;
        }

        this.showLoading(true);

        const answers = this.mentalQuizData.map((q, i) => ({
            question_id: q.id != null ? q.id : (q.question_id != null ? q.question_id : i),
            option_index: this.mentalQuizAnswers[i]
        }));

        try {
            const res = await fetch(`${this.apiBase}/mental/quiz/assess`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    answers: answers,
                    session_id: this.sessionId
                })
            });
            const data = await res.json();

            if (data.success) {
                this.renderMentalQuizResult(data);
            } else {
                this.toast(data.message || '分析失败，请重试', 'error');
            }
        } catch (e) {
            this.toast('网络错误，请稍后重试', 'error');
        }

        this.showLoading(false);
    },

    renderMentalQuizResult(data) {
        const quizEl = document.getElementById('mental-quiz-container');
        if (quizEl) quizEl.style.display = 'none';
        const resultEl = document.getElementById('mental-quiz-result');
        if (!resultEl) return;
        resultEl.style.display = 'block';

        const score = data.overall_score != null ? data.overall_score : (data.score != null ? data.score : 0);
        const level = data.label || data.level || '';
        const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';

        // 五维度得分
        const dimensions = data.dimensions || data.scores || {};
        const dimList = [
            { key: 'anxiety', label: '焦虑', icon: 'bolt' },
            { key: 'depression', label: '抑郁', icon: 'cloud-rain' },
            { key: 'stress', label: '压力', icon: 'fire' },
            { key: 'sleep', label: '睡眠', icon: 'moon' },
            { key: 'social', label: '社交', icon: 'users' }
        ];
        const dimColors = ['#ef4444', '#6366f1', '#f59e0b', '#8b5cf6', '#14b8a6'];
        // 按得分升序排序（得分最低=最需关注 排前面），默认显示前2，点击展开看全部5个
        const dimDataList = dimList.map((d, i) => {
            const raw = dimensions[d.key] != null ? dimensions[d.key] : (dimensions[d.key + '_score'] != null ? dimensions[d.key + '_score'] : null);
            return {...d, val: raw != null ? Number(raw) : null, color: dimColors[i % dimColors.length]};
        });
        const dimSorted = dimDataList.filter(d => d.val != null).sort((a, b) => a.val - b.val);
        const dimTop2 = dimSorted.slice(0, 2);
        const dimRest = dimSorted.slice(2);
        const hasDims = dimSorted.length > 0;
        const dimBarHtml = (d, needAttention) => {
            const pct = Math.max(0, Math.min(100, d.val));
            const label = needAttention ? `${d.label} <span style="font-size:11px;color:#ef4444;margin-left:4px;">需关注</span>` : d.label;
            return `
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span style="font-size:13px;color:var(--text-secondary);"><i class="fas fa-${d.icon}" style="margin-right:6px;color:${d.color};"></i>${label}</span>
                        <span style="font-size:13px;font-weight:700;color:${d.color};">${d.val}</span>
                    </div>
                    <div style="height:8px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;">
                        <div style="width:${pct}%;height:100%;background:${d.color};transition:width 0.8s cubic-bezier(0.4,0,0.2,1);border-radius:4px;"></div>
                    </div>
                </div>
            `;
        };
        const barsHtml = dimTop2.map(d => dimBarHtml(d, true)).join('');
        const restBarsHtml = dimRest.map(d => dimBarHtml(d, false)).join('');

        // 四类建议
        const advice = data.advice || data.suggestions || {};
        const adviceCards = [
            { key: 'self_regulation', title: '自我调节', icon: 'spa', color: '#6366f1' },
            { key: 'lifestyle', title: '生活方式', icon: 'bed', color: '#10b981' },
            { key: 'social', title: '社交支持', icon: 'users', color: '#14b8a6' },
            { key: 'professional', title: '专业建议', icon: 'user-md', color: '#f59e0b' }
        ];
        const adviceHtml = adviceCards.map(a => {
            const content = advice[a.key] || advice[a.key + '_tip'] || '';
            if (!content) return '';
            return `
                <div style="padding:14px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                        <div style="width:30px;height:30px;border-radius:8px;background:${a.color}1a;display:flex;align-items:center;justify-content:center;">
                            <i class="fas fa-${a.icon}" style="color:${a.color};font-size:13px;"></i>
                        </div>
                        <span style="font-weight:700;font-size:13px;color:var(--text);">${a.title}</span>
                    </div>
                    <div style="font-size:13px;color:var(--text-light);line-height:1.6;">${content}</div>
                </div>
            `;
        }).join('');

        resultEl.innerHTML = `
            <div class="card" style="padding:24px;">
                <div style="text-align:center;margin-bottom:20px;">
                    <div style="font-size:13px;color:var(--text-light);margin-bottom:8px;letter-spacing:1px;">心理健康综合评分</div>
                    <div style="font-size:60px;font-weight:800;color:${color};line-height:1;letter-spacing:-1px;">${score}</div>
                    ${level ? `<div style="margin-top:12px;display:inline-flex;align-items:center;gap:6px;padding:6px 18px;background:${color}1a;border:1px solid ${color}40;border-radius:999px;">
                        <span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;"></span>
                        <span style="font-weight:700;color:${color};font-size:14px;">${level}</span>
                    </div>` : ''}
                </div>

                ${hasDims ? `
                <div style="padding:16px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:20px;">
                    <div style="font-size:14px;font-weight:700;color:var(--text);margin-bottom:12px;"><i class="fas fa-chart-bar" style="color:var(--primary-lighter);margin-right:6px;"></i>五维度分析 <span style="font-size:12px;color:var(--text-light);font-weight:400;margin-left:4px;">（按需关注程度排序）</span></div>
                    ${barsHtml}
                    ${dimRest.length > 0 ? `
                    <div id="mental-dim-extra" style="display:none;margin-top:8px;padding-top:8px;border-top:1px dashed var(--border);">
                        ${restBarsHtml}
                    </div>
                    <button class="btn-secondary" style="width:100%;margin-top:8px;font-size:12px;" onclick="app.toggleChartExpand('mental-dim-extra', this, '查看全部5个维度')">
                        <i class="fas fa-chevron-down"></i> 查看全部5个维度
                    </button>` : ''}
                </div>` : ''}

                ${data.description ? `
                <div style="padding:16px;background:rgba(13,148,136,0.06);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:20px;font-size:14px;line-height:1.7;color:var(--text-secondary);">
                    ${data.description}
                </div>` : ''}

                ${adviceHtml ? `
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px;margin-bottom:20px;">
                    ${adviceHtml}
                </div>` : ''}

                <div style="display:flex;gap:12px;justify-content:center;">
                    <button class="btn-secondary" onclick="app.restartMentalQuiz()">
                        <i class="fas fa-redo"></i> 重新测评
                    </button>
                    <button class="btn-primary" style="max-width:200px;" onclick="app.scrollToMentalChat()">
                        <i class="fas fa-comments"></i> AI倾诉
                    </button>
                </div>
            </div>
        `;
    },

    restartMentalQuiz() {
        const result = document.getElementById('mental-quiz-result');
        const intro = document.getElementById('mental-quiz-intro');
        if (result) result.style.display = 'none';
        if (intro) intro.style.display = 'block';
        this.mentalQuizData = null;
        this.mentalQuizAnswers = [];
        this.mentalQuizIndex = 0;
    },

    // 滚动到心理疏导对话区（心理测评结果按钮用）
    scrollToMentalChat() {
        if (this.currentPage !== 'mental') {
            this.switchPage('mental');
        }
        setTimeout(() => {
            const target = document.querySelector('#page-mental .mental-container');
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 120);
    },

    // 通用展开/收起切换（体质9项占比图、心理5维度图共用）
    toggleChartExpand(extraId, btn, expandText) {
        const extra = document.getElementById(extraId);
        if (!extra) return;
        const isHidden = extra.style.display === 'none';
        extra.style.display = isHidden ? 'block' : 'none';
        if (btn) {
            btn.innerHTML = isHidden
                ? '<i class="fas fa-chevron-up"></i> 收起'
                : `<i class="fas fa-chevron-down"></i> ${expandText || '展开'}`;
        }
    },

    // ========== 健康档案参考（AI问诊页） ==========
    // 汇总体质、心理最近一次测评结果，作为AI问诊参考依据
    async loadHealthSummary() {
        const container = document.getElementById('health-summary');
        if (!container) return;

        container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px;"><i class="fas fa-spinner fa-spin"></i> 加载中...</div>';

        try {
            const sid = this.user.student_id;
            // 并行拉取体质历史和心理历史
            const [tcmRes, mentalRes] = await Promise.all([
                fetch(`${this.apiBase}/tcm/constitution/history?student_id=${sid}`).then(r => r.json()).catch(() => ({})),
                fetch(`${this.apiBase}/mental/assessments?student_id=${sid}`).then(r => r.json()).catch(() => ({}))
            ]);

            const tcmList = tcmRes.history || [];
            const mentalList = mentalRes.assessments || [];
            const latestTcm = tcmList[0] || null;
            const latestMental = mentalList[0] || null;

            // 体质卡片
            let tcmHtml;
            if (latestTcm) {
                const label = latestTcm.primary_type_label || latestTcm.primary_type || '未知';
                const score = latestTcm.score || latestTcm.percentages?.[Object.keys(latestTcm.percentages || {})[0]] || 0;
                const time = latestTcm.created_at ? new Date(latestTcm.created_at).toLocaleDateString('zh-CN') : '';
                tcmHtml = `
                    <div style="padding:14px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                            <i class="fas fa-yin-yang" style="color:var(--primary-lighter);"></i>
                            <span style="font-weight:700;font-size:13px;color:var(--text);">中医体质</span>
                        </div>
                        <div style="font-size:18px;font-weight:800;color:var(--primary-lighter);margin-bottom:4px;">${label}</div>
                        <div style="font-size:12px;color:var(--text-light);">匹配度 ${score}% · ${time}</div>
                    </div>`;
            } else {
                tcmHtml = `
                    <div style="padding:14px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);text-align:center;">
                        <i class="fas fa-yin-yang" style="color:var(--text-muted);font-size:20px;margin-bottom:6px;"></i>
                        <div style="font-size:12px;color:var(--text-muted);">尚未测评</div>
                        <button class="btn-secondary" style="margin-top:8px;font-size:12px;padding:4px 12px;" onclick="app.switchPage('tcm')">去测评</button>
                    </div>`;
            }

            // 心理卡片
            let mentalHtml;
            if (latestMental) {
                const score = latestMental.overall_score != null ? latestMental.overall_score : (latestMental.score || 0);
                const level = latestMental.label || latestMental.level || '';
                const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
                const time = latestMental.created_at ? new Date(latestMental.created_at).toLocaleDateString('zh-CN') : '';
                mentalHtml = `
                    <div style="padding:14px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                            <i class="fas fa-brain" style="color:${color};"></i>
                            <span style="font-weight:700;font-size:13px;color:var(--text);">心理健康</span>
                        </div>
                        <div style="font-size:18px;font-weight:800;color:${color};margin-bottom:4px;">${score} 分 · ${level}</div>
                        <div style="font-size:12px;color:var(--text-light);">${time}</div>
                    </div>`;
            } else {
                mentalHtml = `
                    <div style="padding:14px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);text-align:center;">
                        <i class="fas fa-brain" style="color:var(--text-muted);font-size:20px;margin-bottom:6px;"></i>
                        <div style="font-size:12px;color:var(--text-muted);">尚未测评</div>
                        <button class="btn-secondary" style="margin-top:8px;font-size:12px;padding:4px 12px;" onclick="app.switchPage('mental')">去测评</button>
                    </div>`;
            }

            container.innerHTML = `
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(160px, 1fr));gap:12px;margin-bottom:14px;">
                    ${tcmHtml}
                    ${mentalHtml}
                </div>
                <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
                    <button class="btn-secondary" style="font-size:12px;" onclick="app.switchPage('tcm')">
                        <i class="fas fa-yin-yang"></i> 体质测评
                    </button>
                    <button class="btn-secondary" style="font-size:12px;" onclick="app.switchPage('mental')">
                        <i class="fas fa-brain"></i> 心理测评
                    </button>
                </div>
            `;
        } catch (e) {
            container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px;">加载失败</div>';
        }
    },

    // ========== 积分系统 ==========
    async loadRewardsStats() {
        try {
            const res = await fetch(`${this.apiBase}/rewards/stats?student_id=${this.user.student_id}`);
            const data = await res.json();
            document.getElementById('reward-total').textContent = data.total_points || 0;
            document.getElementById('reward-today').textContent = data.today_points || 0;
            document.getElementById('reward-week').textContent = data.week_points || 0;

            if (data.total_points !== undefined) {
                this.user.total_points = data.total_points;
                document.getElementById('user-points').textContent = data.total_points + ' 积分';
                this.updateMobilePoints();
            }
        } catch (e) {
            console.log('加载积分统计失败');
        }
        // 触发加载成就和打卡状态
        this.loadAchievements();
        this.loadCheckinStatus();
    },

    async loadRewardsHistory() {
        const container = document.getElementById('reward-history');
        if (!container) return;

        try {
            const res = await fetch(`${this.apiBase}/rewards/history?student_id=${this.user.student_id}`);
            const data = await res.json();

            if (!data.history || data.history.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:30px 20px;"><i class="fas fa-inbox" style="font-size:32px;opacity:0.5;"></i><p style="margin-top:8px;font-size:13px;">暂无积分记录</p><p style="font-size:12px;margin-top:4px;">和AI小艺对话即可获得积分</p></div>';
                return;
            }

            container.innerHTML = data.history.map(h => `
                <div class="history-item">
                    <span style="font-size:13px;color:var(--text-secondary);">${h.description}</span>
                    <span style="color:${h.points > 0 ? 'var(--success)' : 'var(--danger)'};font-weight:700;font-size:15px;">
                        ${h.points > 0 ? '+' : ''}${h.points}
                    </span>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;">加载失败</div>';
        }
    },

    async loadLeaderboard() {
        const container = document.getElementById('reward-leaderboard');
        if (!container) return;

        try {
            const res = await fetch(`${this.apiBase}/rewards/leaderboard`);
            const data = await res.json();

            if (!data.leaderboard || data.leaderboard.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:30px 20px;"><i class="fas fa-crown" style="font-size:32px;opacity:0.3;"></i><p style="margin-top:8px;font-size:13px;">暂无排行数据</p></div>';
                return;
            }

            container.innerHTML = data.leaderboard.map((u, i) => `
                <div class="leaderboard-item">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div class="leaderboard-rank ${i < 3 ? 'rank-' + (i + 1) : ''}">${i + 1}</div>
                        <span style="font-size:14px;color:var(--text-secondary);">${u.username}</span>
                    </div>
                    <span style="font-weight:700;color:var(--primary-lighter);font-size:15px;">${u.total_points} 分</span>
                </div>
            `).join('');
        } catch (e) {
            container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;">加载失败</div>';
        }
    },

    // ========== 每日打卡 ==========
    

    renderCheckinStatus(data) {
        const statusDiv = document.getElementById('checkin-status');
        const formDiv = document.getElementById('checkin-form');
        if (!statusDiv) return;

        const streak = data.streak || 0;
        const checkedIn = data.checked_in_today;

        if (checkedIn) {
            const c = data.checkin || {};
            statusDiv.innerHTML = `
                <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:10px;padding:16px;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                        <div style="width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#10b981,#059669);display:flex;align-items:center;justify-content:center;font-size:24px;">🔥</div>
                        <div>
                            <div style="font-size:16px;font-weight:700;color:#10b981;">已连续打卡 ${streak} 天</div>
                            <div style="font-size:12px;color:var(--text-light);">${data.last_checkin || '今天'}</div>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;font-size:12px;">
                        <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.05);border-radius:8px;">
                            <div style="font-size:18px;font-weight:700;color:var(--accent-light);">${c.mood_score || '-'}</div>
                            <div style="color:var(--text-muted);">心情</div>
                        </div>
                        <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.05);border-radius:8px;">
                            <div style="font-size:18px;font-weight:700;color:var(--accent-light);">${c.sleep_hours || '-'}</div>
                            <div style="color:var(--text-muted);">睡眠(h)</div>
                        </div>
                        <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.05);border-radius:8px;">
                            <div style="font-size:18px;font-weight:700;color:var(--accent-light);">${c.exercise_minutes || '-'}</div>
                            <div style="color:var(--text-muted);">运动(min)</div>
                        </div>
                        <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.05);border-radius:8px;">
                            <div style="font-size:18px;font-weight:700;color:var(--accent-light);">${c.water_cups || '-'}</div>
                            <div style="color:var(--text-muted);">饮水(杯)</div>
                        </div>
                    </div>
                </div>
            `;
            formDiv.style.display = 'block';
            if (c.mood_score) document.getElementById('checkin-mood').value = c.mood_score;
            if (c.sleep_hours) document.getElementById('checkin-sleep').value = c.sleep_hours;
            if (c.exercise_minutes) document.getElementById('checkin-exercise').value = c.exercise_minutes;
            if (c.water_cups) document.getElementById('checkin-water').value = c.water_cups;
        } else {
            statusDiv.innerHTML = `
                <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:10px;padding:16px;text-align:center;">
                    <i class="fas fa-calendar-plus" style="font-size:32px;color:#f59e0b;"></i>
                    <p style="margin-top:8px;font-size:14px;color:var(--text-light);">今日尚未打卡</p>
                    <p style="font-size:12px;color:var(--text-muted);margin-top:4px;">${streak > 0 ? '连续打卡' + streak + '天，继续加油！' : '开始你的第一次健康打卡吧！'}</p>
                </div>
            `;
            formDiv.style.display = 'block';
        }
    },

    

    // ========== 成就系统 ==========
    

    renderAchievements(achievements) {
        const grid = document.getElementById('achievements-grid');
        if (!grid) return;

        if (achievements.length === 0) {
            grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:20px;">暂无成就数据</div>';
            return;
        }

        grid.innerHTML = achievements.map(a => `
            <div style="text-align:center;padding:14px 8px;border-radius:12px;background:${a.unlocked ? 'rgba(' + this.hexToRgb(a.color) + ',0.12)' : 'rgba(255,255,255,0.03)'};border:1px solid ${a.unlocked ? 'rgba(' + this.hexToRgb(a.color) + ',0.3)' : 'rgba(255,255,255,0.06)'};transition:all 0.3s;${a.unlocked ? '' : 'opacity:0.5;'}">
                <div style="width:40px;height:40px;border-radius:50%;background:${a.unlocked ? a.color : '#475569'};display:flex;align-items:center;justify-content:center;margin:0 auto 8px;font-size:18px;color:white;">
                    <i class="fas ${a.icon}"></i>
                </div>
                <div style="font-size:12px;font-weight:600;color:${a.unlocked ? a.color : 'var(--text-muted)'};">${a.name}</div>
                <div style="font-size:10px;color:var(--text-muted);margin-top:4px;line-height:1.4;">${a.description}</div>
                ${!a.unlocked ? `<div style="margin-top:6px;height:4px;background:rgba(255,255,255,0.08);border-radius:2px;overflow:hidden;"><div style="height:100%;width:${a.progress}%;background:${a.color};border-radius:2px;"></div></div><div style="font-size:10px;color:var(--text-muted);margin-top:2px;">${a.progress}%</div>` : '<div style="font-size:10px;color:#10b981;margin-top:4px;"><i class="fas fa-check-circle"></i> 已解锁</div>'}
            </div>
        `).join('');
    },

    hexToRgb(hex) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `${r},${g},${b}`;
    },

    // ========== 积分渠道 ==========
    

    renderRewardActions(actions) {
        const container = document.getElementById('reward-actions-list');
        if (!container) return;

        if (actions.length === 0) {
            container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;">暂无渠道数据</div>';
            return;
        }

        container.innerHTML = actions.map(a => {
            const pct = a.daily_limit > 0 ? Math.round(a.completed_today / a.daily_limit * 100) : 0;
            const isDone = a.remaining === 0;
            return `
                <div style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;background:rgba(255,255,255,0.03);margin-bottom:8px;border:1px solid rgba(255,255,255,0.05);">
                    <div style="flex:1;">
                        <div style="font-size:13px;font-weight:600;color:var(--text);">${a.description}</div>
                        <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">今日 ${a.completed_today}/${a.daily_limit} 次</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:14px;font-weight:700;color:${isDone ? 'var(--text-muted)' : 'var(--accent-light)'};">+${a.points} <i class="fas fa-coins" style="font-size:11px;"></i></div>
                        <div style="font-size:10px;color:${isDone ? '#10b981' : 'var(--text-muted)'};">${isDone ? '已完成' : '剩余' + a.remaining + '次'}</div>
                    </div>
                </div>
            `;
        }).join('');
    },

    // ========== 积分商城 ==========
    async loadShopItems() {
        const grid = document.getElementById('shop-grid');
        if (!grid) return;

        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:24px;"></i></div>';

        try {
            const res = await fetch(`${this.apiBase}/rewards/shop?student_id=${this.user.student_id}`);
            const data = await res.json();

            const userPoints = data.user_points || 0;
            const items = data.items || [];

            // 更新积分显示
            const pointsEl = document.getElementById('shop-user-points');
            if (pointsEl) pointsEl.textContent = userPoints + ' 积分';

            // 更新进度条
            const progressFill = document.getElementById('points-progress-fill');
            if (progressFill) {
                const maxCost = 300;
                const pct = Math.min((userPoints / maxCost) * 100, 100);
                progressFill.style.width = pct + '%';
            }

            if (items.length === 0) {
                grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--text-muted);">暂无商品</div>';
                return;
            }

            const categoryColors = {
                '服务': 'linear-gradient(135deg,#0d9488,#14b8a6)',
                '数字': 'linear-gradient(135deg,#6366f1,#818cf8)',
                '实物': 'linear-gradient(135deg,#f59e0b,#fbbf24)',
                '虚拟': 'linear-gradient(135deg,#ec4899,#f472b6)'
            };

            grid.innerHTML = items.map(item => `
                <div class="shop-item">
                    <span class="shop-item-category">${item.category}</span>
                    <div class="shop-item-icon" style="background:${categoryColors[item.category] || categoryColors['服务']}">
                        <i class="fas ${item.icon}"></i>
                    </div>
                    <div class="shop-item-name">${item.name}</div>
                    <div class="shop-item-desc">${item.description}</div>
                    <div class="shop-item-cost"><i class="fas fa-coins"></i>${item.cost}</div>
                    <button class="shop-item-btn" ${!item.affordable ? 'disabled' : ''} onclick="app.exchangeItem('${item.id}')">
                        ${item.affordable ? '立即兑换' : '积分不足'}
                    </button>
                </div>
            `).join('');
        } catch (e) {
            grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--text-muted);">加载失败</div>';
        }
    },

    async exchangeItem(itemId) {
        if (!confirm('确定要兑换此商品吗？')) return;

        this.showLoading(true);
        try {
            const res = await fetch(`${this.apiBase}/rewards/exchange`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    item_id: itemId
                })
            });
            const data = await res.json();

            if (data.success) {
                this.toast(data.message, 'success');
                // 更新积分
                this.user.total_points = data.remaining_points;
                document.getElementById('user-points').textContent = data.remaining_points + ' 积分';
                this.updateMobilePoints();
                // 刷新商城和统计
                this.loadShopItems();
                this.loadRewardsStats();
                this.loadRewardsHistory();
            } else {
                this.toast(data.message || '兑换失败', 'error');
            }
        } catch (e) {
            this.toast('网络错误', 'error');
        }
        this.showLoading(false);
    },

    // ========== 每日打卡 ==========
    async loadCheckinStatus() {
        const container = document.getElementById('checkin-status');
        const formDiv = document.getElementById('checkin-form');
        if (!container) return;

        try {
            const res = await fetch(`${this.apiBase}/checkin/status?student_id=${this.user.student_id}`);
            const data = await res.json();

            if (data.checked_in_today) {
                const c = data.checkin || {};
                const score = c.total_score || 0;
                const scoreColor = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
                
                container.innerHTML = `
                    <div style="padding:20px;background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.2);border-radius:12px;">
                        <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">
                            <div style="width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,${scoreColor}20,${scoreColor}40);display:flex;align-items:center;justify-content:center;border:3px solid ${scoreColor};">
                                <span style="font-size:24px;font-weight:700;color:${scoreColor};">${score}</span>
                            </div>
                            <div>
                                <div style="font-size:18px;font-weight:700;color:${scoreColor};">今日得分 ${score}分</div>
                                <div style="font-size:13px;color:var(--text-light);margin-top:4px;">连续打卡 <strong style="color:var(--primary-lighter);">${data.streak || 1}</strong> 天</div>
                            </div>
                        </div>
                        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:6px;font-size:11px;text-align:center;">
                            <div style="padding:8px 4px;background:rgba(255,255,255,0.03);border-radius:6px;">
                                <div style="color:${c.breakfast_done ? '#10b981' : 'var(--text-muted)'};">${c.breakfast_done ? '✓' : '✗'}</div>
                                <div style="margin-top:2px;">早餐</div>
                            </div>
                            <div style="padding:8px 4px;background:rgba(255,255,255,0.03);border-radius:6px;">
                                <div style="color:${c.lunch_done ? '#10b981' : 'var(--text-muted)'};">${c.lunch_done ? '✓' : '✗'}</div>
                                <div style="margin-top:2px;">午餐</div>
                            </div>
                            <div style="padding:8px 4px;background:rgba(255,255,255,0.03);border-radius:6px;">
                                <div style="color:${c.dinner_done ? '#10b981' : 'var(--text-muted)'};">${c.dinner_done ? '✓' : '✗'}</div>
                                <div style="margin-top:2px;">晚餐</div>
                            </div>
                            <div style="padding:8px 4px;background:rgba(255,255,255,0.03);border-radius:6px;">
                                <div style="font-weight:600;">${c.exercise_minutes || 0}分</div>
                                <div style="margin-top:2px;">运动</div>
                            </div>
                            <div style="padding:8px 4px;background:rgba(255,255,255,0.03);border-radius:6px;">
                                <div style="font-weight:600;">${c.water_cups || 0}杯</div>
                                <div style="margin-top:2px;">饮水</div>
                            </div>
                        </div>
                    </div>
                `;
                // 已打卡，隐藏表单
                if (formDiv) formDiv.style.display = 'none';
            } else {
                container.innerHTML = `
                    <div style="padding:12px;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:8px;text-align:center;">
                        <div style="font-size:13px;color:var(--text-light);">今日尚未打卡</div>
                        <div style="font-size:12px;color:var(--text-muted);margin-top:4px;">${data.streak > 0 ? '已连续打卡' + data.streak + '天，继续加油！' : '完成打卡任务获得积分和得分！'}</div>
                    </div>
                `;
                // 未打卡，显示表单
                if (formDiv) formDiv.style.display = 'block';
            }

            // 加载打卡日历
            this.loadCheckinCalendar();
        } catch (e) {
            container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--text-muted);font-size:13px;">打卡状态加载失败</div>';
        }
    },

    // 更新打卡得分预览
    updateCheckinScore() {
        let score = 0;

        // 三餐打卡（45分）
        if (document.getElementById('checkin-breakfast')?.checked) score += 15;
        if (document.getElementById('checkin-lunch')?.checked) score += 15;
        if (document.getElementById('checkin-dinner')?.checked) score += 15;

        // 运动打卡（20分）
        const exercise = parseInt(document.getElementById('checkin-exercise')?.value) || 0;
        document.getElementById('exercise-value').textContent = exercise;
        if (exercise >= 30) score += 20;
        else if (exercise >= 15) score += 15;
        else if (exercise > 0) score += 10;

        // 饮水打卡（15分）
        const water = parseInt(document.getElementById('checkin-water')?.value) || 0;
        document.getElementById('water-value').textContent = water;
        if (water >= 8) score += 15;
        else if (water >= 5) score += 10;
        else if (water > 0) score += 5;

        // 睡眠打卡（10分）
        const sleep = parseFloat(document.getElementById('checkin-sleep')?.value) || 0;
        document.getElementById('sleep-value').textContent = sleep;
        if (sleep >= 7 && sleep <= 9) score += 10;
        else if ((sleep >= 6 && sleep < 7) || (sleep > 9 && sleep <= 10)) score += 8;
        else if (sleep >= 5 && sleep < 6) score += 5;
        else if (sleep > 0) score += 2;

        // 心情打卡（10分）
        const mood = parseInt(document.getElementById('checkin-mood')?.value) || 5;
        if (mood >= 8) score += 10;
        else if (mood >= 6) score += 8;
        else if (mood >= 4) score += 5;
        else if (mood > 0) score += 2;

        // 更新得分预览
        const scoreEl = document.getElementById('checkin-score-preview');
        if (scoreEl) {
            scoreEl.textContent = score;
            scoreEl.style.color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
        }

        // 更新任务状态样式
        this.updateTaskStyle('task-breakfast', document.getElementById('checkin-breakfast')?.checked);
        this.updateTaskStyle('task-lunch', document.getElementById('checkin-lunch')?.checked);
        this.updateTaskStyle('task-dinner', document.getElementById('checkin-dinner')?.checked);
    },

    updateTaskStyle(taskId, checked) {
        const task = document.getElementById(taskId);
        if (task) {
            if (checked) {
                task.style.background = 'rgba(16,185,129,0.15)';
                task.style.borderColor = '#10b981';
            } else {
                task.style.background = '';
                task.style.borderColor = '';
            }
        }
    },

    // 设置心情
    setMood(score) {
        document.getElementById('checkin-mood').value = score;
        document.querySelectorAll('.mood-btn').forEach(btn => {
            btn.classList.remove('active');
            if (parseInt(btn.dataset.mood) === score) {
                btn.classList.add('active');
            }
        });
        this.updateCheckinScore();
    },

    async performCheckin() {
        const breakfastDone = document.getElementById('checkin-breakfast')?.checked || false;
        const lunchDone = document.getElementById('checkin-lunch')?.checked || false;
        const dinnerDone = document.getElementById('checkin-dinner')?.checked || false;
        const exerciseMinutes = parseInt(document.getElementById('checkin-exercise')?.value) || 0;
        const waterCups = parseInt(document.getElementById('checkin-water')?.value) || 0;
        const sleepHours = parseFloat(document.getElementById('checkin-sleep')?.value) || 0;
        const moodScore = parseInt(document.getElementById('checkin-mood')?.value) || 5;
        const notes = document.getElementById('checkin-notes')?.value.trim();

        this.showLoading(true);
        try {
            const res = await fetch(`${this.apiBase}/checkin`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    breakfast_done: breakfastDone,
                    lunch_done: lunchDone,
                    dinner_done: dinnerDone,
                    exercise_minutes: exerciseMinutes,
                    water_cups: waterCups,
                    sleep_hours: sleepHours,
                    mood_score: moodScore,
                    notes: notes
                })
            });
            const data = await res.json();

            if (data.success) {
                this.toast(data.message || '打卡成功', 'success');
                // 更新积分
                if (data.total_points != null) {
                    this.user.total_points = data.total_points;
                    document.getElementById('user-points').textContent = data.total_points + ' 积分';
                    this.updateMobilePoints();
                } else {
                    this.user.total_points = (this.user.total_points || 0) + (data.points_awarded || 0);
                    document.getElementById('user-points').textContent = this.user.total_points + ' 积分';
                    this.updateMobilePoints();
                }
                // 重新加载打卡状态
                this.loadCheckinStatus();
            } else {
                this.toast(data.message || '打卡失败', 'error');
            }
        } catch (e) {
            this.toast('网络错误，请稍后重试', 'error');
        }
        this.showLoading(false);
    },

    // ========== 打卡日历 ==========

    // 加载打卡日历
    async loadCheckinCalendar() {
        if (!this.user) return;

        const container = document.getElementById('checkin-calendar');
        if (!container) return;

        try {
            const res = await fetch(`${this.apiBase}/checkin/history?student_id=${this.user.student_id}&days=365`);
            const data = await res.json();

            if (data.history && data.history.length > 0) {
                this.renderCheckinCalendar(data.history);
            } else {
                container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px;">暂无打卡记录</div>';
            }
        } catch (e) {
            container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px;">加载失败</div>';
        }
    },

    // 渲染打卡日历
    renderCheckinCalendar(history) {
        const container = document.getElementById('checkin-calendar');
        if (!container) return;

        // 将打卡记录转换为日期->记录的映射
        const checkinMap = {};
        history.forEach(r => {
            checkinMap[r.checkin_date] = r;
        });

        // 获取当前月份
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth();
        const today = now.getDate();

        // 计算本月打卡天数和总得分
        let monthCheckinCount = 0;
        let monthTotalScore = 0;
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        
        for (let d = 1; d <= today; d++) {
            const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            if (checkinMap[dateStr]) {
                monthCheckinCount++;
                monthTotalScore += checkinMap[dateStr].total_score || 0;
            }
        }

        // 计算平均日分
        const avgDailyScore = monthCheckinCount > 0 ? Math.round(monthTotalScore / monthCheckinCount) : 0;

        // 生成日历HTML
        const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
        const dayNames = ['日', '一', '二', '三', '四', '五', '六'];

        // 计算本月第一天是星期几
        const firstDay = new Date(currentYear, currentMonth, 1).getDay();

        // 生成日历网格
        let calendarHTML = `
            <div style="margin-bottom:16px;">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                    <h4 style="font-size:15px;margin:0;color:var(--text);">${currentYear}年${monthNames[currentMonth]}</h4>
                </div>
                <!-- 得分统计 -->
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px;">
                    <div style="text-align:center;padding:12px;background:rgba(16,185,129,0.06);border-radius:8px;">
                        <div style="font-size:20px;font-weight:700;color:#10b981;">${monthTotalScore}</div>
                        <div style="font-size:11px;color:var(--text-muted);">本月总分</div>
                    </div>
                    <div style="text-align:center;padding:12px;background:rgba(13,148,136,0.06);border-radius:8px;">
                        <div style="font-size:20px;font-weight:700;color:var(--primary-lighter);">${monthCheckinCount}</div>
                        <div style="font-size:11px;color:var(--text-muted);">打卡天数</div>
                    </div>
                    <div style="text-align:center;padding:12px;background:rgba(245,158,11,0.06);border-radius:8px;">
                        <div style="font-size:20px;font-weight:700;color:#f59e0b;">${avgDailyScore}</div>
                        <div style="font-size:11px;color:var(--text-muted);">平均日分</div>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;text-align:center;margin-bottom:8px;">
                    ${dayNames.map(d => `<div style="font-size:12px;color:var(--text-muted);padding:4px 0;">${d}</div>`).join('')}
                </div>
                <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;">
        `;

        // 填充空白天数
        for (let i = 0; i < firstDay; i++) {
            calendarHTML += '<div style="height:48px;"></div>';
        }

        // 填充日期
        for (let d = 1; d <= daysInMonth; d++) {
            const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const checkin = checkinMap[dateStr];
            const isChecked = !!checkin;
            const isToday = d === today;
            const isFuture = d > today;
            const score = checkin ? (checkin.total_score || 0) : 0;

            let bgColor = 'transparent';
            let textColor = 'var(--text-light)';
            let borderColor = 'transparent';

            if (isChecked) {
                // 根据得分设置颜色
                if (score >= 80) {
                    bgColor = 'rgba(16,185,129,0.2)';
                    textColor = '#10b981';
                    borderColor = 'rgba(16,185,129,0.5)';
                } else if (score >= 60) {
                    bgColor = 'rgba(245,158,11,0.2)';
                    textColor = '#f59e0b';
                    borderColor = 'rgba(245,158,11,0.5)';
                } else {
                    bgColor = 'rgba(239,68,68,0.2)';
                    textColor = '#ef4444';
                    borderColor = 'rgba(239,68,68,0.5)';
                }
            } else if (isToday) {
                bgColor = 'rgba(13,148,136,0.1)';
                textColor = 'var(--primary-lighter)';
                borderColor = 'var(--primary-lighter)';
            } else if (isFuture) {
                textColor = 'var(--text-muted)';
            }

            calendarHTML += `
                <div style="height:48px;display:flex;flex-direction:column;align-items:center;justify-content:center;border-radius:6px;background:${bgColor};color:${textColor};font-size:12px;font-weight:${isChecked || isToday ? '600' : '400'};border:1px solid ${borderColor};${isFuture ? 'opacity:0.5;' : ''}padding:2px;">
                    <div>${d}</div>
                    ${isChecked ? `<div style="font-size:9px;margin-top:1px;">${score}分</div>` : ''}
                </div>
            `;
        }

        calendarHTML += '</div></div>';

        // 添加图例
        calendarHTML += `
            <div style="display:flex;justify-content:center;gap:12px;font-size:11px;color:var(--text-muted);margin-top:12px;flex-wrap:wrap;">
                <div style="display:flex;align-items:center;gap:4px;">
                    <div style="width:14px;height:14px;border-radius:3px;background:rgba(16,185,129,0.2);border:1px solid rgba(16,185,129,0.5);"></div>
                    <span>80分以上</span>
                </div>
                <div style="display:flex;align-items:center;gap:4px;">
                    <div style="width:14px;height:14px;border-radius:3px;background:rgba(245,158,11,0.2);border:1px solid rgba(245,158,11,0.5);"></div>
                    <span>60-79分</span>
                </div>
                <div style="display:flex;align-items:center;gap:4px;">
                    <div style="width:14px;height:14px;border-radius:3px;background:rgba(239,68,68,0.2);border:1px solid rgba(239,68,68,0.5);"></div>
                    <span>60分以下</span>
                </div>
                <div style="display:flex;align-items:center;gap:4px;">
                    <div style="width:14px;height:14px;border-radius:3px;background:rgba(13,148,136,0.1);border:1px solid var(--primary-lighter);"></div>
                    <span>今天</span>
                </div>
            </div>
        `;

        container.innerHTML = calendarHTML;
    },

    // ========== 成就系统 ==========
    async loadAchievements() {
        const grid = document.getElementById('achievements-grid');
        if (!grid) return;

        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:24px;"></i></div>';

        try {
            const res = await fetch(`${this.apiBase}/rewards/achievements?student_id=${this.user.student_id}`);
            const data = await res.json();
            const achievements = data.achievements || [];

            if (achievements.length === 0) {
                grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--text-muted);"><i class="fas fa-trophy" style="font-size:32px;opacity:0.5;"></i><p style="margin-top:8px;font-size:13px;">暂无成就</p></div>';
                return;
            }

            grid.innerHTML = achievements.map(a => {
                const unlocked = a.unlocked || a.is_unlocked;
                const progress = Math.min(100, a.progress || 0);
                const opacity = unlocked ? '1' : '0.5';
                return `
                    <div class="achievement-item" style="padding:16px;background:${unlocked ? 'rgba(16,185,129,0.06)' : 'var(--bg-glass)'};border:1px solid ${unlocked ? 'rgba(16,185,129,0.3)' : 'var(--border)'};border-radius:var(--radius);text-align:center;opacity:${opacity};transition:all 0.3s;">
                        <div style="width:48px;height:48px;border-radius:50%;background:${unlocked ? 'linear-gradient(135deg,#10b981,#34d399)' : 'rgba(255,255,255,0.05)'};display:flex;align-items:center;justify-content:center;margin:0 auto 10px;">
                            <i class="fas fa-${a.icon || 'medal'}" style="color:${unlocked ? '#fff' : 'var(--text-muted)'};font-size:20px;"></i>
                        </div>
                        <div style="font-weight:700;font-size:13px;color:var(--text);margin-bottom:4px;">${a.name || a.title || '成就'}</div>
                        <div style="font-size:12px;color:var(--text-light);margin-bottom:8px;line-height:1.4;">${a.description || ''}</div>
                        ${unlocked ? `<div style="font-size:11px;color:var(--success);font-weight:600;"><i class="fas fa-check"></i> 已解锁</div>` : `
                        <div style="height:6px;background:rgba(255,255,255,0.05);border-radius:3px;overflow:hidden;margin-top:6px;">
                            <div style="width:${progress}%;height:100%;background:var(--primary);border-radius:3px;transition:width 0.6s;"></div>
                        </div>
                        <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${progress}%</div>`}
                    </div>
                `;
            }).join('');
        } catch (e) {
            grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--text-muted);">加载失败</div>';
        }
    },

    async loadRewardActions() {
        const list = document.getElementById('reward-actions-list');
        if (!list) return;

        list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:20px;"></i></div>';

        try {
            const res = await fetch(`${this.apiBase}/rewards/overview?student_id=${this.user.student_id}`);
            const data = await res.json();
            const actions = data.available_actions || data.actions || [];

            if (actions.length === 0) {
                list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px;">暂无积分渠道</div>';
                return;
            }

            list.innerHTML = actions.map(a => {
                const completed = a.today_count || a.completed_today || 0;
                const limit = a.daily_limit || a.limit || 0;
                const reached = limit > 0 && completed >= limit;
                return `
                    <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px;background:var(--bg-glass);border:1px solid var(--border);border-radius:var(--radius);">
                        <div style="flex:1;">
                            <div style="font-size:13px;color:var(--text-secondary);font-weight:500;">${a.description || a.name || ''}</div>
                            ${limit > 0 ? `<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">今日 ${completed} / ${limit}</div>` : ''}
                        </div>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <span style="font-weight:700;color:${reached ? 'var(--text-muted)' : 'var(--success)'};font-size:14px;">+${a.points || 0}</span>
                            ${reached ? '<i class="fas fa-check-circle" style="color:var(--success);font-size:14px;"></i>' : ''}
                        </div>
                    </div>
                `;
            }).join('');
        } catch (e) {
            list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px;">加载失败</div>';
        }
    },

    // ========== 医案溯源 ==========
    async openCaseModal(caseId) {
        const modal = document.getElementById('case-modal');
        const content = document.getElementById('case-modal-content');
        if (!modal || !content) return;

        content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:24px;"></i><p style="margin-top:8px;">加载医案中...</p></div>';
        modal.classList.add('show');

        try {
            const res = await fetch(`${this.apiBase}/tcm/case/${caseId}`);
            const data = await res.json();

            if (data.success) {
                const c = data.case;
                const pi = c.patient_info || {};
                const pe = c.physical_examination || {};
                const dg = c.diagnosis || {};
                const tr = c.treatment || {};

                content.innerHTML = `
                    <div class="case-modal-header">
                        <h3><i class="fas fa-file-medical"></i> 医案 ${c.case_id}</h3>
                        <button class="case-modal-close" onclick="app.closeCaseModal()"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="case-modal-body">
                        <div class="case-section">
                            <div class="case-section-title"><i class="fas fa-user"></i> 患者信息</div>
                            <div class="case-info-grid">
                                <div class="case-info-item"><label>年龄</label><value>${pi.age || '-'}岁</value></div>
                                <div class="case-info-item"><label>性别</label><value>${pi.gender || '-'}</value></div>
                                <div class="case-info-item"><label>职业</label><value>${pi.occupation || '-'}</value></div>
                                <div class="case-info-item"><label>既往病史</label><value>${pi.medical_history || '无'}</value></div>
                            </div>
                        </div>

                        <div class="case-section">
                            <div class="case-section-title"><i class="fas fa-comment-medical"></i> 主诉</div>
                            <div class="case-section-content">${c.chief_complaint || '-'}</div>
                        </div>

                        <div class="case-section">
                            <div class="case-section-title"><i class="fas fa-clipboard-list"></i> 现病史</div>
                            <div class="case-section-content">${c.present_illness || '-'}</div>
                        </div>

                        <div class="case-section">
                            <div class="case-section-title"><i class="fas fa-search"></i> 体征检查</div>
                            <div class="case-info-grid">
                                <div class="case-info-item"><label>舌象</label><value>${pe.tongue || '-'}</value></div>
                                <div class="case-info-item"><label>脉象</label><value>${pe.pulse || '-'}</value></div>
                                <div class="case-info-item"><label>其他体征</label><value>${pe.other_signs || '-'}</value></div>
                            </div>
                        </div>

                        <div class="case-section">
                            <div class="case-section-title"><i class="fas fa-stethoscope"></i> 诊断</div>
                            <div class="case-info-grid">
                                <div class="case-info-item"><label>中医疾病</label><value>${dg.disease || '-'}</value></div>
                                <div class="case-info-item"><label>证候</label><value>${dg.syndrome || '-'}</value></div>
                                <div class="case-info-item"><label>西医诊断</label><value>${dg.western_diagnosis || '-'}</value></div>
                            </div>
                        </div>

                        <div class="case-section">
                            <div class="case-section-title"><i class="fas fa-prescription-bottle-medical"></i> 治疗方案</div>
                            <div class="case-section-content">
                                <p style="margin-bottom:8px;"><strong style="color:var(--primary-lighter);">方剂：</strong>${tr.herbal_medicine || '-'}</p>
                                ${tr.acupuncture && tr.acupuncture !== '无' ? `<p style="margin-bottom:8px;"><strong style="color:var(--primary-lighter);">针灸：</strong>${tr.acupuncture}</p>` : ''}
                                <p style="margin-bottom:8px;"><strong style="color:var(--primary-lighter);">饮食建议：</strong>${tr.dietary_advice || '-'}</p>
                                <p><strong style="color:var(--primary-lighter);">生活建议：</strong>${tr.lifestyle_advice || '-'}</p>
                            </div>
                        </div>

                        <div class="case-section">
                            <div class="case-section-title"><i class="fas fa-chart-line"></i> 治疗结果</div>
                            <div class="case-section-content">${c.outcome || '-'}</div>
                        </div>

                        <div class="case-section">
                            <div class="case-section-title"><i class="fas fa-phone"></i> 随访</div>
                            <div class="case-section-content">${c.follow_up || '-'}</div>
                        </div>

                        <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border);text-align:center;">
                            <span style="font-size:12px;color:var(--text-muted);"><i class="fas fa-database"></i> 数据来源：${c.source || '中医病例数据库'}</span>
                        </div>
                    </div>
                `;
            } else {
                content.innerHTML = `
                    <div style="text-align:center;padding:40px;">
                        <i class="fas fa-exclamation-circle" style="font-size:32px;color:var(--text-muted);"></i>
                        <p style="margin-top:12px;color:var(--text-muted);">${data.message || '医案不存在'}</p>
                        <button class="btn-secondary" style="margin-top:16px;" onclick="app.closeCaseModal()">关闭</button>
                    </div>
                `;
            }
        } catch (e) {
            content.innerHTML = `
                <div style="text-align:center;padding:40px;">
                    <i class="fas fa-wifi" style="font-size:32px;color:var(--text-muted);"></i>
                    <p style="margin-top:12px;color:var(--text-muted);">网络错误，请稍后重试</p>
                    <button class="btn-secondary" style="margin-top:16px;" onclick="app.closeCaseModal()">关闭</button>
                </div>
            `;
        }
    },

    closeCaseModal(event) {
        if (event && event.target.id !== 'case-modal') return;
        document.getElementById('case-modal')?.classList.remove('show');
    },

    // ========== 医案库 ==========
    async openCaseLibrary() {
        const modal = document.getElementById('case-library-modal');
        const content = document.getElementById('case-library-modal-content');
        if (!modal || !content) return;

        content.innerHTML = `
            <div class="case-library-header">
                <h3><i class="fas fa-book-medical"></i> 医案库</h3>
                <button class="case-library-close" onclick="app.closeCaseLibraryModal()"><i class="fas fa-times"></i></button>
            </div>
            <div class="case-library-body">
                <div class="case-library-toolbar">
                    <div class="search-box">
                        <i class="fas fa-search"></i>
                        <input type="text" id="case-library-search" placeholder="搜索症状、病名、证型、方剂..." onkeydown="app.handleCaseLibrarySearch(event)">
                    </div>
                    <div class="filter-tabs" id="case-library-tabs"></div>
                </div>
                <div class="case-library-grid" id="case-library-grid">
                    <div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:24px;"></i><p style="margin-top:8px;">加载医案库...</p></div>
                </div>
            </div>
        `;
        modal.classList.add('show');
        await this.loadCaseLibrary();
    },

    closeCaseLibraryModal(event) {
        if (event && event.target.id !== 'case-library-modal') return;
        document.getElementById('case-library-modal')?.classList.remove('show');
    },

    async loadCaseLibrary() {
        try {
            const res = await fetch(`${this.apiBase}/tcm/cases?page_size=20`);
            const data = await res.json();
            
            if (data.success) {
                this.caseLibraryData = data.cases;
                this.caseLibraryCategories = data.categories || [];
                this.renderCaseLibraryTabs();
                this.renderCaseLibraryGrid(data.cases);
            }
        } catch (e) {
            console.error('加载医案库失败:', e);
            const grid = document.getElementById('case-library-grid');
            if (grid) grid.innerHTML = '<div style="text-align:center;padding:40px;color:var(--danger);">加载失败，请重试</div>';
        }
    },

    renderCaseLibraryTabs() {
        const tabsContainer = document.getElementById('case-library-tabs');
        if (!tabsContainer) return;
        
        // 从分类中提取唯一的病种作为标签
        const diseases = [...new Set(this.caseLibraryData.map(c => c.disease).filter(Boolean))];
        const topDiseases = diseases.slice(0, 8); // 显示前8个
        
        tabsContainer.innerHTML = `
            <button class="filter-tab active" data-filter="all" onclick="app.filterCaseLibrary('all')">全部</button>
            ${topDiseases.map(d => `<button class="filter-tab" data-filter="${d}" onclick="app.filterCaseLibrary('${d}')">${d}</button>`).join('')}
        `;
    },

    filterCaseLibrary(filter) {
        // 更新标签状态
        document.querySelectorAll('#case-library-tabs .filter-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        let filtered = this.caseLibraryData;
        if (filter !== 'all') {
            filtered = this.caseLibraryData.filter(c => c.disease === filter);
        }
        this.renderCaseLibraryGrid(filtered);
    },

    async handleCaseLibrarySearch(e) {
        if (e.key !== 'Enter') return;
        
        const query = e.target.value.trim();
        if (!query) {
            this.renderCaseLibraryGrid(this.caseLibraryData);
            return;
        }

        const grid = document.getElementById('case-library-grid');
        grid.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin"></i><p style="margin-top:8px;">搜索中...</p></div>';

        try {
            const res = await fetch(`${this.apiBase}/tcm/cases/search?q=${encodeURIComponent(query)}&limit=20`);
            const data = await res.json();
            
            if (data.success) {
                this.renderCaseLibraryGrid(data.cases, true);
            }
        } catch (err) {
            grid.innerHTML = '<div style="text-align:center;padding:40px;color:var(--danger);">搜索失败</div>';
        }
    },

    renderCaseLibraryGrid(cases, isSearchResult = false) {
        const grid = document.getElementById('case-library-grid');
        if (!grid) return;

        if (!cases.length) {
            grid.innerHTML = `
                <div style="text-align:center;padding:60px 20px;color:var(--text-muted);">
                    <i class="fas fa-search" style="font-size:48px;margin-bottom:16px;opacity:0.3;"></i>
                    <p style="font-size:16px;">${isSearchResult ? '未找到相关医案' : '暂无医案数据'}</p>
                    <p style="font-size:13px;margin-top:8px;">尝试调整搜索关键词或浏览全部分类</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = cases.map(c => `
            <div class="case-library-card" onclick="app.openCaseModal('${c.case_id}')">
                <div class="case-card-header">
                    <span class="case-card-id">${c.case_id}</span>
                    <span class="case-card-disease">${c.disease || '未知病症'}</span>
                </div>
                <div class="case-card-body">
                    <p class="case-card-complaint">${c.chief_complaint || '无主诉记录'}</p>
                    <div class="case-card-meta">
                        <span><i class="fas fa-user"></i> ${c.patient_age || '-'}岁 ${c.patient_gender || '-'}</span>
                        <span><i class="fas fa-tag"></i> ${c.syndrome || '未分型'}</span>
                    </div>
                </div>
                <div class="case-card-footer">
                    <i class="fas fa-chevron-right"></i>
                    <span>查看详情</span>
                </div>
            </div>
        `).join('');
    },

    // ========== 隐私设置 ==========
    async loadPrivacySettings() {
        try {
            const res = await fetch(`${this.apiBase}/auth/profile?student_id=${this.user.student_id}`);
            const data = await res.json();
            document.getElementById('privacy-alert').checked = data.user?.alert_enabled || false;
        } catch (e) {
            console.log('加载隐私设置失败');
        }
    },

    async updatePrivacy() {
        const alertEnabled = document.getElementById('privacy-alert').checked;

        try {
            await fetch(`${this.apiBase}/auth/privacy`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    alert_enabled: alertEnabled
                })
            });
            this.toast(alertEnabled ? '心理预警已开启' : '心理预警已关闭', 'success');
        } catch (e) {
            this.toast('更新失败，请稍后重试', 'error');
        }
    },

    async exportData() {
        this.toast('正在生成健康档案...', 'info');
        try {
            const res = await fetch(`${this.apiBase}/health/records?student_id=${this.user.student_id}`);
            const data = await res.json();
            const records = data.records || [];

            if (records.length === 0) {
                this.toast('暂无健康档案数据', 'warning');
                return;
            }

            const exportData = {
                export_date: new Date().toISOString(),
                student_id: this.user.student_id,
                username: this.user.username,
                total_records: records.length,
                records: records
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `健康档案_${this.user.student_id}_${new Date().toISOString().slice(0, 10)}.json`;
            a.click();
            URL.revokeObjectURL(url);
            this.toast('健康档案已导出', 'success');
        } catch (e) {
            this.toast('导出失败', 'error');
        }
    },

    async deleteAccount() {
        if (!confirm('确定要删除账户数据吗？此操作不可恢复！')) return;
        if (!confirm('再次确认：所有对话记录、健康档案将被永久删除！')) return;

        this.toast('正在删除数据...', 'info');
        try {
            await fetch(`${this.apiBase}/auth/delete`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({student_id: this.user.student_id})
            });
            this.toast('账户数据已永久删除', 'success');
        } catch (e) {
            this.toast('服务器删除失败，仅清除本地数据', 'warning');
        }
        localStorage.removeItem('zhiyi_user');
        setTimeout(() => location.reload(), 1500);
    },

    // ========== 工具 ==========
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (!overlay) return;
        
        if (show) {
            overlay.style.display = 'flex';
            // 随机显示不同的思考提示语
            const messages = [
                '🧠 小艺正在思考...',
                '📚 查阅专业资料...',
                '💡 分析中 请稍候...',
                '🔍 与医案数据库联想...',
                '🌿 提取健康建议...'
            ];
            const p = overlay.querySelector('p');
            if (p) {
                p.textContent = messages[Math.floor(Math.random() * messages.length)];
            }
            this.setMascotPose('thinking');
        } else {
            overlay.style.display = 'none';
            this.setMascotPose('idle');
        }
    },

    formatContent(text) {
        if (!text) return '';
        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/【(.+?)】/g, '<span style="font-weight:700;color:var(--primary-lighter);">【$1】</span>')
            .replace(/(?:\[)?医案\s*(C\d{3})(?:\])?/g, '<span class="case-ref" onclick="app.openCaseModal(\'$1\')" style="color:var(--primary-lighter);cursor:pointer;text-decoration:underline;font-weight:600;">[医案 $1] <i class="fas fa-external-link-alt" style="font-size:11px;"></i></span>');
        return `<div style="line-height:1.8;font-size:14px;">${html}</div>`;
    },

    // ========== 人物形象动作切换 ==========
    // 动作类型：idle(待机挥手) / thinking(思考倾听) / happy(开心) / guide(指引建议)
    mascotPoses: ['idle', 'thinking', 'happy', 'guide'],
    mascotCurrentPose: 'idle',
    _mascotRevertTimer: null,
    _mascotIdleTimer: null,

    // 切换人物形象动作，revertAfterMs 指定后自动回到 idle
    setMascotPose(pose, revertAfterMs = 0) {
        const img = document.getElementById('mascot-img');
        if (!img) return;
        if (pose === this.mascotCurrentPose && !revertAfterMs) return;

        // 清除之前的自动恢复定时器
        if (this._mascotRevertTimer) { clearTimeout(this._mascotRevertTimer); this._mascotRevertTimer = null; }

        // 淡出 → 换图 → 淡入
        img.style.opacity = '0';
        setTimeout(() => {
            img.src = `img/mascot_${pose}.png`;
            img.style.opacity = '1';
            this.mascotCurrentPose = pose;
        }, 150);

        // 指定时间后自动回到 idle
        if (revertAfterMs > 0) {
            this._mascotRevertTimer = setTimeout(() => {
                this._mascotRevertTimer = null;
                this.setMascotPose('idle');
            }, revertAfterMs);
        }
    },

    // 点击人物形象 → 开心动作 → 跳转对话页
    onAvatarClick() {
        this.setMascotPose('happy', 800);
        setTimeout(() => this.switchPage('chat'), 300);
    },

    // 启动待机动画：每隔 5-8 秒随机在 idle、thinking、happy 之间切换，让人物更"活"
    startMascotIdleAnimation() {
        const availablePoses = ['idle', 'thinking', 'idle', 'happy', 'idle']; // 60% idle, 20% thinking, 20% happy
        
        const scheduleNext = () => {
            const delay = 5000 + Math.random() * 3000; // 5-8秒
            this._mascotIdleTimer = setTimeout(() => {
                // 仅在当前是 idle 时才随机切换
                if (this.mascotCurrentPose === 'idle') {
                    const randomPose = availablePoses[Math.floor(Math.random() * availablePoses.length)];
                    if (randomPose !== 'idle') {
                        this.setMascotPose(randomPose, 2500);
                    } else {
                        // 继续idle，但做一个轻微动画
                        this.setMascotPose(randomPose, 1500);
                    }
                }
                scheduleNext();
            }, delay);
        };
        scheduleNext();
    },

    // 停止待机动画（页面卸载时调用）
    stopMascotIdleAnimation() {
        if (this._mascotIdleTimer) { clearTimeout(this._mascotIdleTimer); this._mascotIdleTimer = null; }
        if (this._mascotRevertTimer) { clearTimeout(this._mascotRevertTimer); this._mascotRevertTimer = null; }
    },

    // ========== 饮食记录功能 ==========

    // 初始化饮食记录日期和时间
    initDietLog() {
        const dateInput = document.getElementById('diet-log-date');
        const timeInput = document.getElementById('diet-log-time');
        if (dateInput) {
            dateInput.value = new Date().toISOString().split('T')[0];
        }
        if (timeInput) {
            const now = new Date();
            timeInput.value = now.toTimeString().slice(0, 5);
        }
    },

    // 添加饮食记录
    async addDietLog() {
        if (!this.user) {
            this.toast('请先登录', 'warning');
            return;
        }

        const date = document.getElementById('diet-log-date').value;
        const time = document.getElementById('diet-log-time').value;
        const mealType = document.getElementById('diet-log-meal').value;
        const foodName = document.getElementById('diet-log-food').value.trim();
        const servingSize = parseFloat(document.getElementById('diet-log-serving').value) || 100;
        const servingCount = parseFloat(document.getElementById('diet-log-count').value) || 1;
        const calories = parseFloat(document.getElementById('diet-log-calories').value) || 0;
        const protein = parseFloat(document.getElementById('diet-log-protein').value) || 0;
        const fat = parseFloat(document.getElementById('diet-log-fat').value) || 0;
        const carbs = parseFloat(document.getElementById('diet-log-carbs').value) || 0;
        const notes = document.getElementById('diet-log-notes').value.trim();

        if (!foodName) {
            this.toast('请输入食物名称', 'warning');
            return;
        }

        if (!date || !time) {
            this.toast('请选择日期和时间', 'warning');
            return;
        }

        this.showLoading(true);

        try {
            const res = await fetch(`${this.apiBase}/diet/log`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: this.user.student_id,
                    log_date: date,
                    log_time: `${date} ${time}:00`,
                    meal_type: mealType,
                    food_name: foodName,
                    serving_size: servingSize,
                    serving_count: servingCount,
                    calories: calories,
                    protein: protein,
                    fat: fat,
                    carbs: carbs,
                    notes: notes
                })
            });

            const data = await res.json();

            if (data.success) {
                this.toast('饮食记录添加成功', 'success');
                // 清空表单
                document.getElementById('diet-log-food').value = '';
                document.getElementById('diet-log-calories').value = '0';
                document.getElementById('diet-log-protein').value = '0';
                document.getElementById('diet-log-fat').value = '0';
                document.getElementById('diet-log-carbs').value = '0';
                document.getElementById('diet-log-notes').value = '';
                // 重新加载记录
                this.loadDietLogs();
                this.loadCaloriesChart(7);
            } else {
                this.toast(data.message || '添加失败', 'error');
            }
        } catch (e) {
            this.toast('网络错误，请稍后重试', 'error');
        }

        this.showLoading(false);
    },

    // 加载饮食记录列表
    async loadDietLogs() {
        if (!this.user) return;

        const container = document.getElementById('diet-logs-list');
        if (!container) return;

        container.innerHTML = '<div style="text-align:center;padding:20px;"><i class="fas fa-spinner fa-spin" style="color:var(--primary);"></i></div>';

        try {
            const today = new Date().toISOString().split('T')[0];
            const res = await fetch(`${this.apiBase}/diet/logs?student_id=${this.user.student_id}&date=${today}`);
            const data = await res.json();

            if (data.success && data.logs && data.logs.length > 0) {
                const mealTypes = {
                    'breakfast': {name: '早餐', icon: 'fa-sun', color: '#f59e0b'},
                    'lunch': {name: '午餐', icon: 'fa-cloud-sun', color: '#3b82f6'},
                    'dinner': {name: '晚餐', icon: 'fa-moon', color: '#8b5cf6'},
                    'snack': {name: '加餐', icon: 'fa-cookie-bite', color: '#10b981'}
                };

                container.innerHTML = data.logs.map(log => {
                    const meal = mealTypes[log.meal_type] || mealTypes['snack'];
                    const time = log.log_time ? new Date(log.log_time).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'}) : '';
                    return `
                        <div style="display:flex;align-items:center;gap:12px;padding:10px;border-radius:8px;background:rgba(255,255,255,0.03);margin-bottom:8px;border:1px solid rgba(255,255,255,0.05);">
                            <div style="width:36px;height:36px;border-radius:50%;background:${meal.color}20;display:flex;align-items:center;justify-content:center;">
                                <i class="fas ${meal.icon}" style="color:${meal.color};font-size:14px;"></i>
                            </div>
                            <div style="flex:1;">
                                <div style="font-size:14px;font-weight:500;">${log.food_name}</div>
                                <div style="font-size:12px;color:var(--text-muted);">${meal.name} · ${time} · ${log.serving_size}g × ${log.serving_count}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:14px;font-weight:600;color:var(--accent-light);">${log.calories} kcal</div>
                                <div style="font-size:11px;color:var(--text-muted);">P:${log.protein}g F:${log.fat}g C:${log.carbs}g</div>
                            </div>
                            <button onclick="app.deleteDietLog(${log.id})" style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:4px;">
                                <i class="fas fa-trash-alt" style="font-size:12px;"></i>
                            </button>
                        </div>
                    `;
                }).join('');

                // 计算今日总热量
                const totalCalories = data.logs.reduce((sum, log) => sum + (log.calories || 0), 0);
                container.innerHTML = `
                    <div style="padding:10px;background:rgba(16,185,129,0.1);border-radius:8px;margin-bottom:12px;text-align:center;">
                        <span style="font-size:14px;color:var(--text-light);">今日已摄入</span>
                        <span style="font-size:18px;font-weight:700;color:#10b981;margin-left:8px;">${totalCalories}</span>
                        <span style="font-size:14px;color:var(--text-light);">kcal</span>
                    </div>
                ` + container.innerHTML;
            } else {
                container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px;">今日暂无饮食记录</div>';
            }
        } catch (e) {
            container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px;">加载失败</div>';
        }
    },

    // 删除饮食记录
    async deleteDietLog(logId) {
        if (!confirm('确定要删除这条记录吗？')) return;

        this.showLoading(true);

        try {
            const res = await fetch(`${this.apiBase}/diet/log/${logId}?student_id=${this.user.student_id}`, {
                method: 'DELETE'
            });

            const data = await res.json();

            if (data.success) {
                this.toast('记录已删除', 'success');
                this.loadDietLogs();
                this.loadCaloriesChart(7);
            } else {
                this.toast(data.message || '删除失败', 'error');
            }
        } catch (e) {
            this.toast('网络错误，请稍后重试', 'error');
        }

        this.showLoading(false);
    },

    // 加载热量图表
    async loadCaloriesChart(days = 7) {
        if (!this.user) return;

        // 更新按钮状态
        document.querySelectorAll('[id^="chart-days-"]').forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-secondary');
        });
        const activeBtn = document.getElementById(`chart-days-${days}`);
        if (activeBtn) {
            activeBtn.classList.remove('btn-secondary');
            activeBtn.classList.add('btn-primary');
        }

        try {
            const res = await fetch(`${this.apiBase}/diet/calories-chart?student_id=${this.user.student_id}&days=${days}`);
            const data = await res.json();

            if (data.success) {
                this.renderCaloriesChart(data.chart_data, data.stats);
            }
        } catch (e) {
            console.error('加载热量图表失败:', e);
        }
    },

    // 渲染热量图表
    renderCaloriesChart(chartData, stats) {
        const canvas = document.getElementById('calories-canvas');
        const container = document.getElementById('calories-chart');
        const statsDiv = document.getElementById('calories-stats');

        if (!canvas || !container) return;

        const ctx = canvas.getContext('2d');
        const width = container.clientWidth;
        const height = 200;
        const padding = {top: 20, right: 20, bottom: 30, left: 40};

        canvas.width = width;
        canvas.height = height;

        // 清空画布
        ctx.clearRect(0, 0, width, height);

        // 计算数据范围
        const allValues = [...chartData.actual, ...chartData.target];
        const maxValue = Math.max(...allValues, 2500);
        const minValue = 0;

        // 计算绘制区域
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        // 绘制网格线
        ctx.strokeStyle = 'rgba(255,255,255,0.1)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(width - padding.right, y);
            ctx.stroke();

            // 标注数值
            const value = Math.round(maxValue - (maxValue / 4) * i);
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(value, padding.left - 5, y + 3);
        }

        // 绘制目标线（虚线）
        ctx.strokeStyle = 'rgba(245,158,11,0.5)';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        const targetY = padding.top + chartHeight * (1 - stats.target_calories / maxValue);
        ctx.beginPath();
        ctx.moveTo(padding.left, targetY);
        ctx.lineTo(width - padding.right, targetY);
        ctx.stroke();
        ctx.setLineDash([]);

        // 绘制柱状图
        const barWidth = Math.max(8, (chartWidth / chartData.labels.length) * 0.6);
        const barGap = (chartWidth / chartData.labels.length) - barWidth;

        chartData.actual.forEach((value, index) => {
            const x = padding.left + (chartWidth / chartData.labels.length) * index + barGap / 2;
            const barHeight = (value / maxValue) * chartHeight;
            const y = padding.top + chartHeight - barHeight;

            // 柱状图颜色（根据是否超过目标）
            const color = value > stats.target_calories ? '#ef4444' : '#10b981';
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.8;
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth, barHeight, [3, 3, 0, 0]);
            ctx.fill();
            ctx.globalAlpha = 1;
        });

        // 绘制X轴标签
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        chartData.labels.forEach((label, index) => {
            const x = padding.left + (chartWidth / chartData.labels.length) * (index + 0.5);
            ctx.fillText(label, x, height - 10);
        });

        // 绘制图例
        ctx.fillStyle = '#10b981';
        ctx.fillRect(padding.left, 5, 10, 10);
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('实际摄入', padding.left + 15, 14);

        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(padding.left + 80, 5, 10, 10);
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.fillText('目标热量', padding.left + 95, 14);

        // 更新统计信息
        if (statsDiv) {
            statsDiv.innerHTML = `
                <div style="padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;">
                    <div style="font-size:16px;font-weight:700;color:var(--accent-light);">${stats.avg_calories}</div>
                    <div style="color:var(--text-muted);">日均摄入</div>
                </div>
                <div style="padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;">
                    <div style="font-size:16px;font-weight:700;color:var(--success);">${stats.max_calories}</div>
                    <div style="color:var(--text-muted);">最高摄入</div>
                </div>
                <div style="padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;">
                    <div style="font-size:16px;font-weight:700;color:#f59e0b;">${stats.target_calories}</div>
                    <div style="color:var(--text-muted);">目标热量</div>
                </div>
                <div style="padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;">
                    <div style="font-size:16px;font-weight:700;color:var(--primary-lighter);">${stats.days_recorded}</div>
                    <div style="color:var(--text-muted);">记录天数</div>
                </div>
            `;
        }
    },

    // 加载夜宵习惯分析
    async loadNightAnalysis() {
        if (!this.user) return;

        const container = document.getElementById('night-analysis');
        if (!container) return;

        try {
            const res = await fetch(`${this.apiBase}/diet/night-analysis?student_id=${this.user.student_id}&days=30`);
            const data = await res.json();

            if (data.success) {
                const analysis = data.analysis;
                
                // 健康等级颜色
                const levelColors = {
                    '正常': '#10b981',
                    '一般': '#f59e0b',
                    '偏高': '#f97316',
                    '严重': '#ef4444'
                };
                const levelColor = levelColors[analysis.health_level] || '#10b981';

                container.innerHTML = `
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;">
                        <div style="text-align:center;padding:12px;background:rgba(255,255,255,0.03);border-radius:8px;">
                            <div style="font-size:20px;font-weight:700;color:var(--accent-light);">${analysis.total_count}</div>
                            <div style="font-size:12px;color:var(--text-muted);">夜宵次数</div>
                        </div>
                        <div style="text-align:center;padding:12px;background:rgba(255,255,255,0.03);border-radius:8px;">
                            <div style="font-size:20px;font-weight:700;color:#f59e0b;">${analysis.total_calories}</div>
                            <div style="font-size:12px;color:var(--text-muted);">总热量(kcal)</div>
                        </div>
                        <div style="text-align:center;padding:12px;background:rgba(255,255,255,0.03);border-radius:8px;">
                            <div style="font-size:20px;font-weight:700;color:var(--primary-lighter);">${analysis.weekly_frequency}</div>
                            <div style="font-size:12px;color:var(--text-muted);">每周平均</div>
                        </div>
                    </div>

                    <div style="padding:12px;background:${levelColor}15;border:1px solid ${levelColor}30;border-radius:8px;margin-bottom:16px;">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                            <i class="fas fa-info-circle" style="color:${levelColor};"></i>
                            <span style="font-weight:600;color:${levelColor};">健康评估: ${analysis.health_level}</span>
                        </div>
                        <div style="font-size:13px;color:var(--text-light);">${analysis.health_suggestion}</div>
                    </div>

                    ${analysis.time_periods && Object.values(analysis.time_periods).some(v => v > 0) ? `
                        <div style="margin-bottom:16px;">
                            <div style="font-size:13px;font-weight:500;margin-bottom:8px;color:var(--text-light);">时间段分布（21:00-03:00）</div>
                            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
                                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;">
                                    <div style="font-size:14px;font-weight:600;">${analysis.time_periods['21-23'] || 0}</div>
                                    <div style="font-size:10px;color:var(--text-muted);">21-23时</div>
                                </div>
                                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;">
                                    <div style="font-size:14px;font-weight:600;">${analysis.time_periods['23-01'] || 0}</div>
                                    <div style="font-size:10px;color:var(--text-muted);">23-01时</div>
                                </div>
                                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;">
                                    <div style="font-size:14px;font-weight:600;">${analysis.time_periods['01-03'] || 0}</div>
                                    <div style="font-size:10px;color:var(--text-muted);">01-03时</div>
                                </div>
                            </div>
                        </div>
                    ` : ''}

                    ${analysis.top_foods && analysis.top_foods.length > 0 ? `
                        <div>
                            <div style="font-size:13px;font-weight:500;margin-bottom:8px;color:var(--text-light);">常吃夜宵</div>
                            ${analysis.top_foods.map((food, index) => `
                                <div style="display:flex;align-items:center;gap:8px;padding:6px 0;${index < analysis.top_foods.length - 1 ? 'border-bottom:1px solid rgba(255,255,255,0.05);' : ''}">
                                    <span style="font-size:12px;color:var(--text-muted);width:20px;">#${index + 1}</span>
                                    <span style="flex:1;font-size:13px;">${food.name}</span>
                                    <span style="font-size:12px;color:var(--text-muted);">${food.count}次 · ${food.calories}kcal</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : '<div style="text-align:center;color:var(--text-muted);padding:12px;font-size:13px;">暂无夜宵记录</div>'}
                `;
            } else {
                container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px;">暂无夜宵数据</div>';
            }
        } catch (e) {
            container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;font-size:13px;">加载失败</div>';
        }
    }
};

// 启动
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
