#!/bin/python3

import json
from pathlib import Path
import sys

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
		print(f'Error: Could not read data file {file.absolute()}')
		return None
	except json.decoder.JSONDecodeError:
		print(f'Error: Unable to parse data file {file.absolute()}')
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
		print('Error: No task name given.')
		return False
	task_name = args[0]
	# Ensure this task doesn't already exist.
	if task_name in tasks:
		print(f'Error: Task {task_name} already exists.')
		return False
	# Combine all remaining args for the description.
	description = ' '.join(args[1:]) if len(args) > 1 else 'no description'
	tasks[task_name] = { 'd': description }
	return True

def main(args: list[str]):
	if len(args) == 0:
		print('Error: No arguments.')
		return

	tasks = get_tasks()
	if tasks is None:
		return

	match args[0]:
		case 'list':
			for t in tasks:
				print(f'{t}: {tasks[t]["d"]}')
		case 'add':
			if add(tasks, args[1:]):
				save(tasks)
		case _:
			print('default')

if __name__ == '__main__':
	main(sys.argv[1:])
