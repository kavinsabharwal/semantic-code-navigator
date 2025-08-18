import unittest
import os
import tempfile
import shutil
from pathlib import Path

from src.code_ingestion import CodeIngestionEngine

class TestCodeIngestion(unittest.TestCase):

    def setUp(self):
        self.engine = CodeIngestionEngine()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_discover_code_files(self):
        """Test that code file discovery works correctly."""
        # Create a dummy file structure
        (Path(self.temp_dir) / "src").mkdir()
        (Path(self.temp_dir) / "src" / "main.py").touch()
        (Path(self.temp_dir) / "src" / "utils.js").touch()
        (Path(self.temp_dir) / "README.md").touch()
        (Path(self.temp_dir) / "node_modules").mkdir()
        (Path(self.temp_dir) / "node_modules" / "lib.js").touch()

        extensions = ["py", "js"]
        exclude_dirs = ["node_modules"]

        found_files = self.engine.discover_code_files(self.temp_dir, extensions, exclude_dirs)

        # Convert to relative paths for comparison
        relative_files = sorted([os.path.relpath(p, self.temp_dir) for p in found_files])

        self.assertEqual(len(relative_files), 2)
        self.assertIn("src/main.py", relative_files)
        self.assertIn("src/utils.js", relative_files)
        self.assertNotIn("README.md", relative_files)
        self.assertNotIn("node_modules/lib.js", relative_files)

    def test_extract_python_function_fallback(self):
        """Test fallback extraction for a simple Python function."""
        code = "def hello_world():\n    print('Hello, World!')"
        chunks = self.engine.extract_functions_fallback(code, "python")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['name'], "hello_world")
        self.assertIn("print('Hello, World!')", chunks[0]['content'])

    def test_extract_python_class_fallback(self):
        """Test fallback extraction for a Python class."""
        code = "class MyClass:\n    def my_method(self):\n        return 1"
        chunks = self.engine.extract_functions_fallback(code, "python")
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]['name'], "MyClass")
        self.assertEqual(chunks[1]['name'], "my_method")

    def test_extract_nested_python_function_fallback(self):
        """Test fallback extraction for nested Python functions."""
        code = "def outer_func():\n    def inner_func():\n        pass"
        chunks = self.engine.extract_functions_fallback(code, "python")
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]['name'], "outer_func")
        self.assertEqual(chunks[1]['name'], "inner_func")

    def test_extract_js_function_fallback(self):
        """Test fallback extraction for a simple JavaScript function."""
        code = "function greet() {\n    return 'Hello';\n}"
        chunks = self.engine.extract_functions_fallback(code, "javascript")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['name'], "greet")
        self.assertIn("return 'Hello';", chunks[0]['content'])

    def test_fallback_chunking(self):
        """Test that plain code is chunked when no functions are found."""
        code = "console.log('line 1');\n" * 60  # 60 lines of code
        chunks = self.engine.extract_functions_fallback(code, "javascript")
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0]['name'], "chunk_1")
        self.assertEqual(chunks[1]['name'], "chunk_2")

if __name__ == '__main__':
    unittest.main()
