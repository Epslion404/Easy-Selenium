# Easy Selenium

[Gitee](https://gitee.com/Nept-Epslion/easy-selenium)

#### Introduction

Imperative Web Automation, evolved from a high school legacy project. Powered by GPT-5.

#### Software Architecture

Developed using Python 3.10.10.

#### Installation Guide

Download the latest release file.

#### Usage Instructions

1.  Extract the software package.
2.  Create a new command file (a simple text file `.txt` is sufficient) inside the `commands` folder.
3.  Navigate back to the parent folder and modify the `run.bat` file. Change `'cmd1.txt'` in `--commands .\command\cmd1.txt` to the name of the command file you just created.
4.  Customize other parameters as needed.
5.  Run `run.bat` and wait for the task to complete.

#### Contributing

1.  me
2.  GPT-5

#### Features

-   **Cross-Browser:** Supports Edge, Chrome, Firefox, including headless mode.
-   **Intuitive Commands:** Click, input, wait, scroll, frame/tab handling, dropdowns, upload, assertions, keyboard actions, JS execution, Cookie management.
-   **Quotes & Spaces:** Commands are parsed using `shlex`, supporting parameters with spaces and Chinese characters.
-   **Default Wait Timeout:** 15 seconds.

#### Command Syntax

##### Quick Guide

-   **Basic Element Operations**
    -   click/rclick/dclick: `click <BY> <selector>`
    -   hover: `hover <BY> <selector>`
    -   click_js: `click_js <BY> <selector>`
    -   write: `write <BY> <selector> "<text (can contain spaces)>"`
    -   clear: `clear <BY> <selector>`
    -   send_keys: `send_keys <BY> <selector> <keys...>`
    -   press: `press <keys...>` (sends to the currently focused element)
    -   Supported key names: `{ENTER} {TAB} {ESC} CTRL_A CTRL_C CTRL_V ...`; plain text can be quoted.
-   **Drag and Drop**
    -   drag_drop: `drag_drop <BY> <src_selector> <BY> <dst_selector>`
    -   drag_offset: `drag_offset <BY> <selector> <x> <y>`
-   **Navigation & Windows**
    -   goto/back/forward/refresh: `goto <url>`
    -   maximize/minimize/set_window: `set_window <width> <height>`
    -   window_latest/window_index/window_close: `window_index 1`
-   **Frame Handling**
    -   frame/frame_index/frame_parent/frame_default:
        -   `frame XPATH "//iframe[@id='f']"`
        -   `frame_index 0`
        -   `frame_parent`
        -   `frame_default`
-   **Explicit Waits**
    -   wait_present: `wait_present <BY> <selector> [timeout]`
    -   wait_visible: `wait_visible <BY> <selector> [timeout]`
    -   wait_clickable: `wait_clickable <BY> <selector> [timeout]`
    -   wait_invisible: `wait_invisible <BY> <selector> [timeout]`
    -   wait_text: `wait_text <BY> <selector> "<text>" [timeout]`
    -   wait_url_contains: `wait_url_contains "<substr>" [timeout]`
    -   wait_title_contains: `wait_title_contains "<substr>" [timeout]`
-   **Scrolling**
    -   scroll_into_view: `scroll_into_view <BY> <selector> [block]` (center|start|end)
    -   scroll_by: `scroll_by <x> <y>`
    -   scroll_top/scroll_bottom
-   **Dropdowns**
    -   select: `select <BY> <selector> (text|value|index) <value>`
-   **Upload/Screenshot/JS**
    -   upload: `upload <BY> <selector> "<file_path>"`
    -   screenshot: `screenshot "<file_path>"`
    -   screenshot_element: `screenshot_element <BY> <selector> "<file_path>"`
    -   exec_js: `exec_js "window.scrollTo(0,0)"`
-   **Assertions/Printing**
    -   assert_text: `assert_text <BY> <selector> "<expected_substr>"`
    -   assert_url_contains: `assert_url_contains "<substr>"`
    -   assert_title_contains: `assert_title_contains "<substr>"`
    -   print_text/print_attr: `print_text <BY> <selector>` / `print_attr <BY> <selector> <name>`
    -   echo: `echo "Message"`
-   **Cookies**
    -   cookie_set/cookies_set/cookie_get/cookie_delete/cookie_clear
-   **Others**
    -   sleep: `sleep <seconds>`
    -   pause: `pause`
    -   keep_open: `keep_open`
-   **BY Values**
    -   XPATH, CSS, ID, NAME, CLASS, TAG, LINK (exact link text), PLINK (partial link text)
-   **Legacy Command Aliases Supported**
    -   L_click/ R_click/ D_click/ put/ write/ jump/ delay/ pause/ keep_open
-   **Common Selector Examples**
    -   XPATH: `//input[@name="q"]`
    -   CSS: `input[name="q"]`
    -   LINK: `Login`, PLINK: `Log`

# Detailed Guide

## Basic Conventions

-   **Selector Locators (BY, case-insensitive)**
    -   XPATH, CSS, ID, NAME, CLASS, TAG, LINK (exact link text match), PLINK (partial link text match)
-   **Quotes and Spaces**
    -   Use quotes (`"..."` or `'...'`) to wrap parameters containing spaces or special characters.
-   **Keyboard Input**
    -   Special keys: Enclosed in curly braces, e.g., `{ENTER}`, `{TAB}`, `{ESC}`.
    -   Modifier key aliases: `CTRL_A`, `CTRL_C`, `CTRL_V`, ...; or `{CTRL} a`.
-   **Explicit Wait Timeout**
    -   `wait_*` commands without an explicit `timeout` parameter use the global default (CLI argument `--timeout`, default 15 seconds).
-   **Error Types (Common)**
    -   Element not found: Selector doesn't match or element isn't rendered yet.
    -   Invalid query expression: BY and selector mismatch or selector syntax error.
    -   Not interactable: Element not visible, obscured, or disabled.
    -   Insufficient parameters/format error: Missing command parameters or incorrect types.

Referenced articles:
[XPATH Tutorial](https://blog.csdn.net/weixin_43865008/article/details/115332404) (Tip: Right-click an element in Developer Tools (F12) to copy its full XPath.)
[CSS Selector Tutorial](https://blog.csdn.net/qq_45914609/article/details/142342792)

---

## Compatible Aliases

-   L_click → click
-   R_click → rclick
-   D_click → dclick
-   put → hover
-   jump → goto
-   delay → sleep
-   pause → pause
-   keep_open → keep_open

---

## Element Operations

### click
-   Syntax: `click <BY> <selector>`
-   Description: Performs a left-click on the target element.
-   Parameters:
    -   BY: Locator method (e.g., XPATH, CSS, ID, ...)
    -   selector: Selector string.
-   Common Errors: Element not found, not interactable, invalid query expression.
-   Example:
    ```text
    click CSS button.submit
    click XPATH "//button[@type='submit']"
    ```

### rclick
-   Syntax: `rclick <BY> <selector>`
-   Description: Right-clicks the element (context menu).
-   Parameters: Same as click.
-   Example:
    ```text
    rclick CSS .file-item
    ```

### dclick
-   Syntax: `dclick <BY> <selector>`
-   Description: Double-clicks the element.
-   Parameters: Same as click.
-   Example:
    ```text
    dclick PLINK "Details"
    ```

### hover
-   Syntax: `hover <BY> <selector>`
-   Description: Hovers the mouse over the element (triggers hover menus/tooltips).
-   Parameters: Same as click.
-   Example:
    ```text
    hover CSS .menu
    ```

### click_js
-   Syntax: `click_js <BY> <selector>`
-   Description: Triggers a click via JavaScript (bypasses occlusion/layout issues).
-   Parameters: Same as click.
-   Example:
    ```text
    click_js CSS .hidden-button
    ```

### clear
-   Syntax: `clear <BY> <selector>`
-   Description: Clears the content of an input field.
-   Parameters: Same as click.
-   Example:
    ```text
    clear NAME username
    ```

### write
-   Syntax: `write <BY> <selector> "<text>"`
-   Description: Clicks the input field and types the text; text can contain spaces.
-   Parameters:
    -   text: Input content, use quotes recommended.
-   Example:
    ```text
    write CSS input[name="q"] "keyword search"
    ```

### send_keys
-   Syntax: `send_keys <BY> <selector> <keys...>`
-   Description: Sends a sequence of keys to the element (can mix text and special/ modifier keys).
-   Parameters:
    -   keys: e.g., `"hello"`, `{ENTER}`, `CTRL_A`, `{CTRL} c`.
-   Example:
    ```text
    send_keys CSS input[name="q"] "hello world" {ENTER}
    send_keys CSS input[name="name"] CTRL_A "new name"
    ```

### press
-   Syntax: `press <keys...>`
-   Description: Sends the key sequence to the "currently focused element".
-   Example:
    ```text
    press {CTRL} "l"
    press CTRL_A {DELETE}
    ```

### drag_drop
-   Syntax: `drag_drop <BY> <src_selector> <BY> <dst_selector>`
-   Description: Drags the source element and drops it onto the target element.
-   Example:
    ```text
    drag_drop CSS .drag-src CSS .drop-zone
    ```

### drag_offset
-   Syntax: `drag_offset <BY> <selector> <x> <y>`
-   Description: Drags the element by an offset (pixels).
-   Parameters:
    -   x, y: Integers (can be negative).
-   Example:
    ```text
    drag_offset CSS .slider 80 0
    ```

---

## Navigation & Windows

### goto
-   Syntax: `goto <url>`
-   Description: Navigates to the specified URL.
-   Example:
    ```text
    goto https://example.com/login
    ```

### back / forward / refresh
-   Syntax: `back` / `forward` / `refresh`
-   Description: Browser back/forward/refresh.
-   Example:
    ```text
    back
    refresh
    ```

### maximize / minimize
-   Syntax: `maximize` / `minimize`
-   Description: Maximizes/Minimizes the browser window (may not work in headless mode for some browsers).
-   Example:
    ```text
    maximize
    ```

### set_window
-   Syntax: `set_window <width> <height>`
-   Description: Sets the window size (integer pixels).
-   Example:
    ```text
    set_window 1920 1080
    ```

---

## Frame Switching

### frame
-   Syntax: `frame <BY> <selector>`
-   Description: Switches to an iframe (located by element).
-   Example:
    ```text
    frame XPATH "//iframe[@id='content']"
    ```

### frame_index
-   Syntax: `frame_index <index>`
-   Description: Switches to a frame by its index (0-based).
-   Example:
    ```text
    frame_index 0
    ```

### frame_parent / frame_default
-   Syntax: `frame_parent` / `frame_default`
-   Description: Switches to the parent frame / returns to the default document context.
-   Example:
    ```text
    frame_parent
    frame_default
    ```

---

## Windows (Tabs)

### window_latest
-   Syntax: `window_latest`
-   Description: Switches to the most recently opened window/tab.
-   Example:
    ```text
    window_latest
    ```

### window_index
-   Syntax: `window_index <i>`
-   Description: Switches to a window by its index (0-based); throws an error for invalid indices.
-   Example:
    ```text
    window_index 1
    ```

### window_close
-   Syntax: `window_close`
-   Description: Closes the current window (you must manually switch to another window afterwards, if any remain).
-   Example:
    ```text
    window_close
    ```

---

## Explicit Waits (Recommended)

Note: Uses the global default timeout (CLI `--timeout`) if no `timeout` is provided.

### wait_present
-   Syntax: `wait_present <BY> <selector> [timeout]`
-   Description: Waits for the element to be present in the DOM (does not guarantee visibility/clickability).
-   Example:
    ```text
    wait_present CSS .list-item 10
    ```

### wait_visible
-   Syntax: `wait_visible <BY> <selector> [timeout]`
-   Description: Waits for the element to become visible.
-   Example:
    ```text
    wait_visible ID login-form 15
    ```

### wait_clickable
-   Syntax: `wait_clickable <BY> <selector> [timeout]`
-   Description: Waits for the element to be clickable (visible and enabled).
-   Example:
    ```text
    wait_clickable CSS button.submit 10
    ```

### wait_invisible
-   Syntax: `wait_invisible <BY> <selector> [timeout]`
-   Description: Waits for the element to become invisible or be removed from the DOM.
-   Example:
    ```text
    wait_invisible CSS .loading 20
    ```

### wait_text
-   Syntax: `wait_text <BY> <selector> "<text>" [timeout]`
-   Description: Waits for the element's text to contain the specified substring.
-   Example:
    ```text
    wait_text CSS .result "Success" 15
    ```

### wait_url_contains
-   Syntax: `wait_url_contains "<substr>" [timeout]`
-   Description: Waits for the current URL to contain the substring.
-   Example:
    ```text
    wait_url_contains "/dashboard" 10
    ```

### wait_title_contains
-   Syntax: `wait_title_contains "<substr>" [timeout]`
-   Description: Waits for the page title to contain the substring.
-   Example:
    ```text
    wait_title_contains "Dashboard"
    ```

---

## Scrolling

### scroll_into_view
-   Syntax: `scroll_into_view <BY> <selector> [block]`
-   Description: Scrolls the element into the viewport; `block` specifies alignment.
-   Parameters:
    -   block: `center` (default) | `start` | `end`
-   Example:
    ```text
    scroll_into_view CSS .footer start
    ```

### scroll_by
-   Syntax: `scroll_by <x> <y>`
-   Description: Scrolls the window by the specified offset (pixels, integers).
-   Example:
    ```text
    scroll_by 0 800
    ```

### scroll_top / scroll_bottom
-   Syntax: `scroll_top` / `scroll_bottom`
-   Description: Scrolls to the top/bottom of the page.
-   Example:
    ```text
    scroll_bottom
    ```

---

## Dropdown Selection

### select
-   Syntax: `select <BY> <selector> (text|value|index) <value>`
-   Description: Selects an option from a `<select>` element.
-   Parameters (Mode):
    -   text: By visible text.
    -   value: By value attribute.
    -   index: By index (integer, 0-based).
-   Example:
    ```text
    select ID city text "Shanghai"
    select NAME lang value "zh-CN"
    select CSS select#page index 2
    ```

---

## Upload / Screenshot / Execute JS

### upload
-   Syntax: `upload <BY> <selector> "<file_path>"`
-   Description: Inputs the file path into an `<input type="file">` element (must be accessible).
-   Note: The path is resolved to an absolute path; an error is thrown if the file doesn't exist.
-   Example:
    ```text
    upload CSS input[type="file"] "./data/upload.png"
    ```

### screenshot
-   Syntax: `screenshot "<file_path>"`
-   Description: Takes a full-page screenshot; parent directories are created automatically.
-   Example:
    ```text
    screenshot "./out/page.png"
    ```

### screenshot_element
-   Syntax: `screenshot_element <BY> <selector> "<file_path>"`
-   Description: Takes a screenshot of a specific element; parent directories are created automatically.
-   Example:
    ```text
    screenshot_element CSS .result "./out/result.png"
    ```

### exec_js
-   Syntax: `exec_js "<javascript code>"`
-   Description: Executes JavaScript directly in the page context (no return value handling).
-   Example:
    ```text
    exec_js "window.scrollTo(0,0)"
    exec_js "console.log('hello from automation')"
    ```

---

## Assertions & Output

### assert_text
-   Syntax: `assert_text <BY> <selector> "<expected_substr>"`
-   Description: Asserts that the element's text contains the substring; throws an error on failure.
-   Example:
    ```text
    assert_text CSS .toast "Operation successful"
    ```

### assert_url_contains
-   Syntax: `assert_url_contains "<substr>"`
-   Description: Asserts that the current URL contains the substring.
-   Example:
    ```text
    assert_url_contains "/dashboard"
    ```

### assert_title_contains
-   Syntax: `assert_title_contains "<substr>"`
-   Description: Asserts that the page title contains the substring.
-   Example:
    ```text
    assert_title_contains "Dashboard"
    ```

### print_text
-   Syntax: `print_text <BY> <selector>`
-   Description: Prints the element's text to the console.
-   Example:
    ```text
    print_text CSS .user-name
    ```

### print_attr
-   Syntax: `print_attr <BY> <selector> <name>`
-   Description: Prints the value of the specified element attribute to the console.
-   Example:
    ```text
    print_attr CSS a.download href
    ```

### echo
-   Syntax: `echo "<message>"`
-   Description: Outputs a message to the console.
-   Example:
    ```text
    echo "Step completed, proceeding to next"
    ```

---

## Cookies

### cookie_set
-   Syntax: `cookie_set <name> <value>`
-   Description: Sets a cookie (must be within a domain context).
-   Example:
    ```text
    cookie_set token 123456
    ```

### cookies_set
-   Syntax: `cookies_set <value>`
-   Description: Sets multiple cookies (must be within a domain context). Format: `name1:value1;name2:value2;......`
-   Example:
    ```text
    cookies_set name1:value1;name2:value2
    ```

### cookie_get
-   Syntax: `cookie_get <name>`
-   Description: Prints the specified cookie's value.
-   Example:
    ```text
    cookie_get token
    ```

### cookie_delete
-   Syntax: `cookie_delete <name>`
-   Description: Deletes the specified cookie.
-   Example:
    ```text
    cookie_delete token
    ```

### cookie_clear
-   Syntax: `cookie_clear`
-   Description: Clears all cookies.
-   Example:
    ```text
    cookie_clear
    ```

---

## Other Controls

### sleep
-   Syntax: `sleep <seconds>`
-   Description: Pauses execution for the specified number of seconds (integer).
-   Example:
    ```text
    sleep 2
    ```

### pause
-   Syntax: `pause`
-   Description: Pauses execution, waits for user to press Enter to continue (skipped automatically in non-interactive terminals).
-   Example:
    ```text
    pause
    ```

### keep_open
-   Syntax: `keep_open`
-   Description: Keeps the browser open after the script finishes (exit with Ctrl+C or close manually).
-   Example:
    ```text
    keep_open
    ```

---

## BY and Selector Examples

-   XPATH: `//input[@name='q']`, `//button[contains(.,'Login')]`
-   CSS: `input[name="q"]`, `button.submit`, `#id .class`
-   ID/NAME/CLASS/TAG: `ID login-btn`, `NAME username`, `CLASS item`, `TAG input`
-   LINK/PLINK: `LINK "Download"` (exact match), `PLINK "Down"` (partial match)

Prefer stable locators (ID, data-* attributes, semantic CSS). Alternatively, copy the element's full XPath directly.

---

## Common Issues & Suggestions

-   If clicks fail, first add a `wait_clickable`. For occluded elements, try `scroll_into_view` or `click_js`.
-   Elements inside iframes require switching via `frame`/`frame_index` first.
-   Use `wait_*` commands for async loading to avoid "element not found" errors.
-   Window-related commands may behave differently in headless mode; use `set_window 1920 1080`.
-   `upload` only works for native `<input type="file">` elements. For custom upload components, use `exec_js` or trigger the native input element.
