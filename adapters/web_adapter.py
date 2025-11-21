"""Web application adapter using Playwright."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

try:
    from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
except ImportError:
    sync_playwright = None
    Page = None
    Browser = None
    PlaywrightTimeout = None

from adapters.base_adapter import BaseApplicationAdapter, Element, DiscoveryResult
from models.test_case import TestCase, TestStep
from models.test_result import TestResult, TestStatus, TestMetrics
from utils.logger import get_logger
from utils.helpers import generate_result_id, sanitize_filename

logger = get_logger(__name__)


class WebAdapter(BaseApplicationAdapter):
    """Adapter for web applications using Playwright."""

    def __init__(self, app_profile):
        """Initialize web adapter."""
        super().__init__(app_profile)

        if sync_playwright is None:
            raise ImportError(
                "Playwright is required for WebAdapter. "
                "Install with: pip install playwright && playwright install"
            )

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.visited_urls = set()

    def _start_browser(self) -> None:
        """Start Playwright browser."""
        if self.playwright is None:
            self.playwright = sync_playwright().start()

        browser_type = self.playwright.chromium  # Can be configurable

        self.browser = browser_type.launch(
            headless=self.app_profile.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.page = context.new_page()
        self.page.set_default_timeout(30000)  # 30 seconds

        logger.info(f"Browser started for {self.name}")

    def authenticate(self) -> bool:
        """Authenticate with the web application."""
        try:
            auth = self.app_profile.auth

            if auth.auth_type == "none":
                return True

            if not self.page:
                self._start_browser()

            # Navigate to base URL
            self.page.goto(self.app_profile.base_url)

            if auth.auth_type == "basic":
                # Handle basic auth in URL or login form
                if auth.username and auth.password:
                    # Try to find and fill login form
                    username_input = self.page.query_selector('input[type="text"], input[name*="user"], input[id*="user"]')
                    password_input = self.page.query_selector('input[type="password"]')

                    if username_input and password_input:
                        username_input.fill(auth.username)
                        password_input.fill(auth.password)

                        # Find and click submit button
                        submit_button = self.page.query_selector('button[type="submit"], input[type="submit"]')
                        if submit_button:
                            submit_button.click()
                            self.page.wait_for_load_state("networkidle")

            logger.info(f"Authentication successful for {self.name}")
            return True

        except Exception as e:
            logger.error(f"Authentication failed for {self.name}: {e}")
            return False

    def discover_elements(self) -> DiscoveryResult:
        """Discover UI elements by crawling the web application."""
        logger.info(f"Starting discovery for {self.name}")

        if not self.page:
            self._start_browser()
            self.authenticate()

        result = DiscoveryResult()
        config = self.app_profile.discovery

        if not config.enabled:
            logger.info("Discovery disabled in configuration")
            return result

        # Start crawling from base URL
        self._crawl_page(config.url or self.app_profile.base_url, result, depth=0)

        logger.info(
            f"Discovery complete: {len(result.elements)} elements, "
            f"{len(result.pages)} pages"
        )

        return result

    def _crawl_page(self, url: str, result: DiscoveryResult, depth: int) -> None:
        """Recursively crawl pages and discover elements."""
        config = self.app_profile.discovery

        if depth > config.max_depth:
            return

        if url in self.visited_urls:
            return

        if len(result.pages) >= config.max_pages:
            return

        # Check URL filters
        if not self._should_crawl_url(url):
            return

        try:
            logger.debug(f"Crawling: {url} (depth: {depth})")
            self.page.goto(url, wait_until="networkidle")
            self.visited_urls.add(url)
            result.pages.append(url)

            # Discover elements on this page
            page_elements = self._discover_page_elements(url)
            result.elements.extend(page_elements)

            # Find links for further crawling
            if depth < config.max_depth:
                links = self.page.query_selector_all("a[href]")
                for link in links[:20]:  # Limit links per page
                    href = link.get_attribute("href")
                    if href:
                        absolute_url = urljoin(url, href)
                        if self._is_same_domain(absolute_url):
                            self._crawl_page(absolute_url, result, depth + 1)

        except Exception as e:
            logger.warning(f"Error crawling {url}: {e}")

    def _discover_page_elements(self, page_url: str) -> List[Element]:
        """Discover elements on current page."""
        elements = []
        discover_types = self.app_profile.discovery.discover_elements

        # Discover buttons
        if "buttons" in discover_types or "all" in discover_types:
            buttons = self.page.query_selector_all("button, input[type='button'], input[type='submit']")
            for idx, btn in enumerate(buttons):
                elements.append(self._create_element(btn, "button", idx, page_url))

        # Discover inputs
        if "inputs" in discover_types or "all" in discover_types:
            inputs = self.page.query_selector_all("input, textarea, select")
            for idx, inp in enumerate(inputs):
                input_type = inp.get_attribute("type") or "text"
                elements.append(self._create_element(inp, f"input_{input_type}", idx, page_url))

        # Discover forms
        if "forms" in discover_types or "all" in discover_types:
            forms = self.page.query_selector_all("form")
            for idx, form in enumerate(forms):
                elements.append(self._create_element(form, "form", idx, page_url))

        # Discover links
        if "links" in discover_types or "all" in discover_types:
            links = self.page.query_selector_all("a[href]")
            for idx, link in enumerate(links):
                elements.append(self._create_element(link, "link", idx, page_url))

        return elements

    def _create_element(self, locator, element_type: str, index: int, page_url: str) -> Element:
        """Create Element object from Playwright locator."""
        element_id = f"{element_type}_{index}_{sanitize_filename(page_url)}"

        try:
            name = (
                locator.get_attribute("name") or
                locator.get_attribute("id") or
                locator.get_attribute("aria-label") or
                locator.inner_text()[:50] if hasattr(locator, "inner_text") else
                f"{element_type}_{index}"
            )
        except:
            name = f"{element_type}_{index}"

        attributes = {}
        for attr in ["id", "name", "class", "type", "href", "placeholder", "value"]:
            try:
                val = locator.get_attribute(attr)
                if val:
                    attributes[attr] = val
            except:
                pass

        # Generate selector
        selector = self._generate_selector(locator, attributes)

        return Element(
            id=element_id,
            type=element_type,
            name=name,
            selector=selector,
            attributes=attributes,
            page_url=page_url
        )

    def _generate_selector(self, locator, attributes: Dict) -> str:
        """Generate CSS selector for element."""
        if attributes.get("id"):
            return f"#{attributes['id']}"
        elif attributes.get("name"):
            return f"[name='{attributes['name']}']"
        elif attributes.get("class"):
            classes = attributes['class'].split()
            if classes:
                return f".{classes[0]}"
        return locator.evaluate("el => el.tagName.toLowerCase()")

    def _should_crawl_url(self, url: str) -> bool:
        """Check if URL should be crawled based on filters."""
        config = self.app_profile.discovery

        # Check exclude patterns
        for pattern in config.exclude_patterns:
            if pattern in url:
                return False

        # Check include patterns (if specified)
        if config.include_patterns:
            for pattern in config.include_patterns:
                if pattern in url:
                    return True
            return False

        return True

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is from the same domain."""
        base_domain = urlparse(self.app_profile.base_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain == url_domain

    def execute_test(self, test_case: TestCase) -> TestResult:
        """Execute a test case."""
        logger.info(f"Executing test: {test_case.name}")

        start_time = datetime.utcnow()

        if not self.page:
            self._start_browser()
            self.authenticate()

        result = TestResult(
            id=generate_result_id(),
            test_case_id=test_case.id,
            test_name=test_case.name,
            status=TestStatus.RUNNING,
            metrics=TestMetrics(
                duration_seconds=0,
                start_time=start_time,
                end_time=start_time
            )
        )

        try:
            # Execute each test step
            for step in test_case.steps:
                step_result = self._execute_step(step, test_case)
                result.add_step_result(
                    step_number=step.step_number,
                    status=step_result["status"],
                    actual_result=step_result["actual"],
                    duration_seconds=step_result["duration"],
                    screenshot_path=step_result.get("screenshot")
                )

                if step_result["status"] == TestStatus.FAILED:
                    result.status = TestStatus.FAILED
                    result.error_message = step_result.get("error")
                    break

            # If all steps passed
            if result.status == TestStatus.RUNNING:
                result.status = TestStatus.PASSED

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            result.status = TestStatus.ERROR
            result.error_message = str(e)

        end_time = datetime.utcnow()
        result.metrics.end_time = end_time
        result.metrics.duration_seconds = (end_time - start_time).total_seconds()

        logger.info(f"Test {test_case.name} completed: {result.status}")
        return result

    def _execute_step(self, step: TestStep, test_case: TestCase) -> Dict[str, Any]:
        """Execute a single test step."""
        step_start = datetime.utcnow()

        try:
            action = step.action.lower()

            if action == "navigate":
                url = step.target if step.target.startswith("http") else urljoin(self.app_profile.base_url, step.target)
                self.page.goto(url)
                actual = f"Navigated to {url}"

            elif action == "click":
                self.page.click(step.target)
                actual = f"Clicked {step.target}"

            elif action == "fill" or action == "type":
                value = step.input_data.get("value", "") if step.input_data else ""
                self.page.fill(step.target, value)
                actual = f"Filled {step.target} with value"

            elif action == "wait":
                timeout = step.input_data.get("timeout", 5000) if step.input_data else 5000
                self.page.wait_for_timeout(timeout)
                actual = f"Waited {timeout}ms"

            elif action == "assert" or action == "verify":
                element = self.page.query_selector(step.target)
                if not element:
                    raise AssertionError(f"Element not found: {step.target}")
                actual = f"Element {step.target} found"

            else:
                actual = f"Unknown action: {action}"

            duration = (datetime.utcnow() - step_start).total_seconds()

            screenshot = None
            if step.screenshot:
                screenshot = self.take_screenshot(f"step_{step.step_number}")

            return {
                "status": TestStatus.PASSED,
                "actual": actual,
                "duration": duration,
                "screenshot": screenshot
            }

        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            return {
                "status": TestStatus.FAILED,
                "actual": f"Step failed: {str(e)}",
                "error": str(e),
                "duration": duration
            }

    def validate_state(self) -> bool:
        """Validate application is accessible."""
        try:
            if not self.page:
                self._start_browser()

            self.page.goto(self.app_profile.base_url, timeout=15000)
            return True
        except Exception as e:
            logger.error(f"State validation failed: {e}")
            return False

    def take_screenshot(self, filename: str) -> Optional[str]:
        """Take screenshot."""
        try:
            if not self.page:
                return None

            screenshots_dir = Path("screenshots") / self.name
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = screenshots_dir / f"{sanitize_filename(filename)}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"

            self.page.screenshot(path=str(screenshot_path), full_page=True)

            logger.debug(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    def cleanup(self) -> None:
        """Clean up browser resources."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            logger.info(f"Cleanup complete for {self.name}")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def get_capabilities(self) -> Dict[str, bool]:
        """Get adapter capabilities."""
        return {
            "ui_testing": True,
            "api_testing": False,
            "database_testing": False,
            "screenshot_capture": True,
            "video_recording": True,
            "log_capture": True,
        }
