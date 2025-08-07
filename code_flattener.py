import os
import re
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FileStats:
    """Statistics for a processed file."""
    size: int
    tokens: int
    lines: int

class CodeFlattener:
    """
    Flattens a codebase into a single, token-efficient markdown file, respecting .gitignore rules.
    """
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.hpp': 'cpp',
        '.h': 'cpp',
        '.c': 'c',
        '.rb': 'ruby',
        '.php': 'php',
        '.sh': 'bash',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.md': 'markdown',
        '.txt': 'text'
    }

    # Class variables that can be modified
    max_file_size: int = 1024 * 1024  # 1MB
    max_token_length: int = 100_000  # Maximum number of tokens per file

    def __init__(self, root_dir: str, output_file: str, ignore_patterns: Optional[List[str]] = None):
        """
        Initializes the CodeFlattener.

        Args:
            root_dir: The root directory of the codebase.
            output_file: The path to the output markdown file.
            ignore_patterns: A list of additional regex patterns for files/directories to ignore.

        Raises:
            FileNotFoundError: If the root directory does not exist.
        """
        root_path = Path(root_dir).resolve()
        if not root_path.exists():
            raise FileNotFoundError(f"Directory not found: {root_dir}")
        if not root_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {root_dir}")

        self.root_dir = str(root_path)
        self.output_file = str(Path(output_file).resolve())
        self.ignore_patterns = ignore_patterns or []
        self.gitignore_patterns = []
        self.all_ignore_patterns = []
        self.flattened_content = []
        self.file_stats: Dict[str, FileStats] = {}
        logger.info(f"Initialized CodeFlattener for directory: {self.root_dir}")

    def _glob_to_regex(self, pattern: str) -> str:
        """Convert a glob pattern to a regex pattern."""
        if not pattern:
            return ""

        # Escape all special regex characters except * and ?
        pattern = re.escape(pattern).replace(r'\*', '*').replace(r'\?', '?')

        # Convert glob patterns to regex patterns
        pattern = pattern.replace('**', '.*')  # Match any number of directories
        pattern = pattern.replace('*', '[^/]*')  # Match anything except /
        pattern = pattern.replace('?', '[^/]')  # Match single char except /

        # Handle directory patterns
        if pattern.endswith('/'):
            pattern = pattern[:-1] + '(?:/.*)?'

        # Handle path anchoring
        if pattern.startswith('/'):
            pattern = '^' + pattern[1:]
        else:
            pattern = '(?:^|/)' + pattern

        return pattern + '$'

    def _load_gitignore(self):
        """
        Loads and parses patterns from the .gitignore file.
        """
        gitignore_path = os.path.join(self.root_dir, '.gitignore')
        if not os.path.exists(gitignore_path):
            logger.info("No .gitignore file found. Skipping.")
            return

        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Skip negation patterns (!) for now
                    if line.startswith('!'):
                        continue
                    self.gitignore_patterns.append(self._glob_to_regex(line))

        # Common ignore patterns
        default_patterns = [
            r'\.git(?:/.*)?',
            r'\.idea(?:/.*)?',
            r'__pycache__(?:/.*)?',
            r'.*\.pyc',
            r'.*\.log',
            r'\.env',
            r'.*venv(?:/.*)?',
            r'node_modules(?:/.*)?',
            r'dist(?:/.*)?',
            r'build(?:/.*)?'
        ]

        # Convert ignore patterns from command line
        converted_ignores = [self._glob_to_regex(p) for p in self.ignore_patterns]

        self.all_ignore_patterns = default_patterns + self.gitignore_patterns + converted_ignores
        logger.info(f"Loaded {len(self.gitignore_patterns)} patterns from .gitignore.")

    def _should_ignore(self, path: str) -> bool:
        """
        Checks if a path should be ignored based on .gitignore and other patterns.
        """
        relative_path = os.path.relpath(path, self.root_dir)
        for pattern in self.all_ignore_patterns:
            # Match the pattern against the entire path
            if re.search(pattern, relative_path):
                return True
            # Also match against the base name for patterns like 'venv'
            if re.search(pattern, os.path.basename(path)):
                return True
        return False

    def _get_language_specific_patterns(self, extension: str) -> Dict[str, str]:
        """
        Returns language-specific patterns for comment removal.
        """
        patterns = {
            'python': {
                'single_line': r'#.*$',
                'multi_line': [r'"""[\s\S]*?"""', r"'''[\s\S]*?'''"],
            },
            'javascript': {
                'single_line': r'//.*$',
                'multi_line': [r'/\*[\s\S]*?\*/'],
            },
            'typescript': {
                'single_line': r'//.*$',
                'multi_line': [r'/\*[\s\S]*?\*/'],
            },
            'java': {
                'single_line': r'//.*$',
                'multi_line': [r'/\*[\s\S]*?\*/'],
            },
            'go': {
                'single_line': r'//.*$',
                'multi_line': [r'/\*[\s\S]*?\*/'],
            },
            'rust': {
                'single_line': r'//.*$',
                'multi_line': [r'/\*[\s\S]*?\*/'],
            },
            'ruby': {
                'single_line': r'#.*$',
                'multi_line': [r'=begin[\s\S]*?=end'],
            },
        }
        return patterns.get(self.SUPPORTED_EXTENSIONS.get(extension, 'text'), {})

    def _clean_code(self, code: str, file_path: str) -> str:
        """
        Removes comments and docstrings to make the code token-efficient.
        """
        extension = os.path.splitext(file_path)[1].lower()
        patterns = self._get_language_specific_patterns(extension)

        if patterns:
            # Remove single-line comments
            if 'single_line' in patterns:
                code = re.sub(patterns['single_line'], '', code, flags=re.MULTILINE)

            # Remove multi-line comments
            if 'multi_line' in patterns:
                for pattern in patterns['multi_line']:
                    code = re.sub(pattern, '', code)

        # Remove empty lines but preserve indentation
        lines = []
        for line in code.splitlines():
            if line.strip():  # Only process non-empty lines
                lines.append(line.rstrip())  # Remove trailing whitespace but keep indentation
        return '\n'.join(lines)

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimates the number of tokens in a text.
        A very rough estimation - actual tokens may vary by model.
        """
        words = re.findall(r'\b\w+\b', text)
        symbols = len(re.findall(r'[^\w\s]', text))
        return len(words) + symbols

    def _process_file(self, file_path: str):
        """
        Reads, cleans, and formats a single file's content.
        """
        try:
            extension = os.path.splitext(file_path)[1].lower()
            if extension not in self.SUPPORTED_EXTENSIONS:
                logger.debug(f"Skipping unsupported file type: {file_path}")
                return

            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(f"Skipping large file: {file_path} ({file_size} bytes)")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            cleaned_content = self._clean_code(content, file_path)
            if cleaned_content:
                relative_path = os.path.relpath(file_path, self.root_dir)
                tokens = self._estimate_tokens(cleaned_content)

                if tokens > self.max_token_length:
                    logger.warning(f"File exceeds token limit: {relative_path} ({tokens} tokens)")
                    cleaned_content = cleaned_content[:int(len(cleaned_content) * self.max_token_length / tokens)]
                    cleaned_content += "\n# ... (truncated due to token limit) ..."

                self.file_stats[relative_path] = FileStats(
                    size=file_size,
                    tokens=tokens,
                    lines=len(cleaned_content.splitlines())
                )

                self.flattened_content.append(
                    f"### File: {relative_path}\n"
                    f"```python\n"
                    f"{cleaned_content}\n"
                    f"```\n"
                )
                logger.debug(f"Processed file: {relative_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")

    def _generate_project_structure(self) -> str:
        """
        Generates a tree-like structure of the project.
        """
        structure = []
        last_dir = None

        for file_path in sorted(self.file_stats.keys()):
            parts = file_path.split(os.sep)
            current_dir = os.path.dirname(file_path)

            if current_dir != last_dir:
                if current_dir:
                    depth = len(current_dir.split(os.sep))
                    structure.append(f"{'  ' * (depth-1)}📁 {os.path.basename(current_dir)}/")
                last_dir = current_dir

            stats = self.file_stats[file_path]
            depth = len(parts) - 1
            structure.append(
                f"{'  ' * depth}📄 {os.path.basename(file_path)} "
                f"({stats.lines} lines, ~{stats.tokens} tokens)"
            )

        return "\n".join(structure)

    def _generate_summary(self) -> str:
        """
        Generates a summary of the flattened codebase.
        """
        total_files = len(self.file_stats)
        total_lines = sum(stats.lines for stats in self.file_stats.values())
        total_tokens = sum(stats.tokens for stats in self.file_stats.values())
        total_size = sum(stats.size for stats in self.file_stats.values())

        return (
            f"## Project Summary\n\n"
            f"- Total files processed: {total_files}\n"
            f"- Total lines of code: {total_lines}\n"
            f"- Estimated total tokens: {total_tokens}\n"
            f"- Total size: {total_size / 1024:.1f} KB\n"
        )

    def flatten(self):
        """
        Recursively traverses the root directory and flattens all files.
        """
        logger.info("Starting to flatten codebase...")
        self._load_gitignore()
        self.flattened_content = []
        self.file_stats.clear()

        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            # Modify dirnames in-place to prune traversal
            dirnames[:] = [d for d in dirnames if not self._should_ignore(os.path.join(dirpath, d))]
            # Sort for consistent output
            dirnames.sort()
            for filename in sorted(filenames):
                file_path = os.path.join(dirpath, filename)
                if not self._should_ignore(file_path):
                    self._process_file(file_path)

        self.save_output()
        logger.info(f"Finished flattening codebase. Output saved to {self.output_file}")

    def save_output(self):
        """
        Saves the flattened content to the specified output file.

        Raises:
            PermissionError: If the output file cannot be written due to permission issues.
            OSError: If there are other IO-related errors.
        """
        try:
            # First check if we can write to the output directory
            output_dir = os.path.dirname(self.output_file)
            if not os.access(output_dir, os.W_OK):
                raise PermissionError(f"No write permission for directory: {output_dir}")

            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write("# Codebase Flattened for Agentic Workflow\n\n")
                f.write("This file contains the project's source code, optimized for token efficiency:\n")
                f.write("- Comments and docstrings have been removed\n")
                f.write("- Empty lines have been cleaned up\n")
                f.write("- Large files have been truncated\n")
                f.write("- Only relevant file types are included\n\n")

                # Write summary
                f.write(self._generate_summary())
                f.write("\n## Project Structure\n\n")
                f.write(self._generate_project_structure())
                f.write("\n\n## Source Code\n\n")
                f.write("Each file is demarcated by a header showing its relative path.\n\n")
                f.write("--------------------\n\n")
                f.write("\n".join(self.flattened_content))

            logger.info(f"Successfully saved flattened content to {self.output_file}")
        except (PermissionError, OSError) as e:
            logger.error(f"Error saving output file {self.output_file}: {e}")
            raise  # Re-raise the exception for proper error handling

def main():
    parser = argparse.ArgumentParser(
        description='Flatten a codebase into a single, token-efficient markdown file.'
    )
    parser.add_argument(
        'root_dir',
        help='Root directory of the codebase to flatten',
        type=str,
        nargs='?',
        default='.',
    )
    parser.add_argument(
        '-o', '--output',
        help='Output markdown file path (default: flattened_codebase.md)',
        type=str,
        default='flattened_codebase.md'
    )
    parser.add_argument(
        '--ignore',
        help='Additional patterns to ignore (comma-separated)',
        type=str,
    )
    parser.add_argument(
        '--max-file-size',
        help='Maximum file size in MB (default: 1)',
        type=float,
        default=1.0
    )
    parser.add_argument(
        '--max-tokens',
        help='Maximum tokens per file (default: 100000)',
        type=int,
        default=100000
    )
    parser.add_argument(
        '-v', '--verbose',
        help='Enable verbose logging',
        action='store_true'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    CodeFlattener.max_file_size = int(args.max_file_size * 1024 * 1024)
    CodeFlattener.max_token_length = args.max_tokens

    ignore_patterns = []
    if args.ignore:
        ignore_patterns = [p.strip() for p in args.ignore.split(',')]

    try:
        root_dir = str(Path(args.root_dir).resolve())
        if not os.path.isdir(root_dir):
            raise ValueError(f"Directory not found: {args.root_dir}")

        flattener = CodeFlattener(
            root_dir=root_dir,
            output_file=args.output,
            ignore_patterns=ignore_patterns
        )
        flattener.flatten()
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())