# CodeFlattener

CodeFlattener is a Python utility that flattens a codebase into a single, token-efficient markdown file. It's designed to help you quickly grasp the structure and content of a project, and to prepare code for use in Large Language Model (LLM) prompts and other agentic workflows.

## Features

*   **Single File Output**: Consolidates an entire codebase into one markdown file.
*   **Token Efficient**: Removes comments, docstrings, and empty lines to reduce token count.
*   **`.gitignore` Aware**: Automatically respects the ignore patterns in your `.gitignore` file.
*   **Customizable**: Allows for additional ignore patterns, and limits on file size and token length.
*   **Language Support**: Supports a wide range of popular programming languages.
*   **Project Overview**: Generates a project summary and a file structure tree for easy navigation.
*   **No Dependencies**: Runs with a standard Python 3 installation, no external libraries needed.

## Getting Started

### Prerequisites

*   Python 3.6 or higher

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/FranklinChui/CodeFlattener.git
    ```
2.  Navigate to the project directory:
    ```bash
    cd CodeFlattener
    ```

### Usage

To flatten a codebase, run the `code_flattener.py` script from your terminal.

**Basic Usage:**

```bash
python code_flattener.py /path/to/your/project
```

This will create a `flattened_codebase.md` file in the current directory.

**Specify Output File:**

```bash
python code_flattener.py /path/to/your/project -o my_project_flat.md
```

## Configuration

You can customize the behavior of CodeFlattener with the following command-line arguments:

| Argument          | Short | Description                                           | Default                  |
| ----------------- | ----- | ----------------------------------------------------- | ------------------------ |
| `root_dir`        |       | The root directory of the codebase to flatten.        | `.`                      |
| `--output`        | `-o`  | The path to the output markdown file.                 | `flattened_codebase.md`  |
| `--ignore`        |       | Comma-separated list of additional patterns to ignore. | ` `                        |
| `--max-file-size` |       | Maximum file size in MB to process.                   | `1.0`                    |
| `--max-tokens`    |       | Maximum number of tokens per file.                    | `100000`                 |
| `--verbose`       | `-v`  | Enable verbose logging for debugging.                 | `False`                  |

## How It Works

The `CodeFlattener` script follows these steps:

1.  **Initializes**: Sets up the root directory, output file, and any custom configurations.
2.  **Loads Ignore Patterns**: Reads `.gitignore` and any additional ignore patterns provided.
3.  **Traverses Directory**: Walks through the project directory, skipping ignored files and folders.
4.  **Processes Files**: For each supported file, it:
    *   Reads the content.
    *   Removes comments and docstrings.
    *   Strips empty lines.
    *   Truncates the file if it exceeds the token limit.
5.  **Generates Output**: Creates a single markdown file containing:
    *   A summary of the project (total files, lines, tokens).
    *   A tree-like view of the project structure.
    *   The cleaned and formatted content of each file.

## Running Tests

To run the test suite, execute the `test_flattener.py` script:

```bash
python test_flattener.py
```

The tests will create temporary directories and files to ensure the `CodeFlattener` works as expected under various conditions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
