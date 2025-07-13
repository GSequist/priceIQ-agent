from classes.keyboardmanager import keyboard_listener
from classes.statemanager import local_state
from utils import ensure_user_workspace
from schema import function_to_schema
from typing import Any, Dict, List
from models_ import model_call
from web_tools_ import (
    visit_url,
    web_search,
    find_on_page,
    find_next,
    page_down,
    page_up,
    screenshot,
)
import asyncio
import json
import os


def _get_tool_schemas() -> List[Dict[str, Any]]:
    """Convert selected tools into OpenAI function-schemas."""
    return [
        function_to_schema(web_search),
        function_to_schema(visit_url),
        function_to_schema(find_on_page),
        function_to_schema(find_next),
        function_to_schema(page_down),
        function_to_schema(page_up),
        function_to_schema(screenshot),
    ]


async def _execute_tool_call(
    tool_call: Dict[str, Any], *, creds: Any, user_id: str, stream_id: str
):
    """
    Runs the requested tool and yields progress updates and final results.
    """
    name = tool_call.name
    raw_args = tool_call.arguments
    try:
        args: Dict[str, Any] = json.loads(raw_args)
    except Exception:
        args = {}

    try:
        if name == "screenshot":
            async for update in screenshot(
                **args, creds=creds, user_id=user_id, stream_id=stream_id
            ):
                if update.get("type") == "tool_result":
                    content = update["content"]
                    truncated_content = (
                        content[:100] + "..." if len(content) > 100 else content
                    )
                    yield {
                        "type": "tool_progress",
                        "toolName": name,
                        "progress": f"◈ Screenshot Analysis Complete ◈\n▸ {truncated_content}",
                        "stream_id": stream_id,
                    }
                    yield {"type": "tool_result", "content": content}
                elif update.get("type") == "endOfMessage":
                    yield update
                    return
                elif update.get("type") == "tool_progress":
                    yield update
            return

        elif name == "web_search":
            text, *_ = web_search(**args, creds=creds, user_id=user_id)
            truncated_content = text[:100] + "..." if len(text) > 100 else text
            yield {
                "type": "tool_progress",
                "toolName": name,
                "progress": f"◈ Web Search Complete ◈\n▸ {truncated_content}",
                "stream_id": stream_id,
            }
            yield {"type": "tool_result", "content": text}

        elif name == "visit_url":
            text, *_ = visit_url(**args, creds=creds, user_id=user_id)
            truncated_content = text[:100] + "..." if len(text) > 100 else text
            yield {
                "type": "tool_progress",
                "toolName": name,
                "progress": f"◈ Page Visit Complete ◈\n▸ {truncated_content}",
                "stream_id": stream_id,
            }
            yield {"type": "tool_result", "content": text}

        elif name == "find_on_page":
            text, *_ = find_on_page(**args, creds=creds, user_id=user_id)
            truncated_content = text[:100] + "..." if len(text) > 100 else text
            yield {
                "type": "tool_progress",
                "toolName": name,
                "progress": f"◈ Content Search Complete ◈\n▸ {truncated_content}",
                "stream_id": stream_id,
            }
            yield {"type": "tool_result", "content": text}

        elif name == "find_next":
            text, *_ = find_next(**args, creds=creds, user_id=user_id)
            truncated_content = text[:100] + "..." if len(text) > 100 else text
            yield {
                "type": "tool_progress",
                "toolName": name,
                "progress": f"◈ Search Continue Complete ◈\n▸ {truncated_content}",
                "stream_id": stream_id,
            }
            yield {"type": "tool_result", "content": text}

        elif name == "page_down":
            text, *_ = page_down(**args, creds=creds, user_id=user_id)
            truncated_content = text[:100] + "..." if len(text) > 100 else text
            yield {
                "type": "tool_progress",
                "toolName": name,
                "progress": f"◈ Page Down Complete ◈\n▸ {truncated_content}",
                "stream_id": stream_id,
            }
            yield {"type": "tool_result", "content": text}

        elif name == "page_up":
            text, *_ = page_up(**args, creds=creds, user_id=user_id)
            truncated_content = text[:100] + "..." if len(text) > 100 else text
            yield {
                "type": "tool_progress",
                "toolName": name,
                "progress": f"◈ Page Up Complete ◈\n▸ {truncated_content}",
                "stream_id": stream_id,
            }
            yield {"type": "tool_result", "content": text}

        else:
            yield {"type": "tool_result", "content": f"Unknown tool {name}"}

    except Exception as e:
        yield {
            "type": "tool_progress",
            "toolName": name,
            "progress": f"◈ Tool Error ◈\n▸ {str(e)[:100]}",
            "stream_id": stream_id,
        }
        yield {"type": "tool_result", "content": f"Error executing {name}: {e}"}


def _build_system_prompt(product: str, sites: List[str]) -> str:
    sites_str = "\n".join(f"• {s}" for s in sites)
    return f"""You are an expert e-commerce research agent.

Goal: For every site below, find the exact product page for
    '{product}'
and extract:
  – price (with currency)  
  – availability (e.g. 'in-stock', 'sold out')  
  – url (the exact url of the product page)
  – notes (any additional notes about your research)

The sites are:
{sites_str}

Return one JSON object ONLY, exactly:

Rules:
- Start with web_search and look for the product across the sites. Use one web search at a time, then wait to get results then go on. For filter_year leave blank.
- The product name may be different across different sites, try to broaden it.
- Experiment also with searching for the product category and then filtering for the specific product.
- Once you have a candidate URL, call visit_url to read the page to get the details. 
- Do a deep research on each page, use find_on_page, find_next, page_down and page_up to navigate the page. 
- Some pages will have bot blockers and you will receive no content back or error. Use screenshot tool on those urls and you will receive back description produced by vision model.
- If product truly not found, mark status 'fail' and leave price/availability empty.
- After each tool call, write down your findings for each product as you move along.
- When you have finished researching ALL sites, end your message with: "RESEARCH_COMPLETE
"""


async def product_pricer_(
    product: str,
    websites: List[str] | str,
    no_turns: int,
    *,
    creds,
    user_id: str,
    stream_id: str,
):
    """
    automated tool that scrapes product prices from multiple websites.
    #parameters:
    product: str #product name
    websites: List[str] | str #list of websites or a string with websites separated by commas
    """
    local_state.start_streaming(user_id)

    if isinstance(websites, str):
        websites = [w.strip() for w in websites.split(",") if w.strip()]

    system_msg = _build_system_prompt(product, websites)
    msgs: List[Dict[str, str]] = [
        {"role": "developer", "content": system_msg},
        {
            "role": "user",
            "content": f"Please start.",
        },
    ]
    tool_schemas = _get_tool_schemas()

    for step in range(no_turns):

        resp = await model_call(
            input=msgs,
            model="gpt-4.1",
            tools=tool_schemas,
            store=False,
            stream=False,
        )
        if not resp:
            yield {
                "type": "tool_result",
                "toolName": "product_pricer",
                "result": "Model call failed – aborting.",
                "content": "",
                "stream_id": stream_id,
            }
            return

        if resp.output and isinstance(resp.output, list):

            if not local_state.get_state(user_id):
                yield {
                    "type": "endOfMessage",
                    "sources": [],
                    "stream_id": stream_id,
                }
                return

            for item in resp.output:

                if item.type == "message" and getattr(item, "role", "") == "assistant":
                    msgs.append({"role": "assistant", "content": item.content[0].text})

                    yield {
                        "type": "tool_progress",
                        "toolName": "product_pricer",
                        "progress": f"◈ agent's thinking ◈ \n... {item.content[0].text}",
                        "content": item.content[0].text,
                        "stream_id": stream_id,
                    }

                    continue

                if item.type == "function_call":

                    yield {
                        "type": "tool_progress",
                        "toolName": item.name,
                        "progress": f"◇ initiating tool ◇ {item.name}...",
                        "percentage": 0,
                        "stream_id": stream_id,
                    }

                    tool_output = None
                    async for update in _execute_tool_call(
                        item, creds=creds, user_id=user_id, stream_id=stream_id
                    ):
                        if update["type"] == "tool_progress":
                            yield update
                        else:
                            tool_output = update["content"]

                    msgs.append(item)
                    msgs.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": tool_output,
                        }
                    )

            if resp.output_text and resp.output_text.strip():
                msgs.append({"role": "assistant", "content": resp.output_text})
                if "RESEARCH_COMPLETE" in resp.output_text:
                    break

            continue

    yield {
        "type": "tool_progress",
        "toolName": "product_pricer",
        "progress": "◆ Synthesis Phase ◆\n▸ Consolidating market data into structured insights...",
        "percentage": 90,
        "stream_id": stream_id,
    }

    assistant_notes = "\n\n".join(
        m["content"]
        for m in msgs
        if isinstance(m, dict) and m.get("role") == "assistant"
    )

    jsonize_prompt = [
        {
            "role": "developer",
            "content": f"""
Your task is to convert findings of a web agent to json. 
From the research notes below, produce a JSON object with these exact website keys: {websites}.

For each website, extract any price and availability info found. If no info was found, mark status as 'fail'.

Return ONLY this JSON format:
{{
  "<website>": {{"status": "success|fail", "price": "...", "availability": "...", "url": "...", "notes": "..."}},
  ...
}}""",
        },
        {"role": "user", "content": f"Research notes:\n{assistant_notes}"},
    ]

    try:
        jsonize_resp = await model_call(
            input=jsonize_prompt,
            model="gpt-4.1-mini",
            store=False,
            stream=False,
        )
        result_json = json.loads(jsonize_resp.output_text)
    except Exception:
        result_json = {
            site: {"status": "fail", "price": "", "availability": "", "url": ""}
            for site in websites
        }

    yield {
        "type": "tool_result",
        "toolName": "product_pricer",
        "result": "Completed product pricer module.",
        "content": json.dumps(result_json, ensure_ascii=False, indent=2),
        "sources": "",
        "tokens": 0,
        "stream_id": stream_id,
    }
