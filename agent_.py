from classes.keyboardmanager import keyboard_listener
from classes.statemanager import local_state
from product_pricer_ import product_pricer_
from rich.prompt import Prompt, IntPrompt
from utils import ensure_user_workspace
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from typing import List
import pandas as pd
import asyncio
import time
import json
import os
import re

console = Console()


def create_welcome_panel():
    """welcome panel"""

    features = [
        ("real-time market monitoring", "white"),
        ("cross-platform price comparison", "white"),
        ("intelligent content navigation", "white"),
        ("visual webpage analysis", "white"),
    ]

    content = Text()

    content.append("\n")
    title_text = Text()
    title_text.append("price", style="bold white")
    title_text.append("iq", style="bold bright_cyan")
    content.append(title_text.plain)
    content.append("\n")
    content.append("agent", style="bold white")
    content.append("\n\n")

    content.append("intelligent product price discovery", style="italic bright_white")
    content.append("\n")
    content.append("less but better pricing intelligence", style="dim cyan")
    content.append("\n\n")

    for feature, style in features:
        content.append("  ▸ ", style="bright_cyan")
        content.append(feature, style=style)
        content.append("\n")

    content.append("\n")
    content.append("Press ", style="dim white")
    content.append("'q'", style="bold bright_red")
    content.append(" to stop", style="dim white")
    content.append("\n")

    centered_content = Align.center(content)

    return Panel(
        centered_content,
        title="",
        border_style="bright_white",
        padding=(2, 4),
        width=70,
    )


def create_product_panel(product: str, index: int, total: int):
    """product processing panel"""
    progress_bar = "▓" * (index) + "░" * (total - index - 1)

    content = Text.assemble(
        ("◈ Product: ", "bright_yellow"),
        (product, "bold white"),
        "\n",
        ("◈ Progress: ", "bright_yellow"),
        (f"{index + 1}/{total}", "bold cyan"),
        " ",
        (progress_bar, "bright_blue"),
        "\n",
        ("◈ Status: ", "bright_yellow"),
        ("Analyzing market data...", "bright_green"),
    )

    return Panel(
        content,
        title=f"╭─ processing product {index + 1} ─╮",
        title_align="center",
        border_style="bright_green",
        padding=(1, 2),
    )


def format_progress_message(message: str, tool_name: str = "") -> Panel:
    """progress msg formatter"""

    tool_styles = {
        "web_search": ("🔍", "bright_blue", "Web Discovery"),
        "visit_url": ("🌐", "bright_green", "Page Analysis"),
        "screenshot": ("📸", "bright_magenta", "Visual Intelligence"),
        "find_on_page": ("🎯", "bright_yellow", "Content Search"),
        "page_down": ("⬇️", "bright_cyan", "Navigation"),
        "page_up": ("⬆️", "bright_cyan", "Navigation"),
        "find_next": ("🔄", "bright_yellow", "Search Continue"),
        "product_pricer": ("💰", "bright_green", "Price Analysis"),
    }

    icon, color, label = tool_styles.get(tool_name, ("⚡", "white", "Processing"))

    timestamp = time.time()
    dots = "●" * (int(timestamp * 2) % 4) + "○" * (3 - (int(timestamp * 2) % 4))

    content = Text.assemble(
        (f"{icon} ", color),
        (label, f"bold {color}"),
        "\n",
        ("▸ ", "dim"),
        (message, "white"),
        "\n",
        ("  ", ""),
        (dots, color),
    )

    return Panel(content, border_style=color, padding=(0, 1), width=80)


def save_results(cum_json: List[dict], user_id: str, save_format: str):
    """Save results in chosen format"""
    user_folder = ensure_user_workspace(user_id)

    if save_format.lower() == "json":
        fname = f"product_pricer_{user_id}.json"
        fpath = os.path.join(user_folder, fname)
        with open(fpath, "w", encoding="utf-8") as fh:
            json.dump(cum_json, fh, ensure_ascii=False, indent=2)
        return fpath

    elif save_format.lower() == "excel":
        fname = f"product_pricer_{user_id}.xlsx"
        fpath = os.path.join(user_folder, fname)

        flattened_data = []
        summary_data = []

        for item in cum_json:
            product = item["product"]

            total_sites = len(item["data"])
            successful_sites = sum(
                1
                for site_data in item["data"].values()
                if site_data["status"] == "success"
            )
            success_rate = f"{successful_sites}/{total_sites} ({(successful_sites/total_sites*100):.1f}%)"

            prices = []
            for site_data in item["data"].values():
                if site_data["status"] == "success" and site_data["price"]:
                    price_text = site_data["price"]
                    try:

                        price_match = re.search(
                            r"(\d+[,.]?\d*)", price_text.replace(",", ".")
                        )
                        if price_match:
                            prices.append(float(price_match.group(1)))
                    except:
                        pass

            best_price = f"{min(prices):.2f} €" if prices else "N/A"

            summary_data.append(
                {
                    "Product": product,
                    "Sites_Searched": total_sites,
                    "Success_Rate": success_rate,
                    "Best_Price_Found": best_price,
                    "Available_At": successful_sites,
                }
            )

            for website, data in item["data"].items():
                flattened_data.append(
                    {
                        "Product": product,
                        "Website": website,
                        "Status": data["status"],
                        "Price": data["price"],
                        "Availability": data["availability"],
                        "URL": data["url"],
                        "Notes": data["notes"],
                    }
                )

        with pd.ExcelWriter(fpath, engine="openpyxl") as writer:
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            detailed_df = pd.DataFrame(flattened_data)
            detailed_df.to_excel(writer, sheet_name="Detailed_Results", index=False)

            success_df = detailed_df[detailed_df["Status"] == "success"]
            success_df.to_excel(writer, sheet_name="Success_Only", index=False)

            failed_df = detailed_df[detailed_df["Status"] == "fail"]
            failed_df.to_excel(writer, sheet_name="Failed_Searches", index=False)

            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        return fpath


async def _agent_entry_():
    user_id = "localUser"
    stream_id = "test_"

    console.clear()
    console.print(create_welcome_panel())
    console.print()

    products_input = Prompt.ask(
        "[bright_cyan]Enter products to analyze (separate with ' | ')[/bright_cyan]",
        default="nöm Joghurt gerührt 3,6% | Danone Dany Sahne Schokolade",
    )
    products = [p.strip() for p in products_input.split("|") if p.strip()]

    websites_input = Prompt.ask(
        "[bright_cyan]Enter websites to search (separate with ' | ')[/bright_cyan]",
        default="https://shop.billa.at/ | https://www.gurkerl.at/ | https://hausbrot.at/",
    )
    websites = [w.strip() for w in websites_input.split("|") if w.strip()]

    save_format = Prompt.ask(
        "[bright_cyan]Choose output format[/bright_cyan]",
        choices=["json", "excel"],
        default="json",
    )

    no_turns = IntPrompt.ask(
        "[bright_cyan]Enter number of turns[/bright_cyan]",
        default=10,
    )

    if save_format == "excel":
        console.print(
            Panel(
                Text.assemble(
                    ("📊 Excel format will include:\n", "bright_yellow"),
                    ("  • ", "dim"),
                    ("Summary sheet with success rates\n", "white"),
                    ("  • ", "dim"),
                    ("Detailed results (flattened)\n", "white"),
                    ("  • ", "dim"),
                    ("Success-only data\n", "white"),
                    ("  • ", "dim"),
                    ("Failed searches analysis\n", "white"),
                ),
                title="╭─ Excel Output ─╮",
                border_style="bright_blue",
            )
        )

    console.print()

    keyboard_listener.start_listening(user_id)
    cum_json: List[dict] = []

    try:
        for index, product in enumerate(products):
            console.print(create_product_panel(product, index, len(products)))
            console.print()

            async for out in product_pricer_(
                product=product,
                websites=websites,
                no_turns=no_turns,
                creds=None,
                user_id=user_id,
                stream_id=stream_id,
            ):
                if not local_state.get_state(user_id):
                    console.print(
                        Panel(
                            "◆ Process stopped by user",
                            style="bold red",
                            title="╭─ Stopped ─╮",
                        )
                    )
                    break

                if out["type"] == "tool_progress":
                    tool_name = out.get("toolName", "")
                    progress_panel = format_progress_message(out["progress"], tool_name)
                    console.print(progress_panel)
                else:
                    result_data = json.loads(out["content"])

                    table = Table(
                        title=f"Results for {product}",
                        show_header=True,
                        header_style="bold cyan",
                    )
                    table.add_column("Website", style="bright_blue", width=30)
                    table.add_column("Status", justify="center", width=10)
                    table.add_column(
                        "Price", justify="right", style="bright_green", width=15
                    )
                    table.add_column("Availability", style="bright_yellow", width=20)

                    for website, data in result_data.items():
                        status_style = (
                            "bright_green"
                            if data["status"] == "success"
                            else "bright_red"
                        )
                        status_icon = "✓" if data["status"] == "success" else "✗"

                        table.add_row(
                            website,
                            f"[{status_style}]{status_icon}[/{status_style}]",
                            data.get("price", "N/A"),
                            data.get("availability", "N/A"),
                        )

                    console.print()
                    console.print(table)
                    console.print()

                    cum_json.append({"product": product, "data": result_data})

    except KeyboardInterrupt:
        console.print(Panel("◆ Process interrupted", style="bold red"))
    finally:
        local_state.stop_streaming(user_id)
        keyboard_listener.stop_listening()

        if cum_json:
            saved_path = save_results(cum_json, user_id, save_format)
            console.print(
                Panel(
                    f"◆ Results saved to: {saved_path}",
                    style="bright_green",
                    title="╭─ Complete ─╮",
                )
            )


if __name__ == "__main__":
    asyncio.run(_agent_entry_())
