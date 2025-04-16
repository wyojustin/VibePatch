# Vibe Patches

Vibe Patches is a Python source file patching tool that applies incremental modifications to code blocks. It supports patching for:

- Standalone functions
- Methods within classes
- Entire class definitions
- Spyder-style cells (delimited by `#%%` markers)

## Features

- **AST-Based Parsing:**  
  Accurately extracts code blocks for functions, methods, classes, and Spyder cells using Python's `ast` module.
- **Flexible Patch Application:**  
  If the target block does not exist, new code is appended or inserted into the appropriate location.
- **Backup & Revert:**  
  Before applying any patch, a sequential backup is created in a dedicated subdirectory (`VibeBackups`) with automatic retention of up to 100 backups.
- **User-Friendly Interface:**  
  A simple tkinter-based GUI allows for file opening, patch selection (via dropdown), patch editing, and output logging.
- **Command-Line Support:**  
  Easily launch the tool with a file argument (e.g., `python vibe_patch.py my_file.py`).

## File Structure
VibePatch/
├── docs
│   └── specification.html
├── LICENSE
├── README.md
├── tests
│   └── sample_vibe_test.py
└── vibe_patch.py

## Getting Started

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/<username>/vibe-patches.git
   cd vibe-patches
