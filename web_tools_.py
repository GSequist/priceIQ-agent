from classes.browser_manager import BrowserManager
from classes.statemanager import local_state
from utils import sanitize_and_encode_image
from models_ import model_call
from typing import Any
import asyncio
import time

browser_manager = BrowserManager()


def web_search(query: str, filter_year: int = None, *, creds: Any, user_id: str) -> str:
    """search the web for information
    #parameters:
    query: a text query to search for in the web
    filter_year: OPTIONAL year filter (e.g., 2020)
    """
    max_tokens = 30000
    browser = browser_manager.get_browser(user_id)
    browser.visit_page(f"google: {query}", filter_year=None)
    header, content = browser._state()
    result = header.strip() + "\n=======================\n" + content
    return result, result, "", max_tokens


def visit_url(url: str, *, creds: Any, user_id: str) -> str:
    """Visit a webpage at a given URL and return its text. Given a url to a YouTube video, this returns the transcript. if you give this file url like "https://example.com/file.pdf", it will download that file and then you can use text_file tool on it.
    #parameters:
    url: the relative or absolute url of the webapge to visit
    """
    max_tokens = 30000
    browser = browser_manager.get_browser(user_id)
    browser.visit_page(url)
    header, content = browser._state()
    result = header.strip() + "\n=======================\n" + content
    return result, result, url, max_tokens


def page_up(creds: Any, user_id: str) -> str:
    """Scroll up one page."""
    max_tokens = 30000
    browser = browser_manager.get_browser(user_id)
    browser.page_up()
    header, content = browser._state()
    result = header.strip() + "\n=======================\n" + content
    return result, result, "", max_tokens


def page_down(creds: Any, user_id: str) -> str:
    """Scroll down one page."""
    max_tokens = 30000
    browser = browser_manager.get_browser(user_id)
    browser.page_down()
    header, content = browser._state()
    result = header.strip() + "\n=======================\n" + content
    return result, result, "", max_tokens


def find_on_page(search_string: str, *, creds: Any, user_id: str) -> str:
    """Scroll the viewport to the first occurrence of the search string. This is equivalent to Ctrl+F.
    #parameters:
    search_string: The string to search for; supports wildcards like '*'
    """
    max_tokens = 30000
    browser = browser_manager.get_browser(user_id)
    result = browser.find_on_page(search_string)
    header, content = browser._state()
    if result is None:
        return (
            (
                header.strip()
                + f"\n=======================\nThe search string '{search_string}' was not found on this page."
            ),
            "",
            "",
            5000,
        )
    end_result = header.strip() + "\n=======================\n" + content
    return end_result, end_result, "", max_tokens


def find_next(creds: Any, user_id: str) -> str:
    max_tokens = 30000
    browser = browser_manager.get_browser(user_id)
    result = browser.find_next()
    header, content = browser._state()
    if result is None:
        return (
            (
                header.strip()
                + "\n=======================\nNo further occurrences found."
            ),
            "",
            "",
            max_tokens,
        )
    end_result = header.strip() + "\n=======================\n" + content
    return (
        end_result,
        end_result,
        "",
        max_tokens,
    )


async def screenshot(url: str, query: str, *, creds: Any, user_id: str, stream_id: str):
    """Take a screenshot of a given url.
    #parameters:
    url: url of the web to take screenshot of
    query: what are you looking for in the screenshot
    """
    max_tokens = 30000
    browser = browser_manager.get_browser(user_id)
    img_path = browser.screenshot(url)
    try:
        encoded_string = sanitize_and_encode_image(img_path)
        model_task = asyncio.create_task(
            model_call(
                input=query,
                encoded_image=encoded_string,
                client_timeout=240,
            )
        )
        percentage = 10
        start_time = time.time()
        timeout = 240
        delay_between_updates = 5

        while not model_task.done():
            yield {
                "type": "tool_progress",
                "toolName": "screenshot",
                "progress": f"◈ vision model working on the screenshot... ◈ ({percentage}%)",
                "percentage": percentage,
                "stream_id": stream_id,
            }

            if not local_state.get_state(user_id):
                model_task.cancel()
                yield {
                    "type": "endOfMessage",
                    "sources": [],
                    "stream_id": stream_id,
                }
                return

            await asyncio.sleep(delay_between_updates)

            if time.time() - start_time > timeout:
                model_task.cancel()
                yield {
                    "type": "tool_result",
                    "toolName": "screenshot",
                    "result": f"Screenshot model timed out after 3 minutes",
                    "content": f"Screenshot model timed out after 3 minutes",
                    "sources": "",
                    "tokens": max_tokens,
                    "stream_id": stream_id,
                }
                return

            if percentage >= 90:
                percentage = 50
            else:
                percentage = min(percentage + 10, 90)
        response = await model_task
        vision_result = response.output_text
        yield {
            "type": "tool_result",
            "toolName": "screenshot",
            "result": f"Screenshot model analysis completed:\n {vision_result}",
            "content": vision_result,
            "sources": "",
            "tokens": max_tokens,
            "stream_id": stream_id,
        }
    except Exception as e:
        yield {
            "type": "tool_result",
            "toolName": "screenshot",
            "result": f"Error processing image: {str(e)}",
            "content": f"Error processing image: {str(e)}",
            "sources": "",
            "tokens": max_tokens,
            "stream_id": stream_id,
        }
