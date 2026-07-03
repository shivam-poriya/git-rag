from services.repo.chunking.splitters.py_splitter import (
    split_python_document,
)

from services.repo.chunking.splitters.js_family_splitter import (
    split_js_family_document,
)

from services.repo.chunking.splitters.java_splitter import (
    split_java_document,
)

from services.repo.chunking.splitters.markdown_splitter import (
    split_markdown_document,
)



#
# Thresholds
#

CODE_SPLIT_THRESHOLD = 5000

MARKDOWN_SPLIT_THRESHOLD = 3000

CONFIG_SPLIT_THRESHOLD = 2000

STATUS_PROCESSING = "processing"

STATUS_COMPLETED = "completed"

STATUS_FAILED = "failed"


#
# Extension Groups
#

PYTHON_EXTENSIONS = {
    ".py",
}

JS_FAMILY_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}

JAVA_EXTENSIONS = {
    ".java",
}

MARKDOWN_EXTENSIONS = {
    ".md",
    ".markdown",
}

CONFIG_EXTENSIONS = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
}


#
# Splitter Registry
#

SPLITTER_REGISTRY = {
    # Python
    ".py": split_python_document,
    ".pyi": split_python_document,

    # JS / TS
    ".js": split_js_family_document,
    ".jsx": split_js_family_document,
    ".ts": split_js_family_document,
    ".tsx": split_js_family_document,

    # Java
    ".java": split_java_document,

    # Markdown
    ".md": split_markdown_document,
    ".markdown": split_markdown_document,
}


#
# Language Registry
#

LANGUAGE_REGISTRY = {
    ".py": "python",
    ".pyi": "python",
    

    ".js": "javascript",
    ".jsx": "javascript",

    ".ts": "typescript",
    ".tsx": "typescript",

    ".java": "java",

    ".md": "markdown",
    ".markdown": "markdown",

    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",

    ".toml": "toml",
    ".ini": "ini",
}