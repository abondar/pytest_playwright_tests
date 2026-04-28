from pathlib import Path
import allure
import pytest
from playwright.sync_api import expect, Browser
from slugify import slugify
from utils.get_user_data_from_file import get_all_users_data

# Temporary no-op change for git workflow verification.
DEFAULT_TIMEOUT = 5000


# Defines the browser configurations and emulations
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        }
    }


@pytest.fixture(scope="session", autouse=True)
def login(browser: Browser, browser_context_args):
    try:
        users_data = get_all_users_data()
        # Get all users information from fixtures/users.json with get_all_users_data()
        # Do login for any user in users.json file and save the state for contexts browsers
        for user_data in users_data:
            # Create context and page
            context = browser.new_context(**browser_context_args)
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            context.set_default_timeout(5000)
            page = context.new_page()
            # Get user and Password from fixtures/users.json
            user = user_data[1]['user']
            password = user_data[1]['password']

            # Go to log in page e do log in with user and password
            page.goto("https://www.saucedemo.com/")
            page.locator("[data-test=\"username\"]").fill(user)
            page.locator("[data-test=\"password\"]").fill(password)
            page.locator("[data-test=\"login-button\"]").click()
            logo = page.locator(".app_logo")

            # Verify if login has sucess and save de state file
            expect(logo).to_have_text("Swag Labs")
            context.storage_state(path=f'{user}' + "_state.json")
            context.close()
        # If login fails abort all tests e log the error
    except Exception as err:
        pytest.exit("Testes abortados, Erro ao tentar fazer login: " + f'{err}')


# Creates a context (browser instance) with Standard User logged
@pytest.fixture(scope="function")
def context_standard_user(browser: Browser, **browser_context_args):
    context = browser.new_context(storage_state="standard_user_state.json")
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    context.set_default_timeout(DEFAULT_TIMEOUT)
    yield context
    context.close()


# Creates a context (browser instance) with Problem User logged
@pytest.fixture(scope="function")
def context_problem_user(browser: Browser, browser_context_args):
    context = browser.new_context(storage_state="problem_user_state.json", **browser_context_args)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    context.set_default_timeout(DEFAULT_TIMEOUT)
    yield context
    context.close()


# Creates a clean context (browser instance) without user session
@pytest.fixture(scope="function")
def context_clean(browser: Browser, browser_context_args):
    context = browser.new_context(**browser_context_args)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    context.set_default_timeout(DEFAULT_TIMEOUT)
    yield context
    context.close()


# If any test fail, take a screenshot, save a trace file and attach to the report
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
