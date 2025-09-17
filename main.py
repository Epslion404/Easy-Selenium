#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令式网页自动化执行器（通用版）

功能
- 从命令文件读取指令，驱动 Selenium WebDriver 执行浏览器操作。
- 支持命令：
  - L_click <BY> <selector>
  - R_click <BY> <selector>
  - D_click <BY> <selector>
  - put <BY> <selector>              # 移动鼠标到元素
  - write <BY> <selector> <text>     # 文本中不含空格（与原版一致）
  - jump <url>                       # 跳转
  - delay <seconds>                  # 休眠秒数
  - pause                            # 等待用户按回车
  - keep_open                        # 执行完毕保持浏览器不关闭
  - # ...（注释行）

使用示例
  python cmd_web_automation.py --driver edge --driver-path msedgedriver.exe \
    --start-url https://example.com --commands command.txt --maximize
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common import exceptions as selerr

# 可选：支持多浏览器
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


SEARCH: Dict[str, By] = {
    'XPATH': By.XPATH,
    'CLASS': By.CLASS_NAME,
    'ID': By.ID,
    'TAG': By.TAG_NAME,
    'LINK': By.LINK_TEXT,
    'NAME': By.NAME,
    'CSS': By.CSS_SELECTOR,
}


def delay(sec: int) -> None:
    time.sleep(sec)


class CommandExecutor:
    def __init__(self, driver):
        self.driver = driver
        self._keep_open = False

    @property
    def keep_open(self) -> bool:
        return self._keep_open

    def _get_by(self, key: str) -> By:
        try:
            return SEARCH[key]
        except KeyError:
            raise KeyError(f'查询方式错误 -> {key}')

    def _find(self, by_key: str, selector: str):
        by = self._get_by(by_key)
        return self.driver.find_element(by=by, value=selector)

    def _left_click(self, by_key: str, selector: str) -> None:
        self._find(by_key, selector).click()

    def _right_click(self, by_key: str, selector: str) -> None:
        ActionChains(self.driver).context_click(self._find(by_key, selector)).perform()

    def _double_click(self, by_key: str, selector: str) -> None:
        ActionChains(self.driver).double_click(self._find(by_key, selector)).perform()

    def _move_to(self, by_key: str, selector: str) -> None:
        ActionChains(self.driver).move_to_element(self._find(by_key, selector)).perform()

    def _write(self, by_key: str, selector: str, text: str) -> None:
        el = self._find(by_key, selector)
        el.click()
        el.send_keys(text)

    def _jump(self, url: str) -> None:
        self.driver.get(url)

    def _pause(self) -> None:
        try:
            input("按回车继续 ... ")
        except EOFError:
            # 无交互终端时直接跳过
            pass

    def run_line(self, line: str) -> None:
        s = line.strip()
        if not s or s.startswith('#'):
            return

        parts = s.split()
        cmd = parts[0]

        try:
            if cmd == 'L_click':
                self._left_click(parts[1], parts[2])
            elif cmd == 'R_click':
                self._right_click(parts[1], parts[2])
            elif cmd == 'D_click':
                self._double_click(parts[1], parts[2])
            elif cmd == 'put':
                self._move_to(parts[1], parts[2])
            elif cmd == 'write':
                # 与原脚本保持一致：text 不含空格
                self._write(parts[1], parts[2], parts[3])
            elif cmd == 'jump':
                self._jump(parts[1])
            elif cmd == 'delay':
                delay(int(parts[1]))
            elif cmd == 'pause':
                self._pause()
            elif cmd == 'keep_open':
                self._keep_open = True
            elif cmd == '#':
                pass
            else:
                raise ValueError(f'非法指令！ -> {cmd}')

        except IndexError:
            raise ValueError(f'参数不足 -> {s}')

        except selerr.NoSuchElementException:
            raise RuntimeError(f'找不到 -> {parts[2] if len(parts) > 2 else s}')

        except selerr.InvalidSelectorException:
            raise RuntimeError(f'查询表达式书写错误或找不到 -> {parts[2] if len(parts) > 2 else s}')

        except selerr.ElementNotInteractableException:
            raise RuntimeError(f'不可交互 -> {parts[2] if len(parts) > 2 else s}')

        except selerr.InvalidArgumentException:
            raise RuntimeError(f'无效参数 -> {s}')

    def run_file(self, command_path: str) -> None:
        p = Path(command_path)
        if not p.exists():
            raise FileNotFoundError(f'未查找到指令文件 -> {command_path}')

        with p.open('r', encoding='utf-8') as f:
            for raw in f:
                self.run_line(raw)


def build_driver(name: str, driver_path: str, headless: bool = False):
    name = name.lower()
    if name == 'edge':
        options = EdgeOptions()
        if headless:
            options.add_argument('--headless=new')
        service = EdgeService(executable_path=driver_path) if driver_path else EdgeService()
        return webdriver.Edge(service=service, options=options)

    if name == 'chrome':
        options = ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        service = ChromeService(executable_path=driver_path) if driver_path else ChromeService()
        return webdriver.Chrome(service=service, options=options)

    if name == 'firefox':
        options = FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        service = FirefoxService(executable_path=driver_path) if driver_path else FirefoxService()
        return webdriver.Firefox(service=service, options=options)

    raise ValueError(f'不支持的浏览器 -> {name}')


def main():
    parser = argparse.ArgumentParser(description='命令式网页自动化执行器')
    parser.add_argument('--driver', type=str, default='edge', choices=['edge', 'chrome', 'firefox'], help='浏览器类型')
    parser.add_argument('--driver-path', type=str, default='', help='浏览器驱动路径（可选）')
    parser.add_argument('--start-url', type=str, default='', help='启动后访问的初始 URL（可选）')
    parser.add_argument('--commands', type=str, default=".\\command.txt", help='命令脚本文件路径')
    parser.add_argument('--maximize', action='store_true', help='启动后最大化窗口')
    parser.add_argument('--headless', action='store_true', help='Headless 模式运行')
    args = parser.parse_args()

    driver = None
    try:
        driver = build_driver(args.driver, args.driver_path, headless=args.headless)

        if args.maximize and not args.headless:
            try:
                driver.maximize_window()
            except Exception:
                pass

        if args.start_url:
            driver.get(args.start_url)

        executor = CommandExecutor(driver)
        executor.run_file(args.commands)

        if executor.keep_open:
            print('执行完成（保持打开）。按 Ctrl+C 退出，或关闭浏览器窗口。')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

    except Exception as e:
        print(f'[错误] {e}', file=sys.stderr)
        sys.exit(1)

    finally:
        # headless 场景或非 keep_open 场景清理
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == '__main__':
    main()