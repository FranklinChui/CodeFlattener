import unittest
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from code_flattener import CodeFlattener

# Configure logging
log_dir = 'test_logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'test_flattener_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Create a formatter that includes timestamp, logger name, level, and message
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create and configure the file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create and configure the console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Configure the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Get logger for this module
logger = logging.getLogger(__name__)

class TestCodeFlattener(unittest.TestCase):
    """
    Comprehensive tests for the CodeFlattener class.
    Tests both positive and negative scenarios.
    """
    # Create unique temporary test directory for each test run
    test_dir: str
    output_file: str

    def _create_temp_dir(self) -> str:
        """Create a unique temporary directory for testing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return os.path.join('tmp', f'test_dir_{timestamp}')

    @classmethod
    def setUpClass(cls):
        """Set up logging and create test directories."""
        logger.info("="*80)
        logger.info("Starting CodeFlattener test suite")
        logger.info("="*80)

    def setUp(self):
        """Set up a temporary project structure for testing."""
        # Log the start of the test method
        current_test = self.id().split('.')[-1]
        logger.info("-"*60)
        logger.info(f"Setting up test: {current_test}")

        # Create temporary test directory
        self.test_dir = self._create_temp_dir()
        self.output_file = os.path.join(self.test_dir, 'output.md')

        # Ensure tmp directory exists
        os.makedirs('tmp', exist_ok=True)

        logger.info(f"Created test environment in {self.test_dir}")

        # Create test project structure
        os.makedirs(os.path.join(self.test_dir, 'src'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'tests'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'docs'), exist_ok=True)

        # Create Python files with various content types
        self._create_test_files()

        # Create files that should be ignored
        self._create_ignored_files()

        logger.debug("Test environment setup completed")

    def _create_test_files(self):
        """Create test files with various content types."""
        # Python file with multiple comment types
        with open(os.path.join(self.test_dir, 'src', 'main.py'), 'w') as f:
            f.write('''"""
            Module level docstring
            with multiple lines
            """

            import sys

            # Constants
            MAX_VALUE = 100

            def calculate(x: int) -> int:
                """Function docstring"""
                # Inline comment
                return x * 2  # Another inline comment
            ''')

        # JavaScript file
        with open(os.path.join(self.test_dir, 'src', 'script.js'), 'w') as f:
            f.write('''// JavaScript file
            /* Multi-line
               comment */
            function test() {
                // Another comment
                return true;
            }
            ''')

        # Empty file
        Path(os.path.join(self.test_dir, 'empty.py')).touch()

        # Large file
        with open(os.path.join(self.test_dir, 'large_file.py'), 'w') as f:
            f.write('x = 1\n' * 50000)  # Create a large file

        # Create a custom .gitignore
        with open(os.path.join(self.test_dir, '.gitignore'), 'w') as f:
            f.write('''
            *.log
            __pycache__/
            .env
            temp/
            ''')

    def _create_ignored_files(self):
        """Create files that should be ignored based on .gitignore patterns."""
        os.makedirs(os.path.join(self.test_dir, '__pycache__'), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, 'temp'), exist_ok=True)

        # Create files that should be ignored
        with open(os.path.join(self.test_dir, 'debug.log'), 'w') as f:
            f.write('log content')
        with open(os.path.join(self.test_dir, '.env'), 'w') as f:
            f.write('SECRET_KEY=test')

    def tearDown(self):
        """Clean up the temporary test environment."""
        current_test = self.id().split('.')[-1]

        # Get the test result
        result = self._outcome.result
        if hasattr(result, '_excinfo') and result._excinfo:
            logger.error(f"Test FAILED: {current_test}")
            error_type, error, _ = result._excinfo[-1]
            logger.error(f"Error: {error_type.__name__}: {str(error)}")
        else:
            logger.info(f"Test PASSED: {current_test}")

        logger.info(f"Cleaning up test: {current_test}")

        # Only remove directories under tmp/
        if self.test_dir and self.test_dir.startswith(os.path.join(os.getcwd(), 'tmp')):
            if os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
                logger.info(f"Removed test directory: {self.test_dir}")

        logger.info("-"*60)    # Positive Test Cases
    def test_basic_flattening(self):
        """Test basic flattening functionality with default settings."""
        logger.info("Testing basic flattening")
        flattener = CodeFlattener(self.test_dir, self.output_file)
        flattener.flatten()

        with open(self.output_file, 'r') as f:
            content = f.read()

        self.assertIn("### File: src/main.py", content)
        self.assertIn("def calculate(x: int) -> int:", content)
        self.assertNotIn('"""Module level docstring"""', content)
        self.assertNotIn("# Constants", content)

        logger.debug("Basic flattening test completed")

    def test_supported_languages(self):
        """Test handling of different supported file types."""
        logger.info("Testing supported languages handling")
        flattener = CodeFlattener(self.test_dir, self.output_file)
        flattener.flatten()

        with open(self.output_file, 'r') as f:
            content = f.read()

        # Python content
        self.assertIn("def calculate", content)
        # JavaScript content
        self.assertIn("function test()", content)
        self.assertNotIn("// JavaScript file", content)
        self.assertNotIn("/* Multi-line", content)

    def test_comment_removal(self):
        """Test comment removal functionality."""
        logger.info("Testing comment removal")
        flattener = CodeFlattener(self.test_dir, self.output_file)
        test_file = os.path.join(self.test_dir, 'test.py')

        code_with_comments = '''# This is a comment
def my_func():
    """A docstring"""
    x = 1 # an inline comment
    return x'''

        with open(test_file, 'w') as f:
            f.write(code_with_comments)

        cleaned_code = flattener._clean_code(code_with_comments, test_file)
        # Use actual indentation from the code
        expected_code = "def my_func():\n    x = 1\n    return x"

        # Compare normalized strings (strip whitespace from each line)
        cleaned_lines = [line.rstrip() for line in cleaned_code.splitlines() if line.strip()]
        expected_lines = [line.rstrip() for line in expected_code.splitlines() if line.strip()]
        self.assertEqual(cleaned_lines, expected_lines)

        logger.debug("Comment removal test completed")

    # Negative Test Cases
    def test_invalid_directory(self):
        """Test handling of non-existent directory."""
        logger.info("Testing invalid directory handling")
        nonexistent_dir = os.path.join(self.test_dir, "nonexistent_subdir")

        # Test with a non-existent subdirectory
        with self.assertRaises((FileNotFoundError, OSError)):
            flattener = CodeFlattener(nonexistent_dir, self.output_file)
            flattener.flatten()

    def test_invalid_gitignore_pattern(self):
        """Test handling of invalid gitignore patterns."""
        logger.info("Testing invalid gitignore pattern handling")
        with open(os.path.join(self.test_dir, '.gitignore'), 'w') as f:
            f.write('[invalid-regex')  # Invalid regex pattern

        flattener = CodeFlattener(self.test_dir, self.output_file)
        flattener.flatten()  # Should handle invalid pattern gracefully

        self.assertTrue(os.path.exists(self.output_file))

    def test_empty_directory(self):
        """Test handling of empty directory."""
        logger.info("Testing empty directory handling")
        empty_dir = "empty_test_dir"
        os.makedirs(empty_dir, exist_ok=True)

        try:
            flattener = CodeFlattener(empty_dir, self.output_file)
            flattener.flatten()

            with open(self.output_file, 'r') as f:
                content = f.read()

            # Check that the content indicates no files were processed
            self.assertIn("Total files processed: 0", content)
            self.assertIn("Total lines of code: 0", content)
            self.assertIn("Project Structure", content)
            self.assertIn("Source Code", content)
        finally:
            shutil.rmtree(empty_dir)

    def test_permission_error(self):
        """Test handling of permission errors."""
        logger.info("Testing permission error handling")
        if os.name != 'nt':  # Skip on Windows
            readonly_dir = "readonly_test_dir"
            os.makedirs(readonly_dir, exist_ok=True)

            # Create a test file in the directory
            test_file = os.path.join(readonly_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("print('test')")

            try:
                # Make directory read-only
                os.chmod(readonly_dir, 0o555)  # r-xr-xr-x
                os.chmod(test_file, 0o444)     # r--r--r--

                output_file = os.path.join(readonly_dir, "output.md")
                flattener = CodeFlattener(readonly_dir, output_file)

                # This should raise PermissionError when trying to write output
                with self.assertRaises(PermissionError):
                    flattener.flatten()
            finally:
                # Restore permissions to allow cleanup
                os.chmod(readonly_dir, 0o755)
                os.chmod(test_file, 0o644)
                shutil.rmtree(readonly_dir)

    def test_special_characters(self):
        """Test handling of files with special characters."""
        logger.info("Testing special characters handling")
        special_file = os.path.join(self.test_dir, 'test-!@#$%.py')

        with open(special_file, 'w') as f:
            f.write('print("test")')

        flattener = CodeFlattener(self.test_dir, self.output_file)
        flattener.flatten()

        with open(self.output_file, 'r') as f:
            content = f.read()

        self.assertIn('test-!@#$%.py', content)

    def test_gitignore_patterns(self):
        """Test proper handling of .gitignore patterns."""
        logger.info("Testing .gitignore patterns")
        flattener = CodeFlattener(self.test_dir, self.output_file)
        flattener.flatten()

        with open(self.output_file, 'r') as f:
            content = f.read()

        # Check that ignored files are not included
        self.assertNotIn('debug.log', content)
        self.assertNotIn('.env', content)
        self.assertNotIn('__pycache__', content)
        self.assertNotIn('temp/', content)

    test_results = {'passed': 0, 'failed': 0, 'errors': 0}

    def run(self, result=None):
        """Override run to track test results"""
        test_method = getattr(self, self._testMethodName)
        try:
            super().run(result)
            if getattr(result, 'failures', []) and test_method.__name__ in str(result.failures[-1]):
                self.__class__.test_results['failed'] += 1
            elif getattr(result, 'errors', []) and test_method.__name__ in str(result.errors[-1]):
                self.__class__.test_results['errors'] += 1
            else:
                self.__class__.test_results['passed'] += 1
        except:
            self.__class__.test_results['errors'] += 1
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean up logging."""
        logger.info("="*80)
        logger.info("Completed CodeFlattener test suite")

        # Log test summary
        logger.info("Test Summary:")
        total_tests = sum(cls.test_results.values())
        logger.info(f"Total tests run: {total_tests}")
        logger.info(f"Tests passed: {cls.test_results['passed']}")
        logger.info(f"Tests failed: {cls.test_results['failed']}")
        logger.info(f"Tests with errors: {cls.test_results['errors']}")
        logger.info("="*80)

        # Clean up log directory if empty
        if os.path.exists(log_dir) and not os.listdir(log_dir):
            os.rmdir(log_dir)
            logger.info("Removed empty log directory")

if __name__ == '__main__':
    unittest.main(verbosity=2)