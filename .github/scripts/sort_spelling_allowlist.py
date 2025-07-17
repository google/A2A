import shutil
import tempfile

from pathlib import Path


def sort_unique_lines_in_file(file_path_str: str) -> None:
    """Atomically sorts the lines in a text file and removes duplicates.

    Args:
        file_path_str: The path to the file to be processed.
    """
    file_path = Path(file_path_str)

    try:
        with file_path.open('r', encoding='utf-8') as original_file:
            unique_lines = sorted(set(original_file))

        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', delete=False, dir=file_path.parent
        ) as temp_file:
            temp_file.writelines(unique_lines)
            temp_path = temp_file.name

        shutil.move(temp_path, file_path)
        print(f'Successfully sorted and updated {file_path.name}')

    except FileNotFoundError:
        print(f'Error: The file {file_path} was not found.')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')


if __name__ == '__main__':
    ALLOW_FILE = '.github/actions/spelling/allow.txt'
    sort_unique_lines_in_file(ALLOW_FILE)
