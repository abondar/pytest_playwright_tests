UV ?= uv
PYTHON_VERSION ?= 3.11

.PHONY: python lock sync browser-install install test test-file test-headed test-firefox test-slowmo debug allure-generate allure-open

python:
	$(UV) python install $(PYTHON_VERSION)

lock: python
	$(UV) lock

sync: lock
	$(UV) sync --python $(PYTHON_VERSION)

browser-install: sync
	$(UV) run playwright install

install: browser-install

test:
	$(UV) run pytest test_playwright_demo.py

test-file:
	$(UV) run pytest -v test_playwright_demo.py

test-headed:
	$(UV) run pytest -vv --headed --browser chromium --alluredir=results/allure_report

test-firefox:
	$(UV) run pytest -vv --headed --browser firefox --alluredir=results/allure_report

test-slowmo:
	$(UV) run pytest -vv --headed --browser chrome --slowmo 500 --alluredir=results/allure_report

debug:
	PWDEBUG=1 $(UV) run pytest --browser chromium test_playwright_demo.py::TestPlaywrightDemo::test_add_product_backpack

allure-generate:
	allure generate --clean results/allure_report -o results/allure_result

allure-open:
	allure open results/allure_result
