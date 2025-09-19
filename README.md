# Easy Selenium

#### 介绍

命令式网页自动化，源于高中遗留项目，Powered by GPT-5

#### 软件架构

使用python 3.10.10开发

#### 安装教程

下载最新release文件

#### 使用说明

1. 解压本软件
2. 在commands文件夹内新建命令文件（文本文件`.txt`即可）
3. 回到上一级文件夹修改`run.bat`内容，将`--commands .\command\cmd1.txt`中的'`cmd1.txt`改为你刚刚新建的命令文件
4. 自定义其他参数
5. 运行`run.bat`，等待任务完成

#### 参与贡献

1.  me
2.  GPT-5

#### 特性

- 跨浏览器：支持 Edge、Chrome、Firefox，支持 headless。
- 命令直观：点击、输入、等待、滚动、frame/tab、下拉框、上传、断言、键盘、JS、Cookie。
- 引号与空格：命令使用 shlex 解析，参数可包含空格与中文。
- 默认等待超时时间：15s

#### 命令语法

##### 速览

- 基础元素操作
  - click/rclick/dclick: `click <BY> <selector>`
  - hover: `hover <BY> <selector>`
  - click_js: `click_js <BY> <selector>`
  - write: `write <BY> <selector> "<text 可含空格>"`
  - clear: `clear <BY> <selector>`
  - send_keys: `send_keys <BY> <selector> <keys...>`
  - press: `press <keys...>`（发给当前焦点元素）
  - 支持键名：`{ENTER} {TAB} {ESC} CTRL_A CTRL_C CTRL_V ...`；普通文本可用引号。

- 拖拽
  - drag_drop: `drag_drop <BY> <src> <BY> <dst>`
  - drag_offset: `drag_offset <BY> <selector> <x> <y>`

- 导航与窗口
  - goto/back/forward/refresh: `goto <url>`
  - maximize/minimize/set_window: `set_window <width> <height>`
  - window_latest/window_index/window_close: `window_index 1`

- Frame
  - frame/frame_index/frame_parent/frame_default:
    - `frame XPATH "//iframe[@id='f']"`
    - `frame_index 0`
    - `frame_parent`
    - `frame_default`

- 等待（显式）
  - wait_present: `wait_present <BY> <selector> [timeout]`
  - wait_visible: `wait_visible <BY> <selector> [timeout]`
  - wait_clickable: `wait_clickable <BY> <selector> [timeout]`
  - wait_invisible: `wait_invisible <BY> <selector> [timeout]`
  - wait_text: `wait_text <BY> <selector> "<text>" [timeout]`
  - wait_url_contains: `wait_url_contains "<substr>" [timeout]`
  - wait_title_contains: `wait_title_contains "<substr>" [timeout]`

- 滚动
  - scroll_into_view: `scroll_into_view <BY> <selector> [block]`（center|start|end）
  - scroll_by: `scroll_by <x> <y>`
  - scroll_top/scroll_bottom

- 下拉框
  - select: `select <BY> <selector> (text|value|index) <value>`

- 上传/截图/JS
  - upload: `upload <BY> <selector> "<file_path>"`
  - screenshot: `screenshot "<file_path>"`
  - screenshot_element: `screenshot_element <BY> <selector> "<file_path>"`
  - exec_js: `exec_js "window.scrollTo(0,0)"`

- 断言/打印
  - assert_text: `assert_text <BY> <selector> "<expected_substr>"`
  - assert_url_contains: `assert_url_contains "<substr>"`
  - assert_title_contains: `assert_title_contains "<substr>"`
  - print_text/print_attr: `print_text <BY> <selector>` / `print_attr <BY> <selector> <name>`
  - echo: `echo "消息"`

- Cookie
  - cookie_set/cookies_set/cookie_get/cookie_delete/cookie_clear

- 其他
  - sleep: `sleep <seconds>`
  - pause: `pause`
  - keep_open: `keep_open`

- BY 取值
  - XPATH, CSS, ID, NAME, CLASS, TAG, LINK（全匹配链接文本）, PLINK（部分匹配链接文本）

- 兼容旧指令别名
  - L_click/ R_click/ D_click/ put/ write/ jump/ delay/ pause/ keep_open

- 常见选择器示例
  - XPATH: `//input[@name="q"]`
  - CSS: `input[name="q"]`
  - LINK: `登录`，PLINK: `登`

# 详细教程

## 基本约定

- 选择器定位（BY，大小写不敏感）
  - XPATH、CSS、ID、NAME、CLASS、TAG、LINK（链接文本全匹配）、PLINK（链接文本部分匹配）
- 引号与空格
  - 参数若包含空格或特殊字符，使用引号（"…" 或 '…'）包裹
- 键盘输入
  - 特殊键：使用花括号包裹，如 `{ENTER} {TAB} {ESC}`
  - 组合键别名：`CTRL_A CTRL_C CTRL_V …`；也可 `{CTRL} a`
- 显式等待超时
  - 未显式提供 `timeout` 的 wait_* 命令使用全局默认（CLI 参数 `--timeout`，默认 15 秒）
- 错误类型（常见）
  - 找不到元素：选择器无匹配或元素尚未渲染
  - 查询表达式错误：BY 与 selector 不匹配或 selector 语法错误
  - 不可交互：元素不可见/被遮挡/禁用
  - 参数不足/格式错误：命令参数缺失或类型不正确

在此引用文章：  
[XPATH教程](https://blog.csdn.net/weixin_43865008/article/details/115332404)(tips:在开发者工具（按下F12里右键元素即可复制完整Xpath）)  
[CSS选择器教程](https://blog.csdn.net/qq_45914609/article/details/142342792)  

---

## 兼容别名

- L_click → click
- R_click → rclick
- D_click → dclick
- put → hover
- jump → goto
- delay → sleep
- pause → pause
- keep_open → keep_open

---

## 元素操作

### click
- 语法：`click <BY> <selector>`
- 说明：对目标元素执行左键点击
- 参数：
  - BY：定位方式（如 XPATH/CSS/ID…）
  - selector：选择器字符串
- 常见错误：找不到元素、不可交互、查询表达式错误
- 示例：
  ```text
  click CSS button.submit
  click XPATH "//button[@type='submit']"
  ```

### rclick
- 语法：`rclick <BY> <selector>`
- 说明：右键点击（上下文菜单）
- 参数：同 click
- 示例：
  ```text
  rclick CSS .file-item
  ```

### dclick
- 语法：`dclick <BY> <selector>`
- 说明：双击
- 参数：同 click
- 示例：
  ```text
  dclick PLINK "详情"
  ```

### hover
- 语法：`hover <BY> <selector>`
- 说明：鼠标悬停（触发悬浮菜单/提示等）
- 参数：同 click
- 示例：
  ```text
  hover CSS .menu
  ```

### click_js
- 语法：`click_js <BY> <selector>`
- 说明：通过 JavaScript 触发元素点击（绕开遮挡/布局问题）
- 参数：同 click
- 示例：
  ```text
  click_js CSS .hidden-button
  ```

### clear
- 语法：`clear <BY> <selector>`
- 说明：清空输入框内容
- 参数：同 click
- 示例：
  ```text
  clear NAME username
  ```

### write
- 语法：`write <BY> <selector> "<text>"`
- 说明：点击输入框并输入文本；文本可包含空格
- 参数：
  - text：输入内容，建议使用引号
- 示例：
  ```text
  write CSS input[name="q"] "关键字 搜索"
  ```

### send_keys
- 语法：`send_keys <BY> <selector> <keys...>`
- 说明：向元素发送按键序列（可混合文本与特殊键/组合键）
- 参数：
  - keys：如 `"hello"` `{ENTER}` `CTRL_A` `{CTRL} c`
- 示例：
  ```text
  send_keys CSS input[name="q"] "hello world" {ENTER}
  send_keys CSS input[name="name"] CTRL_A "新名字"
  ```

### press
- 语法：`press <keys...>`
- 说明：向“当前焦点元素”发送按键序列
- 示例：
  ```text
  press {CTRL} "l"
  press CTRL_A {DELETE}
  ```

### drag_drop
- 语法：`drag_drop <BY> <src_selector> <BY> <dst_selector>`
- 说明：将源元素拖拽到目标元素上
- 示例：
  ```text
  drag_drop CSS .drag-src CSS .drop-zone
  ```

### drag_offset
- 语法：`drag_offset <BY> <selector> <x> <y>`
- 说明：将元素按位移拖拽（像素）
- 参数：
  - x, y：整数（可为负）
- 示例：
  ```text
  drag_offset CSS .slider 80 0
  ```

---

## 导航与窗口

### goto
- 语法：`goto <url>`
- 说明：跳转到指定 URL
- 示例：
  ```text
  goto https://example.com/login
  ```

### back / forward / refresh
- 语法：`back` / `forward` / `refresh`
- 说明：浏览器后退/前进/刷新
- 示例：
  ```text
  back
  refresh
  ```

### maximize / minimize
- 语法：`maximize` / `minimize`
- 说明：最大化/最小化窗口（headless 下部分浏览器无效）
- 示例：
  ```text
  maximize
  ```

### set_window
- 语法：`set_window <width> <height>`
- 说明：设置窗口大小（整数像素）
- 示例：
  ```text
  set_window 1920 1080
  ```

---

## Frame 切换

### frame
- 语法：`frame <BY> <selector>`
- 说明：切换到 iframe（通过元素定位）
- 示例：
  ```text
  frame XPATH "//iframe[@id='content']"
  ```

### frame_index
- 语法：`frame_index <index>`
- 说明：按索引切入 frame（0 基）
- 示例：
  ```text
  frame_index 0
  ```

### frame_parent / frame_default
- 语法：`frame_parent` / `frame_default`
- 说明：切换到上一级 frame / 回到默认文档上下文
- 示例：
  ```text
  frame_parent
  frame_default
  ```

---

## 窗口（Tab）

### window_latest
- 语法：`window_latest`
- 说明：切换到最新打开的窗口/标签页
- 示例：
  ```text
  window_latest
  ```

### window_index
- 语法：`window_index <i>`
- 说明：按索引切换窗口（0 基）；索引越界会报错
- 示例：
  ```text
  window_index 1
  ```

### window_close
- 语法：`window_close`
- 说明：关闭当前窗口（关闭后需手动切换到其他窗口，如果还有）
- 示例：
  ```text
  window_close
  ```

---

## 显式等待（推荐）

注：未提供 timeout 时，使用全局默认超时（CLI `--timeout`）。

### wait_present
- 语法：`wait_present <BY> <selector> [timeout]`
- 说明：等待元素存在于 DOM（不保证可见/可点）
- 示例：
  ```text
  wait_present CSS .list-item 10
  ```

### wait_visible
- 语法：`wait_visible <BY> <selector> [timeout]`
- 说明：等待元素可见
- 示例：
  ```text
  wait_visible ID login-form 15
  ```

### wait_clickable
- 语法：`wait_clickable <BY> <selector> [timeout]`
- 说明：等待元素可点击（可见且可交互）
- 示例：
  ```text
  wait_clickable CSS button.submit 10
  ```

### wait_invisible
- 语法：`wait_invisible <BY> <selector> [timeout]`
- 说明：等待元素不可见或从 DOM 移除
- 示例：
  ```text
  wait_invisible CSS .loading 20
  ```

### wait_text
- 语法：`wait_text <BY> <selector> "<text>" [timeout]`
- 说明：等待元素文本包含指定子串
- 示例：
  ```text
  wait_text CSS .result "成功" 15
  ```

### wait_url_contains
- 语法：`wait_url_contains "<substr>" [timeout]`
- 说明：等待当前 URL 包含子串
- 示例：
  ```text
  wait_url_contains "/dashboard" 10
  ```

### wait_title_contains
- 语法：`wait_title_contains "<substr>" [timeout]`
- 说明：等待页面标题包含子串
- 示例：
  ```text
  wait_title_contains "仪表盘"
  ```

---

## 滚动

### scroll_into_view
- 语法：`scroll_into_view <BY> <selector> [block]`
- 说明：滚动使元素进入视口；block 指定对齐位置
- 参数：
  - block：`center`（默认）| `start` | `end`
- 示例：
  ```text
  scroll_into_view CSS .footer start
  ```

### scroll_by
- 语法：`scroll_by <x> <y>`
- 说明：按位移滚动窗口（像素，整数）
- 示例：
  ```text
  scroll_by 0 800
  ```

### scroll_top / scroll_bottom
- 语法：`scroll_top` / `scroll_bottom`
- 说明：滚动到顶部/底部
- 示例：
  ```text
  scroll_bottom
  ```

---

## 下拉框选择

### select
- 语法：`select <BY> <selector> (text|value|index) <value>`
- 说明：对 `<select>` 元素进行选项选择
- 参数：
  - 模式：
    - text：按可见文本
    - value：按值属性
    - index：按索引（整数，0 基）
- 示例：
  ```text
  select ID city text "上海市"
  select NAME lang value "zh-CN"
  select CSS select#page index 2
  ```

---

## 上传 / 截图 / 执行 JS

### upload
- 语法：`upload <BY> <selector> "<file_path>"`
- 说明：向 `<input type="file">` 输入文件路径（需可访问）
- 注意：路径将解析为绝对路径；不存在会报错
- 示例：
  ```text
  upload CSS input[type="file"] "./data/upload.png"
  ```

### screenshot
- 语法：`screenshot "<file_path>"`
- 说明：页面全屏截图；会自动创建父目录
- 示例：
  ```text
  screenshot "./out/page.png"
  ```

### screenshot_element
- 语法：`screenshot_element <BY> <selector> "<file_path>"`
- 说明：元素截图；会自动创建父目录
- 示例：
  ```text
  screenshot_element CSS .result "./out/result.png"
  ```

### exec_js
- 语法：`exec_js "<javascript 代码>"`
- 说明：在页面上下文直接执行 JS（无返回处理）
- 示例：
  ```text
  exec_js "window.scrollTo(0,0)"
  exec_js "console.log('hello from automation')"
  ```

---

## 断言与输出

### assert_text
- 语法：`assert_text <BY> <selector> "<expected_substr>"`
- 说明：断言元素文本包含子串；失败抛出错误
- 示例：
  ```text
  assert_text CSS .toast "操作成功"
  ```

### assert_url_contains
- 语法：`assert_url_contains "<substr>"`
- 说明：断言当前 URL 包含子串
- 示例：
  ```text
  assert_url_contains "/dashboard"
  ```

### assert_title_contains
- 语法：`assert_title_contains "<substr>"`
- 说明：断言页面标题包含子串
- 示例：
  ```text
  assert_title_contains "仪表盘"
  ```

### print_text
- 语法：`print_text <BY> <selector>`
- 说明：打印元素文本到控制台
- 示例：
  ```text
  print_text CSS .user-name
  ```

### print_attr
- 语法：`print_attr <BY> <selector> <name>`
- 说明：打印元素属性值到控制台
- 示例：
  ```text
  print_attr CSS a.download href
  ```

### echo
- 语法：`echo "<message>"`
- 说明：输出一条消息到控制台
- 示例：
  ```text
  echo "步骤完成，继续下一步"
  ```

---

## Cookie

### cookie_set
- 语法：`cookie_set <name> <value>`
- 说明：设置 Cookie（需在某域名上下文下）
- 示例：
  ```text
  cookie_set token 123456
  ```

### cookies_set
- 语法：`cookie_set <value>`
- 说明：设置多个Cookie（需在某域名上下文下），格式为`name1:value1;name2:value2;......`
- 示例：
  ```text
  cookies_set name1:value1;name2:value2
  ```

### cookie_get
- 语法：`cookie_get <name>`
- 说明：打印指定 Cookie
- 示例：
  ```text
  cookie_get token
  ```

### cookie_delete
- 语法：`cookie_delete <name>`
- 说明：删除指定 Cookie
- 示例：
  ```text
  cookie_delete token
  ```

### cookie_clear
- 语法：`cookie_clear`
- 说明：清空所有 Cookie
- 示例：
  ```text
  cookie_clear
  ```

---

## 其他控制

### sleep
- 语法：`sleep <seconds>`
- 说明：线程休眠若干秒（整数）
- 示例：
  ```text
  sleep 2
  ```

### pause
- 语法：`pause`
- 说明：暂停执行，等待用户回车继续（无交互终端时自动跳过）
- 示例：
  ```text
  pause
  ```

### keep_open
- 语法：`keep_open`
- 说明：脚本结束后保持浏览器不关闭（按 Ctrl+C 退出或手动关闭）
- 示例：
  ```text
  keep_open
  ```

---

## BY 与选择器示例

- XPATH：`//input[@name='q']`、`//button[contains(.,'登录')]`
- CSS：`input[name="q"]`、`button.submit`、`#id .class`
- ID/NAME/CLASS/TAG：`ID login-btn`、`NAME username`、`CLASS item`、`TAG input`
- LINK/PLINK：`LINK "下载"`（全匹配）、`PLINK "下"`（包含）

建议优先选用稳定的定位（ID、data-* 属性、语义明确的 CSS），或者直接复制元素的完整Xpath。

---

## 常见问题与建议

- 点击失败请优先加入 `wait_clickable`；被遮挡可尝试 `scroll_into_view` 或 `click_js`
- iframe 内元素必须先 `frame`/`frame_index` 切换
- 异步加载用 `wait_*` 系列避免“找不到元素”
- headless 下窗口相关命令可能表现不同，可使用 `set_window 1920 1080`
- `upload` 仅适用于原生 `<input type="file">`，自定义组件需改用 `exec_js` 或触发原生输入框
