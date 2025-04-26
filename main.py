import requests
import threading
import os
import sys
import time
import re
import logging
import locale
from datetime import datetime
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TextColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TaskID,
)
from rich.console import Console

# --- Constants ---
CACHE_DIR = "./cache/"
DOWNLOAD_DIR = "./downloads/"
REQUEST_TIMEOUT = 60 # seconds
CHUNK_ITER_SIZE = 8192 # bytes
HEAD_REQUEST_TIMEOUT = 10 # seconds
# --- End Constants ---

# --- Logger Setup ---
locale.setlocale(locale.LC_TIME, '')
log_formatter = logging.Formatter('[%(asctime)s] → %(message)s', datefmt='%A, %d %B %Y - %H:%M (%I:%M %p)')
log_handler = logging.FileHandler('download_history.log', encoding='utf-8')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('DownloadLogger')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
# --- End Logger Setup ---


def clear_console():
    """Clears the console screen."""
    os.system("cls" if os.name == "nt" else "clear")

def ask_until_necessary(msg: str, required_type: str = "str", choice_list: list[str] = []):
    """Prompts the user with a message until a valid input of the specified type is received."""
    while True:
        console.print(msg, end="")
        choice = input().strip()
        
        is_valid = False
        if required_type == "bool":
            is_valid = choice.lower() in choice_list
        elif required_type == "num":
            is_valid = choice == "" or (choice.isdigit() and int(choice) > 0)
        elif required_type == "str":
            is_valid = isinstance(choice, str) and (choice.startswith("http://") or choice.startswith("https://"))

        if is_valid:
            return choice.lower() if required_type == "bool" else choice
        else:
            if len(choice_list) > 0:
                console.print(f"❗️ [bold #f51818]| Please pick one of them: {choice_list}[/]")
            elif required_type == "num":
                console.print("❗️ [bold #f51818]| Please enter a valid number.[/]")
            elif required_type == "str":
                console.print("❗️ [bold #f51818]| Please enter a URL.[/]")
            continue

def download_chunk(url, start_byte, end_byte, output_path, thread_id, progress: Progress, task_id: TaskID, overall_task_id: TaskID, total_size: int):
    headers = {}
    if not (start_byte == 0 and end_byte == total_size - 1):
        headers['Range'] = f'bytes={start_byte}-{end_byte}'
    
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        progress.start_task(task_id)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_ITER_SIZE):
                if chunk:
                    f.write(chunk)
                    progress.update(task_id, advance=len(chunk))
                    progress.update(overall_task_id, advance=len(chunk))

    except requests.exceptions.RequestException as e:
        console.print(f"\n❗️ [bold #f51818]| Error in thread {thread_id}: {e}[/]")
        progress.update(task_id, description=f"[bold #f51818]Thread {thread_id} Error[/]")
    except Exception as e:
        console.print(f"\n❗️ [bold #f51818]| Unexpected error in thread {thread_id}: {e}[/]")
        progress.update(task_id, description=f"[bold #f51818]Thread {thread_id} Error[/]")

def merge_files(num_threads, base_filename, final_filename):
    output_filepath = os.path.join(DOWNLOAD_DIR, final_filename)
    console.print(f"\n⏳ | Merging [cyan]{num_threads}[/] chunks into [cyan]{output_filepath}[/][white]...[/]")
    try:
        with open(output_filepath, 'wb') as outfile:
            for i in range(num_threads):
                chunk_filename = os.path.join(CACHE_DIR, f"{base_filename}.part{i}") 
                if os.path.exists(chunk_filename):
                    with open(chunk_filename, 'rb') as infile:
                        outfile.write(infile.read())
                    os.remove(chunk_filename)
                else:
                    console.print(f"❗️ [bold #f51818]| Chunk file {chunk_filename} not found.[/]")
    except IOError as e:
        console.print(f"❗️ [bold #f51818]| Error merging files! {e}[/]")
    except Exception as e:
        console.print(f"❗️ [bold #f51818]| Unexpected error during merging! {e}[/]")

def download_manager(url: str, num_threads: int):
    try:
        response = requests.head(url, allow_redirects=True, timeout=HEAD_REQUEST_TIMEOUT)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        accept_ranges = response.headers.get('accept-ranges', 'none').lower()
        supports_ranges = accept_ranges == 'bytes'

        if total_size == 0:
            console.print("❗️ [bold #f51818]| Could not determine file size or file size is 0. Process terminated.[/]")
            return

        if not supports_ranges:
            if num_threads > 1:
                console.print("❗️ [bold #f51818]| Server does not support parallel downloads. Falling back to single thread.[/]")
                num_threads = 1

        default_file_name = "downloaded_file" + str(time.time())
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            fname = re.findall('filename=(.+)', content_disposition)
            if fname:
                filename = fname[0].strip('"\'')
            else:
                filename = url.split('/')[-1] or default_file_name
        else:
            filename = url.split('/')[-1] or default_file_name

        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
        if not filename:
            filename = default_file_name
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        chunk_size = total_size // num_threads
        threads = []
        chunk_files = []
        task_ids = []

        progress = Progress(
            TextColumn("[bold blue]{task.description}[/]", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            expand=True
        )

        with progress:
            download_mode = f"{num_threads} threads" if num_threads > 1 else "single thread"
            console.print(f"⏳ | Downloading '[cyan]{filename}[/]' ({total_size / (1024*1024):.2f} MB) using {download_mode}[white]...[/]\n")
            overall_task_id = progress.add_task("[bold #32cd32]Overall Progress[/]", total=total_size) # Added overall task

            for i in range(num_threads):
                start_byte = i * chunk_size
                end_byte = start_byte + chunk_size - 1 if i < num_threads - 1 else total_size - 1
                chunk_filename = f"{filename}.part{i}"
                chunk_filepath = os.path.join(CACHE_DIR, chunk_filename)
                chunk_files.append(chunk_filepath) 
                chunk_total = end_byte - start_byte + 1

                task_id = progress.add_task(f"⤷ Thread {i}", total=chunk_total, start=False)
                task_ids.append(task_id)

                thread = threading.Thread(
                    target=download_chunk,
                    args=(url, start_byte, end_byte, chunk_filepath, i, progress, task_id, overall_task_id, total_size) # Pass total_size
                )
                threads.append(thread)
                thread.start()

            all_threads_done = False
            while not all_threads_done:
                all_threads_done = all(not t.is_alive() for t in threads)
                time.sleep(0.1)

            all_chunks_exist = all(os.path.exists(cf) for cf in chunk_files)
            all_tasks_completed = all(progress.tasks[tid].finished for tid in task_ids)
            no_errors = all("Error" not in progress.tasks[tid].description for tid in task_ids)

            progress.stop()

            if all_chunks_exist and all_tasks_completed and no_errors:
                base_name, extension = os.path.splitext(filename)
                output_filepath = os.path.join(DOWNLOAD_DIR, filename)
                counter = 1
                while os.path.exists(output_filepath):
                    new_filename = f"{base_name} ({counter}){extension}"
                    output_filepath = os.path.join(DOWNLOAD_DIR, new_filename)
                    counter += 1
                
                final_filename = os.path.basename(output_filepath)
                merge_files(num_threads, filename, final_filename)
                console.print(f"✔️  [#1cd916]| File '[cyan]{final_filename}[/]' merged successfully![/]")
                console.print(f"😎 [#1cd916]| Saved as '[cyan]{final_filename}[/]' in the 'downloads' folder.[/]")
                logger.info(f"{url} >> {final_filename}")
            else:
                console.print("\n❗️ [bold #f51818]| Download failed: Not all chunks were downloaded successfully or errors occurred.[/]")
                console.print("⏳ [#dbde16]| Cleaning up partial files...[/]")
                for chunk_filepath in chunk_files:
                    if os.path.exists(chunk_filepath):
                        try:
                            os.remove(chunk_filepath)
                        except OSError as e:
                            console.print(f"❗️ [bold #f51818]| Error removing {chunk_filepath}: {e}[/]")
                console.print(f"✔️  [bold #1cd916]| Partial files successfully deleted.[/]")

    except requests.exceptions.RequestException as e:
        console.print(f"❗️ [bold #f51818]| Error fetching file metadata! {e}[/]")
    except Exception as e:
        console.print(f"❗️ [bold #f51818]| An unexpected error occurred! {e}[/]")

if __name__ == "__main__":
    while True:
        clear_console()
        console = Console()
        console.print(r"""[#0ea5e9]
                                                    ███████╗██╗███████╗████████╗███████╗
                                                    ██╔════╝██║██╔════╝╚══██╔══╝██╔════╝
                                                    █████╗  ██║███████╗   ██║   ███████╗
                                                    ██╔══╝  ██║╚════██║   ██║   ╚════██║
                                                    ██║     ██║███████║   ██║   ███████║
                                                    ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚══════╝
                                                    [/][#f0b616]
██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗      ██████╗  █████╗ ██████╗     ███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ 
██╔══██╗██╔═══██╗██║    ██║████╗  ██║██║     ██╔═══██╗██╔══██╗██╔══██╗    ████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║██║     ██║   ██║███████║██║  ██║    ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝
██║  ██║██║   ██║██║███╗██║██║╚██╗██║██║     ██║   ██║██╔══██║██║  ██║    ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗
██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║███████╗╚██████╔╝██║  ██║██████╔╝    ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║
╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                                                                                                                        
                                                      Thanks for using my program 🤗
              [/]""")
        
        url = ask_until_necessary("🔗 [#dbde16]| Enter the URL of the file you want to download:[/] ", required_type="str")
        num_threads = ask_until_necessary("💪 [#dbde16]| How many threads would you like to use? (Empty means 'Let program decide'):[/] ", required_type="num")
        download_manager(url, (int(num_threads) if num_threads != "" else int(os.cpu_count() / 2)))
        console.print()
        decision = ask_until_necessary("❓ [#dbde16]| Would you like to download another file?:[/] ", required_type="bool", choice_list=["yes", "no"])
        if decision == "no":
            clear_console()
            break
        elif decision == "yes":
            continue