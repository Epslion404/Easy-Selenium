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
import time
import shlex
import os
import shutil
import tempfile
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

VERSION = "v1.0.0"

SEARCH: Dict[str, By] = {
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
            options.add_argument('--net-log-capture-mode=IncludeCookiesAndCredentials')

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
            options.add_argument('--net-log-capture-mode=IncludeCookiesAndCredentials')

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
    def __init__(self, driver, default_timeout: int = 15, user_agent: str = ""):
        self.driver = driver
        self.default_timeout = default_timeout
        self._keep_open = False
        self.user_agent = user_agent

    @property
    def keep_open(self) -> bool:
        return self._keep_open

    # 基础工具
    def _get_by(self, key: str) -> By:
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
    def cmd_wait_present(self, by_key: str, selector: str, timeout: str = None):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.presence_of_element_located((self._get_by(by_key), selector)))

    def cmd_wait_visible(self, by_key: str, selector: str, timeout: str = None):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.visibility_of_element_located((self._get_by(by_key), selector)))

    def cmd_wait_clickable(self, by_key: str, selector: str, timeout: str = None):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.element_to_be_clickable((self._get_by(by_key), selector)))

    def cmd_wait_invisible(self, by_key: str, selector: str, timeout: str = None):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.invisibility_of_element_located((self._get_by(by_key), selector)))

    def cmd_wait_text(self, by_key: str, selector: str, text: str, timeout: str = None):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.text_to_be_present_in_element((self._get_by(by_key), selector), text))

    def cmd_wait_url_contains(self, substr: str, timeout: str = None):
        t = parse_int(timeout, 'timeout') if timeout else None
        self._wait(t).until(EC.url_contains(substr))

    def cmd_wait_title_contains(self, substr: str, timeout: str = None):
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

    # 运行一行命令
    def run_line(self, line: str):
        s = line.strip()

        # 注释
        if not s or s.startswith('#'):
            return

        parts = shlex.split(s, posix=True)
        if not parts:
            return

        raw_cmd = parts[0]
        cmd = ALIASES.get(raw_cmd, raw_cmd).lower()

        try:
            # 元素点击与输入
            if cmd == 'click':
                self.cmd_click(parts[1], parts[2])
            elif cmd == 'rclick':
                self.cmd_rclick(parts[1], parts[2])
            elif cmd == 'dclick':
                self.cmd_dclick(parts[1], parts[2])
            elif cmd == 'hover':
                self.cmd_hover(parts[1], parts[2])
            elif cmd == 'click_js':
                self.cmd_click_js(parts[1], parts[2])
            elif cmd == 'clear':
                self.cmd_clear(parts[1], parts[2])
            elif cmd == 'write':
                self.cmd_write(parts[1], parts[2], *parts[3:])
            elif cmd == 'send_keys':
                self.cmd_send_keys(parts[1], parts[2], *parts[3:])
            elif cmd == 'press':
                self.cmd_press(*parts[1:])

            # 拖拽
            elif cmd == 'drag_drop':
                self.cmd_drag_drop(parts[1], parts[2], parts[3], parts[4])
            elif cmd == 'drag_offset':
                self.cmd_drag_offset(parts[1], parts[2], parts[3], parts[4])

            # 导航
            elif cmd == 'goto':
                self.cmd_goto(parts[1])
            elif cmd == 'back':
                self.cmd_back()
            elif cmd == 'forward':
                self.cmd_forward()
            elif cmd == 'refresh':
                self.cmd_refresh()
            elif cmd == 'maximize':
                self.cmd_maximize()
            elif cmd == 'minimize':
                self.cmd_minimize()
            elif cmd == 'set_window':
                self.cmd_set_window(parts[1], parts[2])

            # Frame
            elif cmd == 'frame':
                self.cmd_frame(parts[1], parts[2])
            elif cmd == 'frame_index':
                self.cmd_frame_index(parts[1])
            elif cmd == 'frame_parent':
                self.cmd_frame_parent()
            elif cmd == 'frame_default':
                self.cmd_frame_default()

            # 窗口
            elif cmd == 'window_latest':
                self.cmd_window_latest()
            elif cmd == 'window_index':
                self.cmd_window_index(parts[1])
            elif cmd == 'window_close':
                self.cmd_window_close()

            # 等待
            elif cmd == 'wait_present':
                self.cmd_wait_present(parts[1], parts[2], parts[3] if len(parts) > 3 else None)
            elif cmd == 'wait_visible':
                self.cmd_wait_visible(parts[1], parts[2], parts[3] if len(parts) > 3 else None)
            elif cmd == 'wait_clickable':
                self.cmd_wait_clickable(parts[1], parts[2], parts[3] if len(parts) > 3 else None)
            elif cmd == 'wait_invisible':
                self.cmd_wait_invisible(parts[1], parts[2], parts[3] if len(parts) > 3 else None)
            elif cmd == 'wait_text':
                # wait_text <BY> <selector> "<text>" [timeout]
                if len(parts) == 5:
                    self.cmd_wait_text(parts[1], parts[2], parts[3], parts[4])
                else:
                    self.cmd_wait_text(parts[1], parts[2], parts[3])
            elif cmd == 'wait_url_contains':
                self.cmd_wait_url_contains(parts[1], parts[2] if len(parts) > 2 else None)
            elif cmd == 'wait_title_contains':
                self.cmd_wait_title_contains(parts[1], parts[2] if len(parts) > 2 else None)

            # 滚动
            elif cmd == 'scroll_into_view':
                self.cmd_scroll_into_view(parts[1], parts[2], parts[3] if len(parts) > 3 else 'center')
            elif cmd == 'scroll_by':
                self.cmd_scroll_by(parts[1], parts[2])
            elif cmd == 'scroll_top':
                self.cmd_scroll_top()
            elif cmd == 'scroll_bottom':
                self.cmd_scroll_bottom()

            # 下拉选择
            elif cmd == 'select':
                self.cmd_select(parts[1], parts[2], parts[3], parts[4])

            # 上传/截图/JS
            elif cmd == 'upload':
                self.cmd_upload(parts[1], parts[2], parts[3])
            elif cmd == 'screenshot':
                self.cmd_screenshot(parts[1])
            elif cmd == 'screenshot_element':
                self.cmd_screenshot_element(parts[1], parts[2], parts[3])
            elif cmd == 'exec_js':
                self.cmd_exec_js(join_rest(parts, 1))

            # 断言/打印
            elif cmd == 'assert_text':
                self.cmd_assert_text(parts[1], parts[2], join_rest(parts, 3))
            elif cmd == 'assert_url_contains':
                self.cmd_assert_url_contains(join_rest(parts, 1))
            elif cmd == 'assert_title_contains':
                self.cmd_assert_title_contains(join_rest(parts, 1))
            elif cmd == 'print_text':
                self.cmd_print_text(parts[1], parts[2])
            elif cmd == 'print_attr':
                self.cmd_print_attr(parts[1], parts[2], parts[3])
            elif cmd == 'echo':
                self.cmd_echo(*parts[1:])

            # Cookie
            elif cmd == 'cookie_set':
                self.cmd_cookie_set(parts[1], parts[2])
            elif cmd == 'cookies_set':
                self.cmd_cookies_set(parts[1])
            elif cmd == 'cookie_get':
                self.cmd_cookie_get(parts[1])
            elif cmd == 'cookie_delete':
                self.cmd_cookie_delete(parts[1])
            elif cmd == 'cookie_clear':
                self.cmd_cookie_clear()

            # 其他
            elif cmd == 'sleep':
                self.cmd_sleep(parts[1])
            elif cmd == 'pause':
                self.cmd_pause()
            elif cmd == 'keep_open':
                self.cmd_keep_open()

            else:
                raise ValueError(f'非法指令！ -> {raw_cmd}')

        except IndexError:
            raise ValueError(f'参数不足 -> {s}')
        except KeyError as e:
            raise ValueError(str(e))
        except selerr.NoSuchElementException:
            raise RuntimeError(f'找不到元素 -> {s}')
        except selerr.InvalidSelectorException:
            raise RuntimeError(f'查询表达式错误 -> {s}')
        except selerr.ElementNotInteractableException:
            raise RuntimeError(f'不可交互 -> {s}')
        except selerr.InvalidArgumentException:
            raise RuntimeError(f'无效参数 -> {s}')

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
    parser.add_argument('--driver-path', type=str, default='', help='浏览器驱动路径（可选）')
    parser.add_argument('--start-url', type=str, default='', help='启动后访问的初始 URL（可选）')
    parser.add_argument('--commands', type=str, default="command.txt", help='命令脚本文件路径')
    parser.add_argument('--maximize', action='store_true', help='启动后最大化窗口')
    parser.add_argument('--headless', action='store_true', help='Headless 模式运行（无窗口模式）')
    parser.add_argument('--timeout', type=int, default=15, help='默认显式等待超时秒数')
    parser.add_argument('--version', action='store_true', help='展示版本')
    parser.add_argument('-v', action='store_true', help='展示版本')
    parser.add_argument("--install-driver", action='store_true', help="安装浏览器驱动（edge, chrome）")
    parser.add_argument('--user-agent', type=str, help="User-Agent")
    parser.add_argument('--anti-ac', action='store_true', default=False, help="反“反爬虫”")
    parser.add_argument('--user-data', type=str, default="", help='用户数据文件夹')
    parser.add_argument('--profile-data', type=str, default="", help='用户资料文件夹')
    parser.add_argument('--weixin-emu', action='store_true', help='启用微信移动端仿真（UA+UACH+设备）')
    parser.add_argument('--net-harden', action='store_true', help='启用网络栈容错（禁QUIC、忽略证书错误等）')
    parser.add_argument('--netlog', type=str, default='', help='写出 Chrome NetLog 到文件（可选）')
    parser.add_argument('--debugger-address', type=str, default='', help='附着调试地址，如 127.0.0.1:9222')
    args = parser.parse_args()

    driver = None
    exit_flag = False
    try:
        if args.v or args.version:
            print(f"Easy Selenium {VERSION} by N_E")
            exit_flag = True
            return None
        
        if args.install_driver:
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

        executor = CommandExecutor(driver, default_timeout=args.timeout)
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