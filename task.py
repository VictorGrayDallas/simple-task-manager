#!/bin/python3

import json
from pathlib import Path
import sys

def main(args: list[str]):
	if len(args) == 0:
		print('Error: No arguments.')
		return

	# Ensure the file exists
	dir = Path(Path.home(), '.simpletasks')
	dir.mkdir(exist_ok=True)
	file = Path(dir, 'data.json')
	if not file.exists():
		file.write_text('{}')
	# Load and parse
	valid = True
	try:
		contents = file.read_text('utf8')
		tasks = json.loads(contents)
	except FileNotFoundError:
		print(f'Error: Could not read data file {file.absolute()}')
		return
	except json.decoder.JSONDecodeError:
		print(f'Error: Unable to parse data file {file.absolute()}')
		valid = False
	# Validate
	valid = type(tasks) == dict # TODO: More rigorous testing? Validation should only matter if the user has manually modified the file.
	if not valid:
		user_input = ''
		while len(user_input) == 0:
			user_input = input('Delete file and make a new one? All data will be lost. y/n: ')
		if user_input[0] == 'y': # Do we even need to check for a no? For now anything other than y is considered a no.
			file.unlink()
			main(args)
		return
	
	match args[0]:
		case 'list':
			for t in tasks:
				print(f'{t}: {tasks[t]}')
		case _:
			print('default')

if __name__ == '__main__':
	main(sys.argv[1::])
