from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio

load_dotenv()


async def model_call(
    input: list | str,
    encoded_image: str | list = None,
    model="gpt-4.1",
    reasoning=None,
    tools=None,
    store=False,
    stream=False,
    json=False,
    client_timeout: int = 100,
):
    """OAI endpoint"""
    retries = 5
    sleep_time = 2

    client = AsyncOpenAI(timeout=client_timeout)

    # multimodal
    if isinstance(input, str):
        input = [{"role": "user", "content": input}]
    if (
        model == "gpt-4o"
        or model == "gpt-4o-mini"
        or model == "gpt-4.1"
        or model == "gpt-4.1-mini"
        or model == "gpt-4.1-nano"
    ):
        if encoded_image:
            last_msg = input[-1].copy()
            last_msg_content = last_msg["content"]
            content_array = [
                {
                    "type": "input_text",
                    "text": f"{last_msg_content}",
                },
            ]
            if isinstance(encoded_image, str):
                content_array.append(
                    {"type": "input_image", "image_url": encoded_image}
                )
            else:
                for img in encoded_image:
                    content_array.append({"type": "input_image", "image_url": img})
            last_msg["content"] = content_array
            input[-1] = last_msg
            api_parameters = {
                "model": model,
                "input": input,
                "store": store,
                "stream": stream,
            }
        else:
            api_parameters = {
                "model": model,
                "input": input,
                "store": store,
                "stream": stream,
            }
    if model == "o3-mini" or model == "o4-mini":
        api_parameters = {
            "model": model,
            "input": input,
            "reasoning": reasoning,
            "store": store,
            "stream": stream,
        }
    if tools:
        api_parameters["tools"] = tools
        api_parameters["tool_choice"] = "auto"
    if json == "json":
        api_parameters["text"] = {"format": {"type": "json_object"}}
    else:
        api_parameters["text"] = {"format": {"type": "text"}}

    for attempt in range(retries):
        try:
            response = await client.responses.create(**api_parameters)
            return response

        except Exception as e:
            print(f"\n[model_call]: {e}")
            if attempt < retries - 1:
                sleep_time = sleep_time * (2**attempt)
                print(f"\n[model_call]: Retrying in {sleep_time} seconds...")
                await asyncio.sleep(sleep_time)
            else:
                print(f"\n[model_call]: Failed after {retries} attempts")
                break

    return None


############################################################################################################
