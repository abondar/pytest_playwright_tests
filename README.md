# Playwright Python demo tests

This project demonstrates some Playwright features for end-to-end test automation using Python and Pytest.

The test code is intentionally simple. For that reason, it does not use Page Objects or other abstraction patterns — the goal is to showcase the project configuration and some core Playwright capabilities.

This project includes:

- Frameworks:
    - Pytest
    - Allure
    - Playwright


- Features:
    - Tests with multiple browser contexts and pages
    - Authenticated test sessions with saved storage states
    - Shopping cart badge validation after adding a product
    - Intercepting page requests (network events)
    - Mocking page requests
    - Screenshot capture on failure with report attachment
    - Trace file generation on failure with report attachment
    - Trace-based debugging for failed tests
    - Interactive debugging with Playwright Inspector
    - Pytest fixture-based configuration
    - Allure reporting

## Demo Pages
These tests use two demo applications:
- [Sauce Demo](https://www.saucedemo.com/)
- [Danube Shop](https://danube-web.shop/)

## Requirements
- uv - [How to install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Allure Client >= 2.21 [How install allure client](https://docs.qameta.io/allure/#_commandline)

The project is configured for Python 3.11 via `.python-version`. Dependencies are managed in `pyproject.toml`, and `uv.lock` keeps installs reproducible.

## Getting Started
Install dependencies and Playwright browsers:

```bash
$ make install
```

If you prefer the raw uv commands:

```bash
$ uv python install 3.11
$ uv lock
$ uv sync --python 3.11
$ uv run playwright install
```

## To run all tests
```bash
$ make test
```

## To run the test file with verbose output
```bash
$ make test-file
```

## To run tests in Chrome (for headless mode remove --headed parameter)
```bash
$ make test-headed
```

## To run tests in Firefox Browser (for headless mode remove --headed parameter):
```bash
$ make test-firefox
```

## To run tests with slo-mo mode
```bash
$ make test-slowmo
```

![Test Execution](img/test_execution.gif)

## Tests with multiple browser instances (contexts) and multiple pages
With Playwright, all tests are isolated through browser contexts and pages. In this project, browser contexts are defined as fixtures in `conftest.py`, where you can also update existing contexts or create new ones.

> IMPORTANT: Any context created must start with the prefix `context_`. Otherwise, screenshots and trace files will not be saved automatically when a test fails.

> Inside `conftest.py`, the `login` fixture authenticates the users from `fixtures/users.json` and saves an authenticated storage state file for each one.

> If login fails, the test suite is aborted.

Example of context as fixture using saved authenticated state for user Standard:

```python
# conftest.py
from playwright.sync_api import Browser
import pytest

DEFAULT_TIMEOUT = 5000

@pytest.fixture(scope="function")
def context_standard_user(browser: Browser, **browser_context_args):
    context = browser.new_context(storage_state="standard_user_state.json")
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    context.set_default_timeout(DEFAULT_TIMEOUT)
    yield context
    context.close()
```

Example of test with multiple contexts and pages:
```python
#test_playwright_demo.py

from playwright.sync_api import expect

def test_with_multiple_context_and_pages_authenticated(self, context_problem_user, context_standard_user):
      self.page_one = context_standard_user.new_page()
      self.page_one.goto("https://www.saucedemo.com/inventory.html")
      self.logo_one = self.page_one.locator(".app_logo")
      self.page_two = context_problem_user.new_page()
      self.page_two.goto("https://www.saucedemo.com/inventory.html")
      self.logo_two = self.page_two.locator(".app_logo")
      expect(self.logo_one).to_have_text("Swag Labs")
      expect(self.logo_two).to_have_text("Swag Labs")
```

## Validate shopping cart badge updates
This example validates an edge case on Sauce Demo: after adding a single product, the shopping cart badge must show the correct quantity.

```Python
# test_playwright_demo.py

from playwright.sync_api import expect

def test_add_product_backpack_updates_cart_badge(self, context_standard_user):
    self.page = context_standard_user.new_page()
    self.page.goto("https://www.saucedemo.com/inventory.html")
    self.add_to_cart_backpack_button = self.page.locator("#add-to-cart-sauce-labs-backpack")
    self.add_to_cart_backpack_button.click()
    self.shopping_cart_badge = self.page.locator(".shopping_cart_badge")
    expect(self.shopping_cart_badge).to_have_text("1")
```

## Intercepting page requests (Network Events)
Playwright provides APIs to monitor and modify network traffic, both HTTP and HTTPS. Any requests that a page does, 
including XHRs and fetch requests, can be tracked, modified and handled.

In the example below I demonstrate a test that intercepts the http request from the api, collects the titles of the 
books and verifies if there is any book with the title Haben oder haben

```Python
# test_playwright_demo.py

import json
from operator import itemgetter

def test_api_intercept(self, context_clean):
    self.page = context_clean.new_page()
    with self.page.expect_response("**/api/books") as response_info:
        self.page.goto("https://danube-web.shop/")
        self.response_body = json.loads(response_info.value.body())
        self.titles = list(map(itemgetter('title'), self.response_body))
        assert 'Haben oder haben' in self.titles
```
## Mock page requests
With playwright, it is possible to mock requests (network events), thus modifying the behavior and content of a 
page in real time


In this example, the books endpoint of the api is mocked, where only two items are informed, 
the quantity and titles are validated

```Python
# test_playwright_demo.py

import json

def test_mock_api(self, context_clean):
  
    # New API response
    request_body = [
        {
            "id": 1,
            "title": "Haben oder haben",
            "author": "Fric Eromm",
            "genre": "philosophy",
            "price": "9.95",
            "rating": "★★★★☆",
            "stock": "1"
        }, ...
    ]
    
    self.page = context_clean.new_page()
    # Intercept and change Api response with new body
    self.page.route(
        "**/api/books",
        lambda route: route.fulfill(
            content_type='application/json',
            status=200,
            body=json.dumps(request_body)
        )
    )
    # Wait for page load
    self.page.wait_for_load_state('networkidle')
    self.page.goto("https://danube-web.shop/")
    self.products_container = self.page.query_selector(".shop-content")
    self.products_name = self.products_container.text_content()
    self.number_of_products = len(self.products_container.query_selector_all('li'))
    assert "Haben oder haben" and "Parry Hotter" in self.products_name
    assert self.number_of_products == 2
```
- Before api mock:

![Before Mock](img/before_mock.png)


- After api mock:

![After Mock](img/after_mock.png)

## Interactive Debug
Set the `PWDEBUG` environment variable to run your Playwright tests in debug mode, or add `page.pause()` in the test code.
This configures Playwright for debugging and opens the inspector.
When the test reaches `page.pause()`, execution is paused so you can inspect the current state interactively.

For debug a specific test scenario:
```bash
$ make debug
```

Equivalent uv command:
```bash
$ PWDEBUG=1 uv run pytest --browser chromium test_playwright_demo.py::TestPlaywrightDemo::test_add_product_backpack
```

```Python
# test_playwright_demo.py

import json
from operator import itemgetter

def test_api_intercept(self, context_clean):
    self.page = context_clean.new_page()
    with self.page.expect_response("**/api/books") as response_info:
        self.page.goto("https://danube-web.shop/")
        self.response_body = json.loads(response_info.value.body())
        self.titles = list(map(itemgetter('title'), self.response_body))
        assert 'Haben oder haben' in self.titles
```

![Interactive debug](img/interactive_debug.gif)

## Trace viewer
If any test fails, the trace file is attached to the report. To inspect and debug it, run the following command:

```bash
$ uv run playwright show-trace FILE-NAME.ZIP
```
![Trace](img/trace_viewer.gif)

Get the trace file from failed test:

![Trace_viewer](img/trace.png)

## Automatic save screenshot and trace file if test fail

In the conftest.py file there is the function pytest_runtest_makereport, every time a test is executed this function 
is called, and if the test fails it will interact in all browsers and pages, will take the screenshot, save the trace file and attach it in the execution report
>Important, every new context must be created as a fixture with the name context_, if the context is created in another 
> way, then the screenshot and the trace file will not be saved.

> Trace file is saved on traces folder
```python
# conftest.py

import pytest
from slugify import slugify
from pathlib import Path

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.failed and rep.when != 'setup':
        traces_dir = Path("traces")
        trace_file = str(traces_dir / f"{slugify(item.nodeid)}.zip")
        partial_context_name = 'context_'
        # Iterate on items to get the actual context
        context = next(
            (value for key, value in item.funcargs.items()
             if key.lower().startswith(partial_context_name)),
            None
        )
        if context:
            # Generate page trace, take screenshot and attach to report
            context.tracing.stop(path=trace_file)
            try:
                # Get each page and take a screenshot
                for page in context.pages:
                    allure.attach(
                        page.screenshot(),
                        name='screenshot' + f'{page.url}',
                        attachment_type=allure.attachment_type.PNG
                    )
                allure.attach.file(
                    trace_file,
                    name='trace',
                    extension="zip"
                )
            except Exception as e:
                print('Fail to take screen-shot: {}'.format(e))
        else:
            pass
```

## Reports
> You must have the allure client installed

Run the command below to generate the test report:

```bash
$ make allure-generate
```

To view the report in the browser:

```bash
$ make allure-open
```
