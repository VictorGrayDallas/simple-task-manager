#!/bin/python3

import json
from pathlib import Path
import sys

def error(err: str):
	print(f'Error: {err}', file=sys.stderr)

def get_file() -> Path:
	dir = Path(Path.home(), '.simpletasks')
	dir.mkdir(exist_ok=True)
	return Path(dir, 'data.json')

def save(tasks: dict):
	get_file().write_text(json.dumps(tasks))

def get_tasks() -> dict | None:
	file = get_file()
	# Load and parse
	valid = True
	try:
		contents = file.read_text('utf8') if file.exists else '{}'
		tasks = json.loads(contents)
	except FileNotFoundError:
		error(f'Could not read data file {file.absolute()}')
		return None
	except json.decoder.JSONDecodeError:
		error(f'Unable to parse data file {file.absolute()}')
		valid = False
	# Validate
	valid = type(tasks) == dict # TODO: More rigorous testing? Validation should only matter if the user has manually modified the file.
	if not valid:
		user_input = ''
		while len(user_input) == 0:
			user_input = input('Delete file? All data will be lost. y/n: ')
		if user_input[0] == 'y': # Do we even need to check for a no? For now anything other than y is considered a no.
			file.unlink()
			tasks = {}
		else:
			return None
	return tasks

def add(tasks: dict, args: list[str]) -> bool:
	if len(args) < 1:
		error('No task name given.')
		return False
	task_name = args[0]
	# Ensure this task doesn't already exist.
	if task_name in tasks:
		error(f'Task {task_name} already exists.')
		return False
	# Combine all remaining args for the description.
	description = ' '.join(args[1:]) if len(args) > 1 else 'no description'
	tasks[task_name] = { 'd': description }
	return True

def delete(tasks: dict, args: list[str]) -> bool:
	if len(args) < 1:
		error('No task name given.')
		return False
	if len(args) > 1:
		error('Unexpected arguments after task name.')
		return False
	task_name = args[0]
	if task_name in tasks:
		del tasks[args[0]]
		return True
	else:
		error(f'task {task_name} does not exist.')
		return False
	
def list_tasks(tasks: dict, args: list[str]) -> bool:
	for t in tasks:
		print(f'{t}: {tasks[t]["d"]}')
	return True

# Map command-line commands to functions that handle them.
arg_handlers = {
	'list': list_tasks,
	'add': add,
	'delete': delete,
}
def main(args: list[str]):
	if len(args) == 0:
		error('No arguments.')
		return

	tasks = get_tasks()
	if tasks is None:
		return

	# Check if we have a function to handle the given command.
	if args[0] in arg_handlers:
		handler = arg_handlers[args[0]]
		# handler should return True if the tasks object was modified
		if handler(tasks, args[1:]):
			save(tasks)
	else:
		error(f'Unknown command {args[0]}')

if __name__ == '__main__':
	main(sys.argv[1:])
