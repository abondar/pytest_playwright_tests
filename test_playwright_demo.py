import json

from playwright.sync_api import expect
from operator import itemgetter

# Temporary no-op change for git workflow verification.

class TestPlaywrightDemo:

    # This test validate in two different browsers if the store page opens correctly,
    # demonstrating use of authenticate state, the multi-context and multi-page features
    def test_with_multiple_context_and_pages_authenticated(self, context_problem_user, context_standard_user):
        self.page_one = context_standard_user.new_page()
        self.page_one.goto("https://www.saucedemo.com/inventory.html")
        self.logo_one = self.page_one.locator(".app_logo")
        self.page_two = context_problem_user.new_page()
        self.page_two.goto("https://www.saucedemo.com/inventory.html")
        self.logo_two = self.page_two.locator(".app_logo")
        expect(self.logo_one).to_have_text("Swag Labs")
        expect(self.logo_two).to_have_text("Swag Labs")

    # This test will fail to demonstrate the screenshot and trace file attached to the report
    def test_fail_for_save_screenshot_and_trace(self, context_standard_user):
        self.page = context_standard_user.new_page()
        self.page.goto("https://www.saucedemo.com/inventory.html")
        self.logo = self.page.locator(".app_logo")
        expect(self.logo).to_have_text("Swag Lab")

    # This test validates whether it is possible to add a product to the cart successfully
    def test_add_product_backpack(self, context_standard_user):
        self.page = context_standard_user.new_page()
        self.page.goto("https://www.saucedemo.com/inventory.html")
        self.add_to_cart_backpack_button = self.page.locator("#add-to-cart-sauce-labs-backpack")
        self.add_to_cart_backpack_button.click()
        self.shop_cart_button = self.page.locator(".shopping_cart_link")
        self.shop_cart_button.click()
        self.cart_container = self.page.locator(".cart_contents_container")
        expect(self.cart_container).to_contain_text("Sauce Labs Backpack")

    # This test validates whether the cart badge is updated when one product is added
    def test_add_product_backpack_updates_cart_badge(self, context_standard_user):
        self.page = context_standard_user.new_page()
        self.page.goto("https://www.saucedemo.com/inventory.html")
        self.add_to_cart_backpack_button = self.page.locator("#add-to-cart-sauce-labs-backpack")
        self.add_to_cart_backpack_button.click()
        self.shopping_cart_badge = self.page.locator(".shopping_cart_badge")
        expect(self.shopping_cart_badge).to_have_text("1")

    # This one demonstrates the use of interception of page requests (Network events) for backend validation
    def test_api_intercept(self, context_clean):
        self.page = context_clean.new_page()
        with self.page.expect_response("**/api/books") as response_info:
            self.page.goto("https://danube-web.shop/")
            self.response_body = json.loads(response_info.value.body())
            self.titles = list(map(itemgetter('title'), self.response_body))
            assert 'Haben oder haben' in self.titles

    # This test demonstrates the mock functionality that allows changing the api response and the page and verify
    # if it has just two products and their names
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
            },
            {
                "id": 2,
                "title": "Parry Hotter",
                "author": "J/K Rowlin'",
                "genre": "erotic",
                "price": "9.95",
                "rating": "★★★☆☆",
                "stock": "1"
            }
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
