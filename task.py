#!/bin/python3

import json
from pathlib import Path
import sys

def error(err: str):
	print(f'Error: {err}', file=sys.stderr)

def index(text, substr) -> int:
	"""The default str.index method throws an exception if the substring isn't found.
	Returning -1 is so much nicer."""
	try:
		return text.index(substr)
	except ValueError:
		return -1

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
		contents = file.read_text('utf8') if file.exists() else '{}'
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

def make_task(description: str) -> dict:
	if len(description) == 0:
		description = 'no description'
	return { 'd': description }

def add(tasks: dict, args: list[str]) -> bool:
	if len(args) < 1:
		error('No task name given. Example usage: task add [title] [description]')
		return False
	task_name = args[0]
	# Ensure this task doesn't already exist.
	if task_name in tasks:
		error(f'Task {task_name} already exists.')
		return False
	# Ensure task name is a visible string
	if task_name.isspace():
		error('task name cannot be empty')
		return False
	# Combine all remaining args for the description.
	tasks[task_name] = make_task(' '.join(args[1:]))
	return True

def delete(tasks: dict, args: list[str]) -> bool:
	if len(args) < 1:
		error('No task name given. Example usage: task delete [title]')
		return False
	if len(args) > 1:
		error('Unexpected arguments after task name. If your task name contains a space, wrap it in quotes: "task title"')
		return False
	task_name = args[0]
	if task_name in tasks:
		del tasks[args[0]]
		return True
	else:
		error(f'task {task_name} does not exist.')
		return False
	
def list_tasks(tasks: dict, args: list[str]) -> bool:
	# List options:
	# -i for case-insensitive filter
	case_sensitive = not '-i' in args
	# Filter
	filter = []
	for arg in args:
		if not arg.startswith('-'):
			filter.append(arg if case_sensitive else arg.lower())
	# -t: filter by title only
	title_only = '-t' in args
 	# -a for ascending, -d for descending, default no sort
	order = ''
	if '-a' in args:
		order = 'a'
	elif '-d' in args:
		order = 'd'
	# -m: mixed, do not show completed tasks first
	mixed = '-m' in args

	tasks_to_display = []
	# Filter
	for t in tasks:
		task = dict(**tasks[t]) # list_tasks should not modify original task list: we will modify task
		text_for_filter = t if case_sensitive else t.lower()
		if not title_only:
			text_for_filter += task['d'] if case_sensitive else task['d'].lower()
		match = len(filter) == 0 # If no filter, everything matches.
		for filter_str in filter:
			if filter_str in text_for_filter:
				match = True
				break
		if match:
			task['title'] = t
			task['c'] = bool(task.get('c')) # Ensures key exists
			tasks_to_display.append(task)

	# Sort, by completed status (if not using -m) then by title (if using a sort order)
	if order != '':
		reversed = order == 'a'
		if mixed:
			tasks_to_display = sorted(tasks_to_display, key=lambda t: t['d'], reverse=reversed)
		else:
			# We use a tuple as the key so it will sort by completed status first (first element of the tuple), then description.
			tasks_to_display = sorted(tasks_to_display, key=lambda t: (not t['c'] ^ reversed, t['d']), reverse=reversed)
	elif not mixed:
		# We use the negation of completion status as the key to sort completed tasks first.
		tasks_to_display = sorted(tasks_to_display, key=lambda t: not t['c'])

	# Show
	if len(tasks_to_display) == 0:
		print('No tasks to display.')
	for task in tasks_to_display:
		if task['c']:
			print(f'[COMPLETED] {task["title"]}: {task["d"]}')
		else:
			print(f'{task["title"]}: {task["d"]}')

	return False

def update(tasks: dict, args: list[str]) -> bool:
	if len(args) < 1:
		error('No task name given. Example usage: task update [title] [new description]')
		return False
	task_name = args[0]
	if task_name not in tasks:
		error(f'task {task_name} does not exist.')
		return False
	
	# Two options for how to modify task.
	# Option 1: Just a new description
	# Option 2: Specify new title with -t and description with -d
	all_args = ' '.join(args)
	dash_t = index(all_args, ' -t ')
	dash_d = index(all_args, ' -d ')
	if dash_t != -1:
		end_index = len(all_args) if dash_d < dash_t else dash_d
		new_title = all_args[dash_t + 4:end_index]
	else:
		new_title = None
	if dash_d != -1:
		end_index = len(all_args) if dash_t < dash_d else dash_t
		new_description = all_args[dash_d + 4:end_index]
	else:
		# Edge case: If command ended with -d, it has no space after
		if args[-1] == '-d':
			new_description = ''
		else:
			new_description = ' '.join(args[1:])
	
	if new_title is not None:
		result = add(tasks, [new_title, new_description]) # new title may already exist
		if result:
			del tasks[task_name]
		return result
	else:
		tasks[task_name] = make_task(new_description)
		return True

def show_help(a, b):
	print("""Simple task tracker
Available commands:
add: Add a new task, optionally include a description.
	Example: task add [title] [task description]
complete: Mark a task as completed.
	Example: task complete [title]
delete: Delete an existing task.
	Example: task delete [title]
edit: Modify an existing task.
	Example: task edit [title] [new description]
	Or: task edit title -t [new title] -d [new description]
list: Display all tasks.
	Example: task list

For all commands, to include spaces in title, or multiple adjacent spaces in description, wrap them in quotes. To include quotes, enter \\"
""")
	return False

def complete(tasks: dict, args: list[str]) -> bool:
	if len(args) < 1:
		error('No task name given. Example usage: task complete [title]')
		return False
	if len(args) > 1:
		error('Unexpected arguments after task name. If your task name contains a space, wrap it in quotes: "task title"')
		return False
	task_name = args[0]
	if task_name in tasks:
		tasks[args[0]]['c'] = True
		return True
	else:
		error(f'task {task_name} does not exist.')
		return False


# Map command-line commands to functions that handle them.
arg_handlers = {
	'list': list_tasks,
	'add': add,
	'delete': delete,
	'edit': update,
	'help': show_help,
	'complete': complete,
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
