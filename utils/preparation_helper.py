from progress import states
from typing import Callable, Optional


def preparation_helper(
    task_id,
    task_name: str,
    csv_file_path,
    writer_csv_exec: Callable[[], None],
    sql_exec: Callable[[], None],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    try:
        progress = states.read_progress()
        if task_id not in progress:
            progress[task_id] = {
                "status": "started",
                "filenames": {},
                "tasks": {},
                "range_date": {},
            }
        progress[task_id]["tasks"][task_name] = "in_progress"

        # callback function writer
        sql_exec()
        writer_csv_exec()

        progress[task_id]["tasks"][task_name] = "completed"
        progress[task_id]["filenames"][task_name] = csv_file_path
        if start_date or end_date:
            if start_date:
                progress[task_id]["range_date"]["start_date"] = start_date
            if end_date:
                progress[task_id]["range_date"]["end_date"] = end_date

        if all(status == "completed" for status in progress[task_id]["tasks"].values()):
            progress[task_id]["status"] = "completed"
        states.write_progress(progress)
    except Exception as e:
        print(f"Error executing query: {e}")
        progress[task_id]["tasks"][task_name] = "failed"
        progress[task_id]["status"] = "failed"
        states.write_progress(progress)
        raise e
