#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令式网页自动化执行器

特性
- 从命令文件按行读取指令执行 Selenium 操作，支持注释与空行。
- 支持引号字符串shlex 解析，文本可包含空格。
- 支持高频操作：点击、输入、悬停、等待、滚动、窗口/Frame、下拉框、键盘、截图、上传、导航、断言、执行 JS、Cookie。
- 支持几乎所有常用操作

兼容别名
- L_click -> click
- R_click -> rclick
- D_click -> dclick
- put    -> hover
- write  -> write
- jump   -> goto
- delay  -> sleep
- pause  -> pause
- keep_open -> keep_open

示例
  python cmd_web_automation.py \
    --driver edge --driver-path msedgedriver.exe \
    --start-url https://example.com \
    --commands command.txt \
    --maximize
"""

import argparse
import sys
import re
import time
import shlex
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from selenium import webdriver
from selenium.common import exceptions as selerr
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# 可选浏览器驱动
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CommandSpec:
    func: str                 # CommandExecutor 的方法名
    min_args: int = 0         # 最少参数数（不含命令名）
    max_args: Optional[int] = None  # 最多参数数，None 表示不限
    join_from: Optional[int] = None # 将 args[join_from:] 用空格合并为一个参数

# 命令表
COMMAND_SPECS = {
    # 元素点击与输入
    'click':                CommandSpec('cmd_click',                2, 2),
    'rclick':               CommandSpec('cmd_rclick',               2, 2),
    'dclick':               CommandSpec('cmd_dclick',               2, 2),
    'hover':                CommandSpec('cmd_hover',                2, 2),
    'click_js':             CommandSpec('cmd_click_js',             2, 2),
    'clear':                CommandSpec('cmd_clear',                2, 2),
    # write 文本可能包含空格，因此不限最大参数数，给 cmd_write 内部 join
    'write':                CommandSpec('cmd_write',                3, None),
    'send_keys':            CommandSpec('cmd_send_keys',            3, None),
    'press':                CommandSpec('cmd_press',                1, None),
    'write_ce':             CommandSpec('cmd_write_ce', 3, None, join_from=2),
    'write_js':             CommandSpec('cmd_write_js', 3, None, join_from=2),

    # 拖拽
    'drag_drop':            CommandSpec('cmd_drag_drop',            4, 4),
    'drag_offset':          CommandSpec('cmd_drag_offset',          4, 4),

    # 导航与窗口
    'goto':                 CommandSpec('cmd_goto',                 1, 1),
    'back':                 CommandSpec('cmd_back',                 0, 0),
    'forward':              CommandSpec('cmd_forward',              0, 0),
    'refresh':              CommandSpec('cmd_refresh',              0, 0),
    'maximize':             CommandSpec('cmd_maximize',             0, 0),
    'minimize':             CommandSpec('cmd_minimize',             0, 0),
    'set_window':           CommandSpec('cmd_set_window',           2, 2),

    # Frame
    'frame':                CommandSpec('cmd_frame',                2, 2),
    'frame_index':          CommandSpec('cmd_frame_index',          1, 1),
    'frame_parent':         CommandSpec('cmd_frame_parent',         0, 0),
    'frame_default':        CommandSpec('cmd_frame_default',        0, 0),

    # 窗口（Tab）
    'window_latest':        CommandSpec('cmd_window_latest',        0, 0),
    'window_index':         CommandSpec('cmd_window_index',         1, 1),
    'window_close':         CommandSpec('cmd_window_close',         0, 0),

    # 等待（注意：wait_text 的 text 建议在命令文件中用引号，shlex 会当作一个参数传入）
    'wait_present':         CommandSpec('cmd_wait_present',         2, 3),
    'wait_visible':         CommandSpec('cmd_wait_visible',         2, 3),
    'wait_clickable':       CommandSpec('cmd_wait_clickable',       2, 3),
    'wait_invisible':       CommandSpec('cmd_wait_invisible',       2, 3),
    'wait_text':            CommandSpec('cmd_wait_text',            3, 4),

    # 滚动
    'scroll_into_view':     CommandSpec('cmd_scroll_into_view',     2, 3),
    'scroll_by':            CommandSpec('cmd_scroll_by',            2, 2),
    'scroll_top':           CommandSpec('cmd_scroll_top',           0, 0),
    'scroll_bottom':        CommandSpec('cmd_scroll_bottom',        0, 0),

    # 下拉选择
    'select':               CommandSpec('cmd_select',               4, 4),

    # 上传/截图/JS（exec_js 需要把剩余合并成一个脚本参数）
    'upload':               CommandSpec('cmd_upload',               3, 3),
    'screenshot':           CommandSpec('cmd_screenshot',           1, 1),
    'screenshot_element':   CommandSpec('cmd_screenshot_element',   3, 3),
    'exec_js':              CommandSpec('cmd_exec_js',              1, None, join_from=0),

    # 断言/打印（可能包含空格的内容需要 join）
    'assert_text':          CommandSpec('cmd_assert_text',          3, None, join_from=2),
    'assert_url_contains':  CommandSpec('cmd_assert_url_contains',  1, None, join_from=0),
    'assert_title_contains':CommandSpec('cmd_assert_title_contains',1, None, join_from=0),
    'print_text':           CommandSpec('cmd_print_text',           2, 2),
    'print_attr':           CommandSpec('cmd_print_attr',           3, 3),
    'echo':                 CommandSpec('cmd_echo',                 0, None),

    # Cookie
    'cookie_set':           CommandSpec('cmd_cookie_set',           2, 2),
    'cookies_set':          CommandSpec('cmd_cookies_set',          1, 1),
    'cookie_get':           CommandSpec('cmd_cookie_get',           1, 1),
    'cookie_delete':        CommandSpec('cmd_cookie_delete',        1, 1),
    'cookie_clear':         CommandSpec('cmd_cookie_clear',         0, 0),

    # 其他
    'sleep':                CommandSpec('cmd_sleep',                1, 1),
    'pause':                CommandSpec('cmd_pause',                0, 0),
    'keep_open':            CommandSpec('cmd_keep_open',            0, 0),

    # 实用
    'set_var':              CommandSpec('cmd_set_var',              2, 2),
}

VERSION = "v1.0.0"

SEARCH: Dict[str, str] = {
    'XPATH': By.XPATH,
    'CSS': By.CSS_SELECTOR,
    'ID': By.ID,
    'NAME': By.NAME,
    'CLASS': By.CLASS_NAME,
    'TAG': By.TAG_NAME,
    'LINK': By.LINK_TEXT,
    'PLINK': By.PARTIAL_LINK_TEXT,
}

KEYS: Dict[str, str] = {
    'ENTER': Keys.ENTER,
    'TAB': Keys.TAB,
    'ESC': Keys.ESCAPE,
    'ESCAPE': Keys.ESCAPE,
    'SPACE': Keys.SPACE,
    'BACKSPACE': Keys.BACKSPACE,
    'DELETE': Keys.DELETE,
    'HOME': Keys.HOME,
    'END': Keys.END,
    'PAGE_UP': Keys.PAGE_UP,
    'PAGE_DOWN': Keys.PAGE_DOWN,
    'LEFT': Keys.ARROW_LEFT,
    'RIGHT': Keys.ARROW_RIGHT,
    'UP': Keys.ARROW_UP,
    'DOWN': Keys.ARROW_DOWN,
    'CTRL': Keys.CONTROL,
    'SHIFT': Keys.SHIFT,
    'ALT': Keys.ALT,
    'CMD': Keys.COMMAND,
    'META': Keys.META,
}

# 快捷键组合
KEY_COMBOS: Dict[str, List[str]] = {
    'CTRL_A': [Keys.CONTROL, 'a'],
    'CTRL_C': [Keys.CONTROL, 'c'],
    'CTRL_V': [Keys.CONTROL, 'v'],
    'CTRL_X': [Keys.CONTROL, 'x'],
    'CTRL_S': [Keys.CONTROL, 's'],
    'CTRL_Z': [Keys.CONTROL, 'z'],
    'CTRL_Y': [Keys.CONTROL, 'y'],
}

# 老版本兼容
ALIASES = {
    'L_click': 'click',
    'R_click': 'rclick',
    'D_click': 'dclick',
    'put': 'hover',
    'jump': 'goto',
    'delay': 'sleep',
    'pause': 'pause',
    'keep_open': 'keep_open',
}

# 微信UA模拟
WECHAT_ANDROID_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Version/4.0 Chrome/114.0.5735.196 Mobile Safari/537.36 "
    "MicroMessenger/8.0.44(0x28002c57) Process/appbrand0 WeChat/arm64 NetType/WIFI Language/zh_CN ABI/arm64"
)

def set_ua_via_cdp(driver, ua: str):
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": ua,
        "platform": "Android",
        "userAgentMetadata": {
            "brands": [
                {"brand": "Chromium", "version": "114"},
                {"brand": "Google Chrome", "version": "114"}
            ],
            "fullVersion": "114.0.5735.196",
            "platform": "Android",
            "platformVersion": "13",
            "architecture": "arm64",
            "model": "Pixel 6",
            "mobile": True
        }
    })
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "Accept-Language": "zh-CN,zh;q=0.9",
            "X-Requested-With": "com.tencent.mm",
            "Referer": "https://weixin.qq.com/"
        }
    })

LOCK_FILES = {"SingletonLock", "SingletonCookie", "SingletonSocket", "SingletonStartupLock"}

def normalize_abs_path(p: str) -> str:
    if not p:
        return ""
    return str(Path(p).expanduser().resolve())

def has_lock_files(user_data_dir: str) -> bool:
    if not user_data_dir:
        return False
    p = Path(user_data_dir)
    return any((p / lf).exists() for lf in LOCK_FILES)

def prepare_unique_user_data_dir(base_dir: str) -> str:
    """
    - base_dir 为空：返回空（不使用 user-data-dir）
    - base_dir 存在锁文件：创建同级唯一临时目录并返回
    - base_dir 不存在：创建后返回
    - 否则：返回 base_dir
    """
    if not base_dir:
        return ""
    base = Path(base_dir).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    if has_lock_files(str(base)):
        uniq = base.parent / f"{base.name}_{int(time.time())}"
        uniq.mkdir(parents=True, exist_ok=True)
        print(f"[提示] 检测到锁文件，改用唯一目录：{uniq}")
        return str(uniq)
    return str(base)

def join_rest(parts: List[str], start: int = 0) -> str:
    return ' '.join(parts[start:]) if len(parts) > start else ''


def parse_int(s: str, name: str = 'number') -> int:
    try:
        return int(s)
    except Exception:
        raise ValueError(f'{name} 必须为整数 -> {s}')


def parse_float(s: str, name: str = 'number') -> float:
    try:
        return float(s)
    except Exception:
        raise ValueError(f'{name} 必须为数字 -> {s}')

# 生成浏览器驱动
def build_driver(name: str, driver_path: str, ua: str, user_data: str, profile_data: str,
                 anti_ac: bool = False, headless: bool = False, net_harden: bool = False, netlog_path: str = "",
                 debugger_address: str = ""):
    name = name.lower()
    if name == 'edge':
        options = EdgeOptions()
        if headless:
            options.add_argument('--headless=new')
        if debugger_address:
            # 附着模式,只设置debuggerAddress
            options.add_experimental_option("debuggerAddress", debugger_address)
        else:
            # 非附着可设置
            if ua:
                options.add_argument(f'--user-agent={ua}')
            if anti_ac:
                # 这些在附着模式下会报错，这里仅在非附着模式配置
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                options.add_argument("--disable-blink-features=AutomationControlled")
            if user_data:
                options.add_argument(f"--user-data-dir={user_data}")
            if profile_data:
                options.add_argument(f"--profile-directory={profile_data}")

        # 网络稳态
        if net_harden:
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-insecure-localhost')
            options.add_argument('--disable-quic')
            options.add_argument('--disable-http2')
            options.add_argument('--disable-features=TLS13EarlyData')
            options.set_capability("acceptInsecureCerts", True)
        if netlog_path:
            netlog_path = str(Path(netlog_path).expanduser().resolve())
            Path(netlog_path).parent.mkdir(parents=True, exist_ok=True)
            options.add_argument(f'--log-net-log={netlog_path}')
            options.add_argument('--net-log-capture-mode=IncludeSensitive')

        service = EdgeService(executable_path=driver_path) if driver_path else EdgeService()
        return webdriver.Edge(service=service, options=options)

    if name == 'chrome':
        options = ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        if debugger_address:
            options.add_experimental_option("debuggerAddress", debugger_address)
        else:
            if ua:
                options.add_argument(f'--user-agent={ua}')
            if anti_ac:
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                options.add_argument("--disable-blink-features=AutomationControlled")
            if user_data:
                options.add_argument(f"--user-data-dir={user_data}")
            if profile_data:
                options.add_argument(f"--profile-directory={profile_data}")

        options.add_argument('--disable-gpu')

        if net_harden:
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-insecure-localhost')
            options.add_argument('--disable-quic')
            options.add_argument('--disable-http2')
            options.add_argument('--disable-features=TLS13EarlyData')
            options.set_capability("acceptInsecureCerts", True)
        if netlog_path:
            netlog_path = str(Path(netlog_path).expanduser().resolve())
            Path(netlog_path).parent.mkdir(parents=True, exist_ok=True)
            options.add_argument(f'--log-net-log={netlog_path}')
            options.add_argument('--net-log-capture-mode=IncludeSensitive')

        service = ChromeService(executable_path=driver_path) if driver_path else ChromeService()
        return webdriver.Chrome(service=service, options=options)

    if name == 'firefox':
        options = FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        if ua != '':
            options.add_argument(f'--user-agent={ua}')
            options.add_argument("--disable-blink-features=AutomationControlled")
        if user_data != '':
            options.add_argument(f"--user-data-dir={user_data}")
        if profile_data != '':
            options.add_argument(f"--profile-directory={profile_data}")
        service = FirefoxService(executable_path=driver_path) if driver_path else FirefoxService()
        return webdriver.Firefox(service=service, options=options)

    raise ValueError(f'不支持的浏览器 -> {name}')


class CommandExecutor:
    def __init__(self, driver, ignore_error: bool = False, default_timeout: int = 15, user_agent: str = ""):
        self.driver = driver
        self.default_timeout = default_timeout
        self._keep_open = False
        self._ginore_error = ignore_error
        self.user_agent = user_agent
        self._var_set: Dict[str, Any] = {}
        self._fliter: re.Pattern = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?:\|([A-Za-z0-9_|:%\-\.\+]+))?\}')

    @property
    def keep_open(self) -> bool:
        return self._keep_open

    # 基础工具
    def _get_by(self, key: str) -> str:
        upper = key.upper()
        if upper not in SEARCH:
            raise KeyError(f'查询方式错误 -> {key}')
        return SEARCH[upper]

    def _find(self, by_key: str, selector: str):
        return self.driver.find_element(self._get_by(by_key), selector)

    def _wait(self, seconds: Optional[int] = None) -> WebDriverWait:
        return WebDriverWait(self.driver, seconds if seconds is not None else self.default_timeout)

    def _parse_keys(self, parts: List[str]) -> List[Any]:
        # shlex解析
        out: List[Any] = []
        for t in parts:
            if len(t) >= 3 and t.startswith('{') and t.endswith('}'):
                keyname = t[1:-1].upper()
                if keyname in KEYS:
                    out.append(KEYS[keyname])
                elif keyname in KEY_COMBOS:
                    out.extend(KEY_COMBOS[keyname])
                else:
                    raise ValueError(f'未知键名 -> {t}')
            else:
                if t.upper() in KEY_COMBOS:
                    out.extend(KEY_COMBOS[t.upper()])
                elif t.upper() in KEYS:
                    out.append(KEYS[t.upper()])
                else:
                    out.append(t)
        return out

    # 命令实现（元素操作）
    def cmd_click(self, by_key: str, selector: str):
        self._find(by_key, selector).click()

    def cmd_rclick(self, by_key: str, selector: str):
        ActionChains(self.driver).context_click(self._find(by_key, selector)).perform()

    def cmd_dclick(self, by_key: str, selector: str):
        ActionChains(self.driver).double_click(self._find(by_key, selector)).perform()

    def cmd_hover(self, by_key: str, selector: str):
        ActionChains(self.driver).move_to_element(self._find(by_key, selector)).perform()

    def cmd_click_js(self, by_key: str, selector: str):
        el = self._find(by_key, selector)
        self.driver.execute_script("arguments[0].click();", el)

    def cmd_clear(self, by_key: str, selector: str):
        self._find(by_key, selector).clear()

    def cmd_write(self, by_key: str, selector: str, *text_parts: str):
        el = self._find(by_key, selector)
        el.click()
        el.send_keys(' '.join(text_parts))

    def cmd_send_keys(self, by_key: str, selector: str, *keys_tokens: str):
        el = self._find(by_key, selector)
        el.click()
        seq = self._parse_keys(list(keys_tokens))
        el.send_keys(*seq)

    def cmd_press(self, *keys_tokens: str):
        el = self.driver.switch_to.active_element
        seq = self._parse_keys(list(keys_tokens))
        el.send_keys(*seq)

    def cmd_write_ce(self, by_key: str, selector: str, *text_parts: str):
        el = self._find(by_key, selector)
        text = ' '.join(text_parts)

        # 滚动并聚焦，提升可交互性
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el
            )
        except Exception:
            pass

        self.driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];

            // 尝试聚焦
            try { el.focus(); } catch (e) {}

            // 若非 contenteditable，也尽量按 textbox 处理
            const isCE = (el.isContentEditable === true) ||
                        (el.getAttribute && el.getAttribute('contenteditable') === 'true') ||
                        (el.getAttribute && el.getAttribute('role') === 'textbox');

            // 清空原内容
            try {
                const sel = window.getSelection && window.getSelection();
                if (sel && sel.rangeCount) sel.removeAllRanges();

                const range = document.createRange();
                range.selectNodeContents(el);
                if (sel) sel.addRange(range);

                document.execCommand('delete');
            } catch (e) {
                // fallback: 置空
                try { el.innerText = ''; } catch (e2) {}
            }

            // 写入文本
            let ok = false;
            try {
                ok = document.execCommand && document.execCommand('insertText', false, text);
            } catch (e) {}

            if (!ok) {
                // 兜TMD底
                try { el.innerText = text; } catch (e) { try { el.textContent = text; } catch (e2) {} }
                try {
                    el.dispatchEvent(new InputEvent('input', {bubbles:true, cancelable:true, inputType:'insertText', data:text}));
                } catch (e) {
                    el.dispatchEvent(new Event('input', {bubbles:true}));
                }
                el.dispatchEvent(new Event('change', {bubbles:true}));
            }
        """, el, text)
    
    def cmd_write_js(self, by_key: str, selector: str, *text_parts: str):
        el = self._find(by_key, selector)
        text = ' '.join(text_parts)

        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'nearest'});", el
            )
        except Exception:
            pass

        self.driver.execute_script("""
            const el = arguments[0];
            const text = arguments[1];

            function setValueForInputLike(el, text) {
                const tag = el.tagName ? el.tagName.toLowerCase() : '';
                const isInput = tag === 'input';
                const isTA = tag === 'textarea';

                if (isInput || isTA) {
                    // 使用原型 setter，兼容 React/Vue
                    const proto = isInput ? HTMLInputElement.prototype : HTMLTextAreaElement.prototype;
                    const desc = Object.getOwnPropertyDescriptor(proto, 'value');
                    if (desc && desc.set) {
                        desc.set.call(el, text);
                    } else {
                        el.value = text;
                    }
                    // 触发事件
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            }

            function setForContentEditable(el, text) {
                try { el.focus(); } catch (e) {}
                // 清空
                try {
                    const sel = window.getSelection && window.getSelection();
                    if (sel && sel.rangeCount) sel.removeAllRanges();
                    const range = document.createRange();
                    range.selectNodeContents(el);
                    if (sel) sel.addRange(range);
                    document.execCommand('delete');
                } catch (e) {
                    try { el.innerText = ''; } catch (e2) {}
                }
                // 插入
                let ok = false;
                try { ok = document.execCommand && document.execCommand('insertText', false, text); } catch (e) {}
                if (!ok) {
                    try { el.innerText = text; } catch (e) { try { el.textContent = text; } catch (e2) {} }
                    try {
                        el.dispatchEvent(new InputEvent('input', {bubbles:true, cancelable:true, inputType:'insertText', data:text}));
                    } catch (e) {
                        el.dispatchEvent(new Event('input', {bubbles:true}));
                    }
                    el.dispatchEvent(new Event('change', {bubbles:true}));
                }
            }

            // 处理 input/textarea
            if (setValueForInputLike(el, text)) {
                try { el.focus(); } catch (e) {}
                return;
            }

            // 处理 contenteditable/textbox
            const isCE = (el.isContentEditable === true) ||
                        (el.getAttribute && el.getAttribute('contenteditable') === 'true') ||
                        (el.getAttribute && el.getAttribute('role') === 'textbox');
            if (isCE) {
                setForContentEditable(el, text);
                return;
            }

            // 兜TMD底
            try { el.focus(); } catch (e) {}
            try { el.textContent = text; } catch (e) { try { el.innerText = text; } catch (e2) {} }
            try { el.dispatchEvent(new Event('input', {bubbles:true})); } catch (e) {}
            try { el.dispatchEvent(new Event('change', {bubbles:true})); } catch (e) {}
        """, el, text)

    def cmd_drag_drop(self, by_src: str, sel_src: str, by_dst: str, sel_dst: str):
        src = self._find(by_src, sel_src)
        dst = self._find(by_dst, sel_dst)
        ActionChains(self.driver).drag_and_drop(src, dst).perform()

    def cmd_drag_offset(self, by_key: str, selector: str, x: str, y: str):
        el = self._find(by_key, selector)
        ActionChains(self.driver).drag_and_drop_by_offset(el, parse_int(x, 'x'), parse_int(y, 'y')).perform()

    # 导航与窗口
    def cmd_goto(self, url: str):
        self.driver.get(url)

    def cmd_back(self):
        self.driver.back()

    def cmd_forward(self):
        self.driver.forward()

    def cmd_refresh(self):
        self.driver.refresh()

    def cmd_maximize(self):
        try:
            self.driver.maximize_window()
        except Exception:
            pass

    def cmd_minimize(self):
        try:
            self.driver.minimize_window()
        except Exception:
            pass

    def cmd_set_window(self, width: str, height: str):
        self.driver.set_window_size(parse_int(width, 'width'), parse_int(height, 'height'))

    # Frame
    def cmd_frame(self, by_key: str, selector: str):
        el = self._find(by_key, selector)
        self.driver.switch_to.frame(el)

    def cmd_frame_index(self, index: str):
        self.driver.switch_to.frame(parse_int(index, 'index'))

    def cmd_frame_parent(self):
        self.driver.switch_to.parent_frame()

    def cmd_frame_default(self):
        self.driver.switch_to.default_content()

    # 窗口（Tab）
    def cmd_window_latest(self):
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[-1])

    def cmd_window_index(self, index: str):
        idx = parse_int(index, 'index')
        handles = self.driver.window_handles
        if idx < 0 or idx >= len(handles):
            raise ValueError(f'窗口索引越界 -> {idx}')
        self.driver.switch_to.window(handles[idx])

    def cmd_window_close(self):
        self.driver.close()

    # 等待（Explicit Wait）
    def cmd_wait_present(self, by_key: str, selector: str, timeout: str = ""):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.presence_of_element_located((self._get_by(by_key), selector)))

    def cmd_wait_visible(self, by_key: str, selector: str, timeout: str = ""):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.visibility_of_element_located((self._get_by(by_key), selector)))

    def cmd_wait_clickable(self, by_key: str, selector: str, timeout: str = ""):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.element_to_be_clickable((self._get_by(by_key), selector)))

    def cmd_wait_invisible(self, by_key: str, selector: str, timeout: str = ""):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.invisibility_of_element_located((self._get_by(by_key), selector)))

    def cmd_wait_text(self, by_key: str, selector: str, text: str, timeout: str = ""):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.text_to_be_present_in_element((self._get_by(by_key), selector), text))

    def cmd_wait_url_contains(self, substr: str, timeout: str = ""):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.url_contains(substr))

    def cmd_wait_title_contains(self, substr: str, timeout: str = ""):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.title_contains(substr))

    # 滚动
    def cmd_scroll_into_view(self, by_key: str, selector: str, block: str = 'center'):
        el = self._find(by_key, selector)
        self.driver.execute_script("arguments[0].scrollIntoView({block: arguments[1]});", el, block)

    def cmd_scroll_by(self, x: str, y: str):
        self.driver.execute_script("window.scrollBy(arguments[0], arguments[1]);",
                                   parse_int(x, 'x'), parse_int(y, 'y'))

    def cmd_scroll_top(self):
        self.driver.execute_script("window.scrollTo(0,0);")

    def cmd_scroll_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # 下拉选择
    def cmd_select(self, by_key: str, selector: str, mode: str, value: str):
        el = self._find(by_key, selector)
        sel = Select(el)
        m = mode.lower()
        if m == 'text':
            sel.select_by_visible_text(value)
        elif m == 'value':
            sel.select_by_value(value)
        elif m == 'index':
            sel.select_by_index(parse_int(value, 'index'))
        else:
            raise ValueError(f'select 模式应为 text|value|index -> {mode}')

    # 上传、截图、JS
    def cmd_upload(self, by_key: str, selector: str, file_path: str):
        p = Path(file_path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f'文件不存在 -> {p}')
        self._find(by_key, selector).send_keys(str(p))

    def cmd_screenshot(self, path: str):
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        self.driver.save_screenshot(str(p))

    def cmd_screenshot_element(self, by_key: str, selector: str, path: str):
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        el = self._find(by_key, selector)
        el.screenshot(str(p))

    def cmd_exec_js(self, script: str):
        # 脚本请用引号包裹，参数可进一步扩展
        self.driver.execute_script(script)

    # 断言与打印
    def cmd_assert_text(self, by_key: str, selector: str, expected: str):
        el = self._find(by_key, selector)
        if expected not in (el.text or ''):
            raise AssertionError(f'断言失败：未包含文本 -> {expected}')

    def cmd_assert_url_contains(self, substr: str):
        if substr not in self.driver.current_url:
            raise AssertionError(f'断言失败：URL 未包含 -> {substr}')

    def cmd_assert_title_contains(self, substr: str):
        title = self.driver.title or ''
        if substr not in title:
            raise AssertionError(f'断言失败：标题未包含 -> {substr}')

    def cmd_print_text(self, by_key: str, selector: str):
        print(self._find(by_key, selector).text)

    def cmd_print_attr(self, by_key: str, selector: str, name: str):
        print(self._find(by_key, selector).get_attribute(name))

    def cmd_echo(self, *msg: str):
        print(' '.join(msg))

    # Cookie
    def cmd_cookie_set(self, name: str, value: str):
        self.driver.add_cookie({'name': name, 'value': value})
    
    def cmd_cookies_set(self, values: str):
        for i in values.split(';'):
            res = i.split(':')
            if len(res) != 2:
                raise AssertionError(f'cookie添加失败：未知格式 -> {i}')
            else:
                res[0].replace(" ","")
                res[1].replace(" ","")
                self.driver.add_cookie({'name':res[0], 'value':res[1]})

    def cmd_cookie_get(self, name: str):
        c = self.driver.get_cookie(name)
        print(c if c else '')

    def cmd_cookie_delete(self, name: str):
        self.driver.delete_cookie(name)

    def cmd_cookie_clear(self):
        self.driver.delete_all_cookies()

    # 其他
    def cmd_sleep(self, seconds: str):
        time.sleep(parse_int(seconds, 'seconds'))

    def cmd_pause(self):
        try:
            input('按回车继续 ... ')
        except EOFError:
            pass

    def cmd_keep_open(self):
        self._keep_open = True
    
    def cmd_set_var(self, name: str, var: Any):
        self._var_set[name] = var
    
    def _var_filter(self, part: str):
        if not part or "${" not in part:
            return part
        result = self._fliter.search(part)
        if result == None:
            return part
        else:
            name = part[result.span()[0]: result.span()[1]]
            try:
                part = part.replace(name, str(self._var_set[name[2:-1]]), 1)
                return self._var_filter(part)
            except KeyError as e:
                raise RuntimeError(f'变量未定义 -> {e}')

    # 运行一行命令
    def run_line(self, line: str):
        s = line.strip()
        if not s or s.startswith('#'):
            return

        parts = shlex.split(s, posix=True)
        if not parts:
            return

        for i in range(len(parts)):
            parts[i] = self._var_filter(parts[i])

        raw_cmd = parts[0]
        cmd = ALIASES.get(raw_cmd, raw_cmd).lower()

        try:
            spec = COMMAND_SPECS.get(cmd)
            if not spec:
                raise ValueError(f'非法指令！ -> {raw_cmd}')

            # 准备参数（不含命令名）
            args = parts[1:]

            # 当需要把尾部参数合并成一个时
            if spec.join_from is not None:
                if len(args) < spec.join_from:
                    raise ValueError(f'参数不足 -> {s}')
                head = args[:spec.join_from]
                tail = ' '.join(args[spec.join_from:]) if len(args) > spec.join_from else ''
                args = head + ([tail] if tail != '' or spec.min_args - len(head) == 1 else [])

            # 校验参数个数
            argc = len(args)
            if argc < spec.min_args:
                raise ValueError(f'参数不足 -> {s}')
            if spec.max_args is not None and argc > spec.max_args:
                raise ValueError(f'参数过多 -> {s}')

            # 反射调用目标方法
            func = getattr(self, spec.func, None)
            if not callable(func):
                raise RuntimeError(f'内部错误：未实现方法 {spec.func}')
            func(*args)

        except KeyError as e:
            if self._ginore_error:
                print(f"值错误 -> {e}，继续运行")
            else:
                raise ValueError(str(e))
        except selerr.NoSuchElementException:
            if self._ginore_error:
                print(f"找不到元素 -> {s}，继续运行")
            else:
                raise RuntimeError(f'找不到元素 -> {s}')
        except selerr.InvalidSelectorException:
            if self._ginore_error:
                print(f"查询表达式错误 -> {s}，继续运行")
            else:
                raise RuntimeError(f'查询表达式错误 -> {s}')
        except selerr.ElementNotInteractableException:
            if self._ginore_error:
                print(f"不可交互 -> {s}，继续运行")
            else:
                raise RuntimeError(f'不可交互 -> {s}')
        except selerr.InvalidArgumentException:
            if self._ginore_error:
                print(f"无效参数 -> {s}，继续运行")
            else:
                raise RuntimeError(f'无效参数 -> {s}')
        except selerr.TimeoutException:
            if self._ginore_error:
                print(f"等待超时 -> {s}，继续运行")
            else:
                raise RuntimeError(f'等待超时 -> {s}')

    def run_file(self, command_path: str):
        p = Path(command_path)
        if not p.exists():
            raise FileNotFoundError(f'未查找到指令文件 -> {command_path}')
        with p.open('r', encoding='utf-8') as f:
            for raw in f:
                self.run_line(raw)


def get_driver(browser: str, ver_b: str, ver_s: str):
    print("下载中。。。")
    if browser == "edge":
        resopnse = requests.get(f"https://msedgedriver.microsoft.com/{ver_b}/edgedriver_{ver_s}.zip")
        if resopnse.status_code != 200:
            print(f"下载失败，请重试，状态码：{resopnse.status_code}")
        
        with open('./web_driver.zip', 'wb') as f:
            f.write(resopnse.content)
            f.close()
        print("下载成功")
        print("请解压压缩包并保留可执行文件（通常叫做*****driver.exe），之后将可执行文件放在与软件同级的目录里")
    
    elif browser == "chrome":
        if ver_s == "arm64":
            print("没有找到适用于windows的arm64，请在https://googlechromelabs.github.io/chrome-for-testing/自行寻找")
        
        resopnse = requests.get(f"https://storage.googleapis.com/chrome-for-testing-public/{ver_b}/{ver_s}/chromedriver-{ver_s}.zip")
        if resopnse.status_code != 200:
            print(f"下载失败，请重试，状态码：{resopnse.status_code}")
        
        with open('./web_driver.zip', 'wb') as f:
            f.write(resopnse.content)
            f.close()
        print("下载成功")
        print("请解压压缩包并保留可执行文件（通常叫做*****driver.exe），之后将可执行文件放在与软件同级的目录里")


def main():
    parser = argparse.ArgumentParser(description='命令式网页自动化执行器')
    parser.add_argument('--driver', type=str, default='edge', choices=['edge', 'chrome', 'firefox'], help='浏览器类型')
    parser.add_argument('--driver-path', type=str, default='msedgedriver.exe', help='浏览器驱动路径（可选）')
    parser.add_argument('--start-url', type=str, default='', help='启动后访问的初始 URL（可选）')
    parser.add_argument('--commands', type=str, default="command.txt", help='命令脚本文件路径')
    parser.add_argument('--maximize', action='store_true', help='启动后最大化窗口')
    parser.add_argument('--headless', action='store_true', help='Headless 模式运行（无窗口模式）')
    parser.add_argument('--timeout', type=int, default=15, help='默认显式等待超时秒数')
    parser.add_argument('--version', action='store_true', help='展示版本')
    parser.add_argument('-v', action='store_true', help='展示版本')
    parser.add_argument("--download-driver", action='store_true', help="安装浏览器驱动（edge, chrome）")
    parser.add_argument('--user-agent', type=str, help="User-Agent")
    parser.add_argument('--anti-ac', action='store_true', default=False, help="反“反爬虫”")
    parser.add_argument('--user-data', type=str, default="", help='用户数据文件夹')
    parser.add_argument('--profile-data', type=str, default="", help='用户资料文件夹')
    parser.add_argument('--weixin-emu', action='store_true', help='启用微信移动端仿真（UA+UACH+设备）')
    parser.add_argument('--net-harden', action='store_true', help='启用网络栈容错（禁QUIC、忽略证书错误等）')
    parser.add_argument('--netlog', type=str, default='', help='写出 Chrome NetLog 到文件（可选）')
    parser.add_argument('--debugger-address', type=str, default='', help='附着调试地址，如 127.0.0.1:9222')
    parser.add_argument('--error-no-quit', action='store_true', default=False, help='发生错误不关闭浏览器')
    parser.add_argument('--ignore-error', action='store_true', default=False, help='忽略并跳过发生错误的语句')
    args = parser.parse_args()

    driver = None
    exit_flag = False
    try:
        if args.v or args.version:
            print(f"Easy Selenium {VERSION} by N_E")
            exit_flag = True
            return None
        
        if args.download_driver:
            browser = input("请输入目标浏览器(edge、chrome)：")
            ver_browser = input("请输入你的浏览器版本号：")
            ver_sys = input("请输入你的系统版本(win32、win64、arm64)：")

            get_driver(browser, ver_browser, ver_sys)
            
            exit_flag = True
            return None

        # 规范化user-data-dir
        final_user_data = normalize_abs_path(args.user_data) if args.user_data else ""
        if final_user_data:
            final_user_data = prepare_unique_user_data_dir(final_user_data)
            print(f"使用的用户数据目录：{final_user_data}")

        # profile-data：对于“新建目录”请不要强制传；若你要复用真实目录才需要。
        final_profile = args.profile_data if args.profile_data else ""

        
        driver = build_driver(
            args.driver,
            args.driver_path,
            args.user_agent,
            final_user_data,
            final_profile,
            anti_ac=args.anti_ac,
            headless=args.headless,
            net_harden=args.net_harden,
            netlog_path=args.netlog,
            debugger_address=args.debugger_address
        )

        if args.weixin_emu:
            # 若命令行无 --user-agent，则使用内置 ANDROID 微信 UA
            # apply_wechat_emulation(driver, ua=args.user_agent if args.user_agent else "")
            set_ua_via_cdp(driver, 'MicroMessenger')


        if args.anti_ac:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined})
                    Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
                    Object.defineProperty(navigator, 'plugins',   { get: () => [1,2,3,4,5] });
                    """
            })

        if args.maximize and not args.headless:
            try:
                driver.maximize_window()
            except Exception:
                pass

        if args.start_url:
            driver.get(args.start_url)

        executor = CommandExecutor(driver, args.ignore_error, default_timeout=args.timeout)
        executor.run_file(args.commands)

        if executor.keep_open:
            print('执行完成，保持打开。按 Ctrl+C 退出，或关闭浏览器窗口。')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

    except Exception as e:
        print(f'[错误] {e}', file=sys.stderr)
        if args.quit:
            print('发生错误，保持打开。按 Ctrl+C 退出，或关闭浏览器窗口。')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            sys.exit(1)
    finally:
        if exit_flag:
            return None
        
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == '__main__':
    main()