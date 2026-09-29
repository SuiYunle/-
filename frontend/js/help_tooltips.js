/**
 * 脉衡界 - 帮助提示系统 (Help Tooltips)
 * ------------------------------------------------------------
 * 功能说明：
 *   1. 在页面/区块右上角添加一个悬浮的问号(?)图标
 *   2. 桌面端鼠标悬停、移动端点击时，展示该页面的使用说明卡片
 *   3. 暗色玻璃拟态风格，匹配脉衡界主题（深色背景 + 青色点缀 + 背景模糊）
 *   4. 自动定位，避免卡片溢出屏幕
 *
 * 使用方式：
 *   方式一（自动初始化）：在需要帮助提示的容器上添加 data-help-page="chat" 属性，
 *                         页面加载后调用 HelpTooltips.autoInit() 即可。
 *   方式二（手动挂载）：HelpTooltips.attachTo('chat', document.querySelector('#chat-page'));
 *   扩展新页面：HelpTooltips.addPage('newpage', '帮助文本', 'fa-icon-class');
 *
 * 依赖：FontAwesome（用于图标，需在页面中提前引入）
 * ------------------------------------------------------------
 */
(function (global) {
  'use strict';

  /* ============================================================
   * 一、帮助内容配置
   * ------------------------------------------------------------
   * HELP_CONTENT 存储每个页面的帮助文本与对应图标。
   * 结构：{ 页面key: { text: '帮助文本', icon: 'FontAwesome图标类名' } }
   * 扩展时只需在此对象中新增条目，或调用 addPage() 方法。
   * ============================================================ */
  var HELP_CONTENT = {
    // AI小艺对话页
    chat: {
      icon: 'fa-solid fa-comments',
      text: 'AI小艺对话页 - 与数字人小艺对话，支持文字、图片输入。可快速选择心理压力、中医体质、健康问诊、食疗推荐等话题。上传舌象获取中医分析，上传餐食获取饮食建议。'
    },
    // 心理疏导页
    mental: {
      icon: 'fa-solid fa-brain',
      text: '心理疏导页 - 专业心理测评问卷（评估焦虑、抑郁、压力、睡眠、社交五维心理健康）+ AI小艺倾听陪伴。系统记录心理状态趋势，支持心理预警（可在隐私设置开启）。'
    },
    // 中医体质辨识页
    tcm: {
      icon: 'fa-solid fa-yin-yang',
      text: '中医体质辨识页 - 从35题题库随机抽取10题，智能辨识九种体质类型，给出饮食、运动、起居、情志调理方案。另含舌象分析、餐食分析、食疗推荐等辅助功能。'
    },
    // AI问诊页
    diagnosis: {
      icon: 'fa-solid fa-stethoscope',
      text: 'AI问诊页 - BMI分析（男女差异化建议）、症状自查，并汇总你在体质、心理板块的最近测评结果作为问诊参考。'
    },
    // 健康资讯页
    community: {
      icon: 'fa-solid fa-newspaper',
      text: '健康资讯页 - 浏览健康知识文章和资讯，获取科学健康指导。'
    },
    // 积分中心页
    rewards: {
      icon: 'fa-solid fa-gift',
      text: '积分中心页 - 查看你的积分余额和获取记录。通过每日登录、对话互动、完成测评等多种方式获取积分。'
    },
    // 隐私设置页
    privacy: {
      icon: 'fa-solid fa-shield-halved',
      text: '隐私设置页 - 管理你的数据隐私偏好。可开启/关闭心理预警功能，管理数据存储和分享设置，支持一键删除所有账户数据。'
    }
  };

  /* ============================================================
   * 二、样式注入
   * ------------------------------------------------------------
   * 动态注入 CSS，无需额外引入样式文件。
   * 采用暗色玻璃拟态风格，青色(teal)作为点缀色。
   * ============================================================ */
  var STYLE_ID = '__maiheng_help_tooltip_style__';

  // 主题色变量，便于统一调整
  var THEME = {
    teal: '#2dd4bf',            // 青色主点缀色
    tealDark: '#14b8a6',        // 深青色（悬停态）
    bgDark: 'rgba(17, 25, 40, 0.82)', // 深色半透明背景
    borderColor: 'rgba(45, 212, 191, 0.35)', // 青色边框
    textColor: '#e2e8f0',       // 浅色文字
    subTextColor: '#94a3b8'     // 次级文字
  };

  /**
   * 注入样式（仅注入一次）
   */
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;

    var css = '' +
      /* 问号图标按钮 */
      '.mh-help-icon {' +
      '  position: absolute;' +
      '  top: 16px;' +
      '  right: 16px;' +
      '  width: 24px;' +
      '  height: 24px;' +
      '  border-radius: 50%;' +
      '  background: ' + THEME.teal + ';' +
      '  color: #042f2e;' +
      '  border: none;' +
      '  cursor: pointer;' +
      '  display: flex;' +
      '  align-items: center;' +
      '  justify-content: center;' +
      '  font-size: 13px;' +
      '  font-weight: 700;' +
      '  line-height: 1;' +
      '  z-index: 9998;' +
      '  box-shadow: 0 2px 8px rgba(45, 212, 191, 0.35);' +
      '  transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;' +
      '  user-select: none;' +
      '  -webkit-tap-highlight-color: transparent;' +
      '}' +
      '.mh-help-icon:hover {' +
      '  background: ' + THEME.tealDark + ';' +
      '  transform: scale(1.12);' +
      '  box-shadow: 0 4px 14px rgba(45, 212, 191, 0.5);' +
      '}' +
      '.mh-help-icon:active {' +
      '  transform: scale(0.95);' +
      '}' +

      /* 帮助卡片（玻璃拟态） */
      '.mh-help-card {' +
      '  position: fixed;' +
      '  z-index: 9999;' +
      '  max-width: 320px;' +
      '  min-width: 220px;' +
      '  padding: 14px 16px;' +
      '  border-radius: 12px;' +
      '  background: ' + THEME.bgDark + ';' +
      '  -webkit-backdrop-filter: blur(14px);' +
      '  backdrop-filter: blur(14px);' +
      '  border: 1px solid ' + THEME.borderColor + ';' +
      '  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(45, 212, 191, 0.08) inset;' +
      '  color: ' + THEME.textColor + ';' +
      '  font-size: 13px;' +
      '  line-height: 1.6;' +
      '  opacity: 0;' +
      '  visibility: hidden;' +
      '  transform: translateY(6px) scale(0.96);' +
      '  transition: opacity 0.22s ease, transform 0.22s ease, visibility 0.22s ease;' +
      '  pointer-events: none;' +
      '}' +
      '.mh-help-card.is-visible {' +
      '  opacity: 1;' +
      '  visibility: visible;' +
      '  transform: translateY(0) scale(1);' +
      '  pointer-events: auto;' +
      '}' +

      /* 卡片头部（图标 + 标题） */
      '.mh-help-card__header {' +
      '  display: flex;' +
      '  align-items: center;' +
      '  gap: 8px;' +
      '  margin-bottom: 8px;' +
      '  padding-bottom: 8px;' +
      '  border-bottom: 1px solid rgba(45, 212, 191, 0.18);' +
      '}' +
      '.mh-help-card__icon {' +
      '  color: ' + THEME.teal + ';' +
      '  font-size: 15px;' +
      '  flex-shrink: 0;' +
      '}' +
      '.mh-help-card__title {' +
      '  font-size: 13px;' +
      '  font-weight: 600;' +
      '  color: ' + THEME.teal + ';' +
      '  letter-spacing: 0.3px;' +
      '}' +

      /* 卡片正文 */
      '.mh-help-card__body {' +
      '  color: ' + THEME.textColor + ';' +
      '  word-break: break-word;' +
      '}' +

      /* 卡片小箭头（指向图标） */
      '.mh-help-card__arrow {' +
      '  position: absolute;' +
      '  width: 10px;' +
      '  height: 10px;' +
      '  background: ' + THEME.bgDark + ';' +
      '  border-right: 1px solid ' + THEME.borderColor + ';' +
      '  border-bottom: 1px solid ' + THEME.borderColor + ';' +
      '  transform: rotate(45deg);' +
      '  z-index: -1;' +
      '}' +

      /* 挂载容器需为相对定位，使图标绝对定位生效 */
      '.mh-help-anchor {' +
      '  position: relative;' +
      '}';

    var styleEl = document.createElement('style');
    styleEl.id = STYLE_ID;
    styleEl.textContent = css;
    document.head.appendChild(styleEl);
  }

  /* ============================================================
   * 三、核心工具函数
   * ============================================================ */

  /**
   * 判断当前是否为移动端（通过触摸支持 + 屏幕宽度综合判断）
   * @returns {boolean}
   */
  function isMobile() {
    var hasTouch = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;
    return hasTouch && window.innerWidth < 1024;
  }

  /**
   * 创建问号图标按钮元素
   * @returns {HTMLButtonElement}
   */
  function createIcon() {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'mh-help-icon';
    btn.setAttribute('aria-label', '查看页面使用帮助');
    btn.textContent = '?';
    return btn;
  }

  /**
   * 创建帮助卡片元素（含图标、标题、正文）
   * @param {string} pageKey - 页面标识
   * @param {Object} content - { icon, text }
   * @returns {HTMLDivElement}
   */
  function createCard(pageKey, content) {
    var card = document.createElement('div');
    card.className = 'mh-help-card';
    card.setAttribute('role', 'tooltip');
    card.setAttribute('data-page', pageKey);

    // 标题：取帮助文本中 " - " 之前的部分作为标题
    var titleText = '使用说明';
    var bodyText = content.text || '';
    var dashIdx = bodyText.indexOf(' - ');
    if (dashIdx > -1) {
      titleText = bodyText.substring(0, dashIdx);
      bodyText = bodyText.substring(dashIdx + 3);
    }

    // 头部：图标 + 标题
    var header = document.createElement('div');
    header.className = 'mh-help-card__header';

    var iconEl = document.createElement('i');
    iconEl.className = 'mh-help-card__icon ' + (content.icon || 'fa-solid fa-circle-info');

    var titleEl = document.createElement('span');
    titleEl.className = 'mh-help-card__title';
    titleEl.textContent = titleText;

    header.appendChild(iconEl);
    header.appendChild(titleEl);

    // 正文
    var body = document.createElement('div');
    body.className = 'mh-help-card__body';
    body.textContent = bodyText;

    card.appendChild(header);
    card.appendChild(body);

    return card;
  }

  /**
   * 自动定位卡片，避免溢出屏幕
   * @param {HTMLElement} card - 卡片元素
   * @param {HTMLElement} icon - 图标元素
   */
  function positionCard(card, icon) {
    var iconRect = icon.getBoundingClientRect();
    var cardRect = card.getBoundingClientRect();
    var viewportW = window.innerWidth;
    var viewportH = window.innerHeight;
    var scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    var scrollY = window.pageYOffset || document.documentElement.scrollTop;

    // 默认放置在图标右下方
    var GAP = 10; // 图标与卡片的间距
    var left = iconRect.right - cardRect.width; // 右对齐到图标
    var top = iconRect.bottom + GAP;

    var arrow = card.querySelector('.mh-help-card__arrow');
    var arrowSize = 10;

    // —— 水平方向修正 ——
    if (left < scrollX + 8) {
      // 左侧溢出：左对齐到图标
      left = iconRect.left;
      if (arrow) {
        arrow.style.left = (iconRect.width / 2 - arrowSize / 2) + 'px';
        arrow.style.right = 'auto';
      }
    } else if (left + cardRect.width > scrollX + viewportW - 8) {
      // 右侧溢出：贴右边
      left = scrollX + viewportW - cardRect.width - 8;
      if (arrow) {
        arrow.style.right = (viewportW - iconRect.right + iconRect.width / 2 - arrowSize / 2) + 'px';
        arrow.style.left = 'auto';
      }
    } else {
      // 默认右对齐，箭头靠右
      if (arrow) {
        arrow.style.right = (iconRect.width / 2 - arrowSize / 2) + 'px';
        arrow.style.left = 'auto';
      }
    }

    // —— 垂直方向修正 ——
    if (top + cardRect.height > scrollY + viewportH - 8) {
      // 下方溢出：改放到图标上方
      top = iconRect.top - cardRect.height - GAP;
      // 翻转箭头方向（指向下方）
      if (arrow) {
        arrow.style.top = 'auto';
        arrow.style.bottom = '-5px';
        arrow.style.transform = 'rotate(225deg)';
      }
    } else {
      // 默认下方，箭头指向上方
      if (arrow) {
        arrow.style.bottom = 'auto';
        arrow.style.top = '-5px';
        arrow.style.transform = 'rotate(45deg)';
      }
    }

    card.style.left = left + 'px';
    card.style.top = top + 'px';
  }

  /* ============================================================
   * 四、帮助提示控制器
   * ------------------------------------------------------------
   * 封装单个页面区块的帮助图标 + 卡片交互逻辑。
   * ============================================================ */

  /**
   * 帮助提示控制器构造函数
   * @param {string} pageKey - 页面标识（对应 HELP_CONTENT 的 key）
   * @param {HTMLElement} container - 挂载容器（图标将出现在其右上角）
   */
  function HelpController(pageKey, container) {
    this.pageKey = pageKey;
    this.container = container;
    this.icon = null;
    this.card = null;
    this._showTimer = null;
    this._hideTimer = null;
    this._visible = false;

    this._init();
  }

  HelpController.prototype = {
    constructor: HelpController,

    /**
     * 初始化：创建图标与卡片，绑定事件
     */
    _init: function () {
      var content = HELP_CONTENT[this.pageKey];
      if (!content) {
        console.warn('[HelpTooltips] 未找到页面 "' + this.pageKey + '" 的帮助内容，请先通过 addPage() 添加。');
        return;
      }

      // 容器需为相对定位，使图标定位生效
      if (getComputedStyle(this.container).position === 'static') {
        this.container.classList.add('mh-help-anchor');
      }

      this.icon = createIcon();
      this.card = createCard(this.pageKey, content);

      // 卡片内追加小箭头
      var arrow = document.createElement('span');
      arrow.className = 'mh-help-card__arrow';
      this.card.appendChild(arrow);

      this.container.appendChild(this.icon);
      document.body.appendChild(this.card);

      this._bindEvents();
    },

    /**
     * 绑定交互事件（区分桌面端 / 移动端）
     */
    _bindEvents: function () {
      var self = this;
      var mobile = isMobile();

      if (mobile) {
        // —— 移动端：点击图标切换显示，点击其他区域关闭 ——
        self.icon.addEventListener('click', function (e) {
          e.stopPropagation();
          if (self._visible) {
            self.hide();
          } else {
            self.show();
          }
        });

        // 点击卡片内部时阻止冒泡，避免立即关闭
        self.card.addEventListener('click', function (e) {
          e.stopPropagation();
        });

        // 点击页面其他区域关闭
        self._outsideHandler = function () {
          self.hide();
        };
        document.addEventListener('click', self._outsideHandler);
      } else {
        // —— 桌面端：鼠标悬停显示，移出隐藏 ——
        // 使用 enter/leave 事件，并对图标与卡片整体监听，避免移动到卡片时闪烁
        var enterTarget = self.icon;

        enterTarget.addEventListener('mouseenter', function () {
          clearTimeout(self._hideTimer);
          self._showTimer = setTimeout(function () {
            self.show();
          }, 120);
        });

        enterTarget.addEventListener('mouseleave', function () {
          clearTimeout(self._showTimer);
          self._hideTimer = setTimeout(function () {
            self.hide();
          }, 150);
        });

        // 鼠标进入卡片时取消隐藏
        self.card.addEventListener('mouseenter', function () {
          clearTimeout(self._hideTimer);
        });

        self.card.addEventListener('mouseleave', function () {
          self._hideTimer = setTimeout(function () {
            self.hide();
          }, 150);
        });
      }

      // 滚动或窗口尺寸变化时，重新定位 / 关闭卡片
      self._scrollHandler = function () {
        if (self._visible) {
          positionCard(self.card, self.icon);
        }
      };
      window.addEventListener('scroll', self._scrollHandler, true);
      window.addEventListener('resize', self._scrollHandler);
    },

    /**
     * 显示帮助卡片（带淡入动画）
     */
    show: function () {
      if (!this.card || this._visible) return;
      // 先显示再定位，确保能获取到卡片尺寸
      this.card.classList.add('is-visible');
      this._visible = true;
      positionCard(this.card, this.icon);
    },

    /**
     * 隐藏帮助卡片
     */
    hide: function () {
      if (!this.card || !this._visible) return;
      this.card.classList.remove('is-visible');
      this._visible = false;
    },

    /**
     * 切换显示状态
     */
    toggle: function () {
      if (this._visible) this.hide();
      else this.show();
    },

    /**
     * 销毁：移除 DOM 与事件监听
     */
    destroy: function () {
      clearTimeout(this._showTimer);
      clearTimeout(this._hideTimer);
      if (this._outsideHandler) {
        document.removeEventListener('click', this._outsideHandler);
      }
      if (this._scrollHandler) {
        window.removeEventListener('scroll', this._scrollHandler, true);
        window.removeEventListener('resize', this._scrollHandler);
      }
      if (this.icon && this.icon.parentNode) {
        this.icon.parentNode.removeChild(this.icon);
      }
      if (this.card && this.card.parentNode) {
        this.card.parentNode.removeChild(this.card);
      }
      this.icon = null;
      this.card = null;
      this._visible = false;
    }
  };

  /* ============================================================
   * 五、对外 API
   * ------------------------------------------------------------
   * 通过 window.HelpTooltips 暴露，供全局调用。
   * ============================================================ */

  // 已创建的控制器集合（按 pageKey 存储，支持多实例）
  var controllers = [];

  var HelpTooltips = {
    /**
     * 帮助内容对象（可外部读取 / 修改，便于扩展）
     */
    HELP_CONTENT: HELP_CONTENT,

    /**
     * 添加新页面的帮助内容
     * @param {string} key - 页面标识
     * @param {string} text - 帮助文本
     * @param {string} [icon='fa-solid fa-circle-info'] - FontAwesome 图标类名
     * @returns {Object} HelpTooltips（支持链式调用）
     */
    addPage: function (key, text, icon) {
      HELP_CONTENT[key] = {
        icon: icon || 'fa-solid fa-circle-info',
        text: text
      };
      return this;
    },

    /**
     * 为指定容器挂载帮助图标
     * @param {string} pageKey - 页面标识
     * @param {HTMLElement} container - 挂载容器
     * @returns {HelpController|null}
     */
    attachTo: function (pageKey, container) {
      if (!container) {
        console.warn('[HelpTooltips] attachTo: container 不能为空。');
        return null;
      }
      injectStyles();
      var ctrl = new HelpController(pageKey, container);
      controllers.push(ctrl);
      return ctrl;
    },

    /**
     * 自动初始化：扫描带有 data-help-page 属性的元素并挂载帮助图标
     * 使用示例：<div data-help-page="chat">...</div>
     * @returns {number} 初始化的控制器数量
     */
    autoInit: function () {
      injectStyles();
      var nodes = document.querySelectorAll('[data-help-page]');
      var count = 0;
      for (var i = 0; i < nodes.length; i++) {
        var pageKey = nodes[i].getAttribute('data-help-page');
        if (pageKey && HELP_CONTENT[pageKey]) {
          this.attachTo(pageKey, nodes[i]);
          count++;
        } else if (pageKey) {
          console.warn('[HelpTooltips] 页面 "' + pageKey + '" 暂无帮助内容，已跳过。');
        }
      }
      return count;
    },

    /**
     * 销毁所有已创建的控制器（清理 DOM 与事件）
     */
    destroyAll: function () {
      for (var i = 0; i < controllers.length; i++) {
        if (controllers[i]) controllers[i].destroy();
      }
      controllers = [];
    },

    /**
     * 获取所有已创建的控制器
     * @returns {Array}
     */
    getControllers: function () {
      return controllers.slice();
    }
  };

  // 暴露到全局
  global.HelpTooltips = HelpTooltips;

  /* ============================================================
   * 六、自动启动（DOM 就绪后自动扫描 data-help-page）
   * ------------------------------------------------------------
   * 若页面已有 data-help-page 标记，则无需手动调用 autoInit()。
   * 如需更精细控制，可设置 window.__MH_HELP_DISABLE_AUTO__ = true 跳过。
   * ============================================================ */
  function onReady(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    if (global.__MH_HELP_DISABLE_AUTO__) return;
    // 仅当存在标记元素时才自动初始化，避免无意义扫描
    if (document.querySelector('[data-help-page]')) {
      HelpTooltips.autoInit();
    }
  });

})(typeof window !== 'undefined' ? window : this);
