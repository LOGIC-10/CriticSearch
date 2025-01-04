# cli.py
import click

from .tasks_runner import run_tasks


@click.command()
@click.argument("tasks", nargs=-1)  # 接收多个任务作为参数
@click.option(
    "--max-iterations",
    "-m",
    default=10,
    help="Maximum number of iterations for each task.",
)
def cli(tasks, max_iterations):
    """
    Command-line tool to run multiple tasks iteratively.

    Arguments:
    - TASKS: List of tasks (questions) to process.

    Options:
    - --max-iterations/-m: Maximum number of iterations for each task.
    """
    run_tasks(tasks, max_iterations)


if __name__ == "__main__":
    cli()
