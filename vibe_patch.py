import sys
import ast
import textwrap
from tkinter import filedialog, scrolledtext, messagebox
import tkinter as tk
import os
import re
import shutil

SCROLLTEXT_WIDTH = 132
SCROLLTEXT_HEIGHT = 30

class VibePatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VibePatch System")
        self.geometry("1000x1080")
        self.create_widgets()
        self.file_path = ""  # Initialize file_path variable

    def create_widgets(self):
        # Container for filename label and dropdown
        self.top_frame = tk.Frame(self)
        self.top_frame.pack(pady=5)

        self.filename_label = tk.Label(self.top_frame, text="No file loaded")
        self.filename_label.pack(side=tk.LEFT, padx=5)

        # Add an "Open" button here to load a file.
        self.open_button = tk.Button(self.top_frame, text="Open", command=self.open_file)
        self.open_button.pack(side=tk.LEFT, padx=5)

        # Create the StringVar with a trace for automatic loading
        self.load_var = tk.StringVar(self)
        self.load_var.trace("w", lambda *args: self.load_patch())
        self.load_dropdown = tk.OptionMenu(self.top_frame, self.load_var, "")
        self.load_dropdown.pack(side=tk.LEFT, padx=5)

        # Patch ScrollText
        self.patch_label = tk.Label(self, text="Patch")
        self.patch_label.pack(pady=5)
        self.patch_text = scrolledtext.ScrolledText(self, width=SCROLLTEXT_WIDTH, height=SCROLLTEXT_HEIGHT)
        self.patch_text.pack(pady=10)

        # Buttons
        self.buttons_frame = tk.Frame(self)
        self.buttons_frame.pack(pady=10)
        self.paste_button = tk.Button(self.buttons_frame, text="Paste", command=lambda: self.paste_text())
        self.paste_button.grid(row=0, column=0, padx=5)
        self.load_from_file_button = tk.Button(self.buttons_frame, text="Load from File", command=self.load_from_file)
        self.load_from_file_button.grid(row=0, column=1, padx=5)
        self.clear_button = tk.Button(self.buttons_frame, text="Clear", command=self.clear_text)
        self.clear_button.grid(row=0, column=2, padx=5)
        self.apply_patch_button = tk.Button(self.buttons_frame, text="Apply Patch", command=self.apply_patch)
        self.apply_patch_button.grid(row=0, column=3, padx=5)
        self.revert_button = tk.Button(self.buttons_frame, text="Revert", command=self.revert_file)
        self.revert_button.grid(row=0, column=4, padx=5)

        # Output ScrollText
        self.output_label = tk.Label(self, text="Output")
        self.output_label.pack(pady=5)
        self.output_text = scrolledtext.ScrolledText(self, width=SCROLLTEXT_WIDTH, height=SCROLLTEXT_HEIGHT)
        self.output_text.pack(pady=10)

    def open_file(self, file_path=None):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if file_path:
            self.file_path = file_path
            self.filename_label.config(text=f"File: {os.path.basename(self.file_path)}")
            self.update_dropdown(self.file_path)

    def XX_update_dropdown(self, file_path):
        # Get updated options from the file using self.parse_file only.
        options = self.parse_file(file_path)

        spyder_options = self.parse_spyder_cells(file_path)
        if spyder_options:
            options.extend(spyder_options)
        # Save the current selection, if any.
        current_selection = self.load_var.get()

        # Update the dropdown menu with new options.
        menu = self.load_dropdown["menu"]
        menu.delete(0, "end")
        for option in options:
            menu.add_command(label=option, command=tk._setit(self.load_var, option))

        # If the previous selection is still available, keep it; otherwise, select the first.
        if current_selection in options:
            self.load_var.set(current_selection)
        elif options:
            self.load_var.set(options[0])


    def not_update_dropdown(self, file_path):
        # Get updated options from the file (using your parse_file and parse_ipython_cells functions)
        options = self.parse_file(file_path)
        ipy_options = self.parse_ipython_cells(file_path)
        if ipy_options:
            options.extend(ipy_options)

        # Save the current selection, if any.
        current_selection = self.load_var.get()

        # Update the dropdown menu with new options.
        menu = self.load_dropdown["menu"]
        menu.delete(0, "end")
        for option in options:
            menu.add_command(label=option, command=tk._setit(self.load_var, option))

        # Set the load_var: if the current selection still exists, keep it; otherwise, choose the first.
        if current_selection in options:
            self.load_var.set(current_selection)
        elif options:
            self.load_var.set(options[0])


    def update_dropdown(self, file_path):
        # Parse the file via AST for functions, classes, and methods
        options = self.parse_file(file_path)
        # Also parse Spyder cells in the file
        spyder_options = self.parse_spyder_cells(file_path)
        if spyder_options:
            options.extend(spyder_options)
        menu = self.load_dropdown["menu"]
        menu.delete(0, "end")
        for option in options:
            menu.add_command(label=option, command=tk._setit(self.load_var, option))
        if options:
            self.load_var.set(options[0])

    def parse_file(self, file_path):
        """
        Parses the file using AST to generate labels for functions, classes, and methods.
        Methods are labeled as "Method: ClassName.method_name", classes as "Class: ClassName",
        and standalone functions as "Function: function_name".
        """
        options = []
        with open(file_path, 'r') as file:
            source = file.read()
        tree = ast.parse(source, filename=file_path)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                options.append(f"Function: {node.name}")
            elif isinstance(node, ast.ClassDef):
                options.append(f"Class: {node.name}")
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        options.append(f"Method: {node.name}.{child.name}")
        return options

    def parse_spyder_cells(self, file_path):
        """
        Parses a Python file for Spyder-style cells marked by lines starting with "#%%".
        Returns a list of labels in the format "Spyder Cell: X: descriptor" (if a descriptor is present)
        or "Spyder Cell: X" otherwise, where X is a zero-based index.
        """
        options = []
        with open(file_path, 'r') as file:
            lines = file.readlines()
        cell_markers = []  # Will store tuples: (line_index, descriptor)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#%%"):
                # Remove the marker and capture any descriptor that may follow
                match = re.match(r"#%%\s*(.*)", stripped)
                descriptor = match.group(1) if match and match.group(1) else ""
                cell_markers.append((i, descriptor))
        for idx, (line_index, descriptor) in enumerate(cell_markers):
            if descriptor:
                label = f"Spyder Cell: {idx}: {descriptor}"
            else:
                label = f"Spyder Cell: {idx}"
            options.append(label)
        return options

    def load_patch(self):
        selected_item = self.load_var.get()
        if selected_item:
            if selected_item.startswith("Function:"):
                func_name = selected_item.split(":", 1)[1].strip()
                self.load_function(self.file_path, func_name)
            elif selected_item.startswith("Method:"):
                label = selected_item.split(":", 1)[1].strip()
                try:
                    class_name, method_name = label.split(".", 1)
                except ValueError:
                    self.output_text.insert(tk.END, "Error: Incorrect method label format.\n")
                    return
                self.load_method(self.file_path, class_name, method_name)
            elif selected_item.startswith("Class:"):
                class_name = selected_item.split(":", 1)[1].strip()
                self.load_class(self.file_path, class_name)
            elif selected_item.startswith("Spyder Cell:"):
                # Expected format: "Spyder Cell: <number>" or "Spyder Cell: <number>: descriptor"
                parts = selected_item.split(":")
                try:
                    cell_number = int(parts[1].strip())
                except (IndexError, ValueError):
                    self.output_text.insert(tk.END, "Error: Incorrect Spyder cell label format.\n")
                    return
                self.load_spyder_cell(cell_number)

    def load_function(self, file_path, func_name):
        with open(file_path, 'r') as file:
            source = file.read()
        tree = ast.parse(source, filename=file_path)
        func_source = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                func_source = ast.get_source_segment(source, node)
                break
        self.patch_text.delete("1.0", tk.END)
        if func_source:
            self.patch_text.insert(tk.END, func_source)
        else:
            self.patch_text.insert(tk.END, f"Function {func_name} not found.")

    def load_method(self, file_path, class_name, method_name):
        """
        Loads a method's source code from the file and inserts it into the patch text area.
        This function preserves the exact original indentation and content, except that
        the first line (the "def" header) is modified to include the class name before the method name.

        For example, if the file contains:

                def method1(self):
                    ...

        then the patch area will display:

                def ClassA.method1(self):
                    ...

        (All indentation and newlines are preserved.)
        """
        with open(file_path, 'r') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
        method_source = None

        # Find the target method within the desired class.
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == method_name:
                        method_source = ast.get_source_segment(source, child)
                        break
            if method_source:
                break

        self.patch_text.delete("1.0", "end")
        if method_source:
            # Split by lines (preserving all characters).
            lines = method_source.splitlines()
            if lines:
                # Insert the class name into the header.
                # This regex finds the leading whitespace and "def " and then inserts ClassName.
                # For example, if lines[0] is "    def method1(self):"
                # it becomes "    def ClassA.method1(self):"
                new_header = re.sub(r"^(\s*def\s+)", r"\1" + f"{class_name}.", lines[0], count=1)
                lines[0] = new_header
            qualified_source = "\n".join(lines)
            self.patch_text.insert("end", qualified_source)
        else:
            self.patch_text.insert("end", f"Method {class_name}.{method_name} not found.")

    def load_class(self, file_path, class_name):
        with open(file_path, 'r') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
        class_source = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_source = ast.get_source_segment(source, node)
                break
        self.patch_text.delete("1.0", tk.END)
        if class_source:
            self.patch_text.insert(tk.END, class_source)
        else:
            self.patch_text.insert(tk.END, f"Class {class_name} not found.")

    def load_spyder_cell(self, cell_index):
        """
        Loads a Spyder-style cell from the file. Cells are determined by "#%%" markers.
        The cell content is loaded from the marker line up to (but not including) the next marker,
        or EOF.
        """
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
        marker_indices = [i for i, line in enumerate(lines) if line.strip().startswith("#%%")]
        if cell_index < 0 or cell_index >= len(marker_indices):
            self.patch_text.delete("1.0", tk.END)
            self.patch_text.insert(tk.END, f"Spyder Cell index {cell_index} out of range.")
            return
        start = marker_indices[cell_index]
        end = marker_indices[cell_index + 1] if (cell_index + 1) < len(marker_indices) else len(lines)
        cell_text = "".join(lines[start:end])
        self.patch_text.delete("1.0", tk.END)
        self.patch_text.insert(tk.END, cell_text)

    def paste_text(self):
        try:
            # Clear the patch text area
            self.patch_text.delete("1.0", tk.END)
            clipboard_text = self.clipboard_get()
            self.patch_text.insert(tk.END, clipboard_text)
        except tk.TclError:
            messagebox.showerror("Error", "Nothing to paste from clipboard.")

    def load_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                file_content = file.read()
                self.patch_text.delete("1.0", tk.END)
                self.patch_text.insert(tk.END, file_content)

    def clear_text(self):
        self.patch_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)

    def apply_patch(self):
        """
        Applies a patch to the currently loaded file using a stand-alone patch provided in the patch text area.

        The patch text must be fully self-contained; that is, its first nonblank line serves as a header that determines
        the patch type. The rules are:

          - If the patch text (after stripping leading whitespace) begins with "def ", it is interpreted as either a 
            function patch or a method patch:
              * If the header contains a dot (e.g. "def ClassA.method1(self):"), it is treated as a method patch.
              * Otherwise, it is treated as a function patch.
          - If the patch text begins with "class ", it is treated as a class patch.
          - If the patch text begins with "#%%", it is treated as a Spyder cell patch. (For Spyder cell patches, if the 
            header includes something like "#%% Cell 0: ..." the number (0 in this case) will be used as the cell index.

        This method:
          1. Reads the patch text from the patch area.
          2. Creates a backup of the current file.
          3. Examines the first nonblank line of the patch text to determine the type.
          4. Calls the corresponding patch routine (apply_function_patch, apply_method_patch, apply_class_patch, or apply_spyder_cell_patch)
             with the patch text.

        Note: The patch routines themselves assume that the patch text is in Vibe Patch format – i.e. it is a complete, stand-alone code
              snippet that can be directly inserted or used to replace the target area.
        """
        patch_content = self.patch_text.get("1.0", tk.END).strip()
        if not patch_content:
            self.output_text.insert("end", "No patch to apply.\n")
            return

        # Create a backup BEFORE applying any patch.
        self.backup_file(self.file_path)

        stripped_patch = patch_content.lstrip()

        # Case 1: Patch starts with "def "
        if stripped_patch.startswith("def "):
            # Get the first line of the patch text
            first_line = patch_content.splitlines()[0].lstrip()
            # This regex will capture a word that can include a dot (for method names) right after "def "
            m = re.match(r"^def\s+([\w\.]+)\s*\(", first_line)
            if m:
                full_name = m.group(1)
                if "." in full_name:
                    # Method patch. Expected format: "def ClassName.methodName(...):"
                    class_name, method_name = full_name.split(".", 1)
                    self.apply_method_patch(self.file_path, class_name, method_name, patch_content)
                else:
                    # Function patch.
                    self.apply_function_patch(self.file_path, full_name, patch_content)
            else:
                self.output_text.insert("end", "Invalid patch header for a function/method patch.\n")
        # Case 2: Patch starts with "class "
        elif stripped_patch.startswith("class "):
            m = re.match(r"^class\s+(\w+)", stripped_patch)
            if m:
                class_name = m.group(1)
                self.apply_class_patch(self.file_path, class_name, patch_content)
            else:
                self.output_text.insert("end", "Invalid patch header for a class patch.\n")
        # Case 3: Patch starts with "#%%" (Spyder cell patch)
        elif stripped_patch.startswith("#%%"):
            first_line = patch_content.splitlines()[0].strip()
            # Look for a cell index e.g. "#%% Cell 0:" (if provided)
            m = re.match(r"^#%%\s*Cell\s*(\d+)", first_line, re.IGNORECASE)
            if m:
                cell_index = int(m.group(1))
            else:
                cell_index = 0  # Default to cell 0 if not provided
            self.apply_spyder_cell_patch(cell_index, patch_content)
        else:
            self.output_text.insert("end", "Unknown patch type. The patch must start with 'def', 'class', or '#%%'.\n")

    def apply_function_patch(self, file_path, selected_func_name, patch_content):
        """
        Applies a patch to a standalone function. If a function with the name specified
        in the patch header is found, its block is replaced. Otherwise, the new function
        is inserted after the last previously defined function in the file (or appended to
        the end if no functions are found).
        """
        # Extract function name from patch header using regex.
        header_match = re.search(r"def\s+(\w+)\s*\(", patch_content)
        if header_match:
            patched_func_name = header_match.group(1)
        else:
            # Fall back if header is not found.
            patched_func_name = selected_func_name

        func_name = patched_func_name

        with open(file_path, 'r') as file:
            source = file.read()

        try:
            tree = ast.parse(source, filename=file_path)
        except Exception as e:
            self.output_text.insert(tk.END, f"Error parsing file: {e}\n")
            return

        target_node = None
        # Search for an existing function with the same name.
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                target_node = node
                break

        if target_node is None:
            # No function found; insert new function after the last defined function.
            lines = source.splitlines()

            # Find the last top-level function definition.
            last_func_node = None
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    last_func_node = node

            if last_func_node is not None:
                # Insert after the last function; end_lineno is 1-indexed.
                insertion_index = last_func_node.end_lineno
                # Ensure there's a blank line before the new function.
                new_lines = lines[:insertion_index] + ["", patch_content, ""] + lines[insertion_index:]
            else:
                # No functions found; append at the end.
                new_lines = lines + ["", patch_content, ""]

            new_source = "\n".join(new_lines) + "\n"
            with open(file_path, 'w') as file:
                file.write(new_source)

            self.output_text.insert(tk.END, f"New function {func_name} created successfully.\n")
            return

        # If the function exists, replace its existing code.
        start_line = target_node.lineno - 1
        end_line = target_node.end_lineno
        lines = source.splitlines()
        first_line = lines[start_line]
        indent = first_line[:len(first_line) - len(first_line.lstrip())]
        patched_lines = [indent + line if line.strip() else line for line in patch_content.splitlines()]
        new_lines = lines[:start_line] + patched_lines + lines[end_line:]
        new_source = "\n".join(new_lines) + "\n"

        with open(file_path, 'w') as file:
            file.write(new_source)

        self.output_text.insert(tk.END, f"Function {func_name} patched successfully.\n")

    def apply_method_patch(self, file_path, class_name, method_name, patch_content):
        """
        Replaces the target method's block in the file with the patch text.

        If the method exists in the specified class, its block (from AST's lineno to end_lineno)
        is replaced with the provided patch content.

        If the method is not found but the class exists, the new method is inserted at the end 
        of the class (after its last line) with a blank line preceding it. The patch_content 
        should be a complete Vibe Patch for a method, for example:

            def Greeter.say_hi(self):
                '''
                Says hi to the person.
                '''
                print("Hi there!")

        When inserting as a new method:
          - The header is reindented to be one level inside the class (e.g. 4 spaces),
            and any class qualification is removed so that it appears as "def say_hi(self):"
          - The method body is reindented so that each nonblank line is indented one level further (e.g. 8 spaces)
          - A blank line is inserted before the new method.

        Parameters:
          file_path: str - path to the file to patch.
          class_name: str - name of the target class.
          method_name: str - name of the target method.
          patch_content: str - the complete patch text.
        """
        # Remove any trailing newline characters.
        patch_content = patch_content.rstrip("\n")

        # Read the file.
        with open(file_path, 'r') as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=file_path)
        except Exception as e:
            self.output_text.insert(tk.END, f"Error parsing file: {e}\n")
            return

        # Get the file lines, preserving newlines.
        file_lines = source.splitlines(keepends=True)

        # Try to locate the target method.
        target_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for child in node.body:
                    if isinstance(child, ast.FunctionDef) and child.name == method_name:
                        target_node = child
                        break
            if target_node:
                break

        if target_node is None:
            # Method not found: attempt to insert as a new method in the target class.
            class_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    class_node = node
                    break
            if class_node is None:
                self.output_text.insert(tk.END, f"Class {class_name} not found.\n")
                return

            # Split the patch content into lines.
            patch_lines = patch_content.splitlines()
            if not patch_lines:
                self.output_text.insert(tk.END, "No patch content provided.\n")
                return

            # Process the header line: remove any class qualification.
            header_line = patch_lines[0].lstrip()
            m_header = re.match(r"^def\s+(?:(\w+)\.)?(?P<name>\w+)(.*)$", header_line)
            if not m_header:
                self.output_text.insert(tk.END, "Invalid method header in patch.\n")
                return
            unqualified_name = m_header.group("name")
            remainder = m_header.group(3)

            # Determine the class header indent.
            class_header_line = file_lines[class_node.lineno - 1]
            m_class_indent = re.match(r"^(\s*)", class_header_line)
            class_indent = m_class_indent.group(1) if m_class_indent else ""
            # New method header indent: one level inside the class (e.g., 4 spaces).
            method_indent = class_indent + "    "

            # Build the new header (without the class qualification).
            new_header = method_indent + "def " + unqualified_name + remainder

            # Process the body lines.
            patch_body_lines = patch_lines[1:]
            new_body_lines = []
            # The desired body indent is the method_indent plus one extra level (e.g. 4 spaces).
            desired_body_indent = method_indent + "    "
            for line in patch_body_lines:
                # Remove any leading whitespace from the patch body lines.
                content = line.lstrip()
                # Preserve lines that are exactly docstring delimiters.
                if content.strip() in ('"""', "'''"):
                    new_line = desired_body_indent + content.strip()
                else:
                    new_line = desired_body_indent + content
                new_body_lines.append(new_line)

            # Assemble the new method block.
            new_method_block = "\n".join([new_header] + new_body_lines) + "\n"
            # Insert a blank line before the new method block.
            new_method_block = "\n" + new_method_block

            # Insert the new method at the end of the class.
            # class_node.end_lineno is 1-indexed and indicates the last line of the class.
            insertion_index = class_node.end_lineno  # Insert after the class block.
            new_file_lines = file_lines[:insertion_index] + new_method_block.splitlines(keepends=True) + file_lines[insertion_index:]
            new_source = "".join(new_file_lines)

            with open(file_path, 'w') as f:
                f.write(new_source)
            self.output_text.insert(tk.END, f"New method {class_name}.{method_name} created successfully.\n")
            return

        # If the target method exists, replace its block.
        start_line = target_node.lineno - 1  # zero-indexed
        end_line = target_node.end_lineno     # exclusive
        patch_block_lines = patch_content.splitlines(keepends=True)
        new_file_lines = file_lines[:start_line] + patch_block_lines + file_lines[end_line:]
        new_source = "".join(new_file_lines)

        with open(file_path, 'w') as f:
            f.write(new_source)
        self.output_text.insert(tk.END, f"Method {class_name}.{method_name} patched successfully.\n")

    def backup_file(self, file_path):
        """
        Creates a backup copy of the given file in a subdirectory "VibeBackups" (located
        in the same directory as the file). The backup filename will be like:
            my_file_006.py  (for the 6th backup)
        After creating a backup, if there are more than 100 backups, the oldest are deleted.
        """
        dir_name = os.path.dirname(file_path)
        backup_dir = os.path.join(dir_name, "VibeBackups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        basename = os.path.basename(file_path)
        name, ext = os.path.splitext(basename)
        # Look for existing backups that match the pattern: name_###.py
        pattern = rf"^{re.escape(name)}_(\d{{3}}){re.escape(ext)}$"
        existing_backups = [f for f in os.listdir(backup_dir) if re.match(pattern, f)]
        # Determine next sequence number.
        if existing_backups:
            seq_numbers = [int(re.match(pattern, f).group(1)) for f in existing_backups]
            next_seq = max(seq_numbers) + 1
        else:
            next_seq = 1
        new_backup_name = f"{name}_{next_seq:03d}{ext}"
        new_backup_path = os.path.join(backup_dir, new_backup_name)
        shutil.copy2(file_path, new_backup_path)
        self.output_text.insert("end", f"Backup created: {new_backup_path}\n")

        # Delete older backups if more than 100 exist.
        existing_backups = sorted(existing_backups, key=lambda f: int(re.match(pattern, f).group(1)))
        while len(existing_backups) >= 100:
            file_to_delete = existing_backups.pop(0)
            os.remove(os.path.join(backup_dir, file_to_delete))
            self.output_text.insert("end", f"Deleted old backup: {file_to_delete}\n")

    def revert_file(self):
        """
        Reverts the currently loaded file to the newest backup.
        Looks for the backups in the VibeBackups directory (in the file's directory) and, if found,
        copies the newest backup over the file.
        """
        if not self.file_path:
            messagebox.showerror("Error", "No file loaded to revert.")
            return
        dir_name = os.path.dirname(self.file_path)
        backup_dir = os.path.join(dir_name, "VibeBackups")
        if not os.path.exists(backup_dir):
            messagebox.showerror("Error", "No backups found.")
            return

        basename = os.path.basename(self.file_path)
        name, ext = os.path.splitext(basename)
        pattern = rf"^{re.escape(name)}_(\d{{3}}){re.escape(ext)}$"
        backup_files = [f for f in os.listdir(backup_dir) if re.match(pattern, f)]
        if not backup_files:
            messagebox.showerror("Error", "No backups found.")
            return

        # Choose the backup with the highest sequence number.
        newest_backup = max(backup_files, key=lambda f: int(re.match(pattern, f).group(1)))
        newest_backup_path = os.path.join(backup_dir, newest_backup)
        if messagebox.askyesno("Revert", f"Are you sure you want to revert to backup {newest_backup}?"):
            shutil.copy2(newest_backup_path, self.file_path)
            self.output_text.insert("end", f"File reverted to backup: {newest_backup_path}\n")
            self.update_dropdown(self.file_path)

    def apply_class_patch(self, file_path, class_name, patch_content):
        with open(file_path, 'r') as file:
            source = file.read()
        tree = ast.parse(source, filename=file_path)
        target_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                target_node = node
                break

        if target_node is None:
            # No existing class—append new class definition at the end.
            with open(file_path, 'a') as file:
                file.write("\n" + patch_content + "\n")
            self.output_text.insert(tk.END, f"New class {class_name} created successfully.\n")
            return

        start_line = target_node.lineno - 1
        end_line = target_node.end_lineno
        lines = source.splitlines()
        first_line = lines[start_line]
        indent = first_line[:len(first_line) - len(first_line.lstrip())]
        patched_lines = [indent + line if line.strip() else line for line in patch_content.splitlines()]
        new_lines = lines[:start_line] + patched_lines + lines[end_line:]
        new_source = "\n".join(new_lines) + "\n"

        with open(file_path, 'w') as file:
            file.write(new_source)
        self.output_text.insert(tk.END, f"Class {class_name} patched successfully.\n")

    def apply_spyder_cell_patch(self, cell_index, patch_content):
        """
        Applies a patch to a Spyder-style cell in the file.

        The function first reads the file and locates all cell markers (lines starting with "#%%").
        It then determines the target cell based on the supplied cell_index.

        - If cell_index is within the current markers, it will replace the block for that cell.
        - If cell_index is out-of-range (i.e. greater than or equal to the number of cells),
          it will append the patch as a new cell at the end of the file.

        The patch content is assumed to be fully stand-alone (i.e. it includes a cell marker if desired).
        If the patch content (after stripping leading whitespace) does not start with "#%%",
        the original marker will be preserved for replacement.
        """
        # Read the file, preserving newlines.
        with open(self.file_path, 'r') as file:
            file_lines = file.readlines()  # Each line includes its terminating newline

        # Identify all cell marker indices.
        marker_indices = [i for i, line in enumerate(file_lines) if line.strip().startswith("#%%")]

        # Ensure the patch content ends with one newline.
        patch_content = patch_content.rstrip("\n") + "\n"

        # Determine if we are replacing an existing cell or appending a new one.
        if cell_index >= 0 and cell_index < len(marker_indices):
            # Replace an existing cell.
            start = marker_indices[cell_index]
            end = marker_indices[cell_index + 1] if (cell_index + 1) < len(marker_indices) else len(file_lines)

            # If the patch content does not start with a marker, preserve the original marker from the file.
            if not patch_content.lstrip().startswith("#%%"):
                original_marker = file_lines[start].rstrip("\n")
                new_cell_content = original_marker + "\n" + patch_content
            else:
                new_cell_content = patch_content

            new_cell_lines = new_cell_content.splitlines(keepends=True)
            new_file_lines = file_lines[:start] + new_cell_lines + file_lines[end:]
            new_source = "".join(new_file_lines)
            with open(self.file_path, 'w') as file:
                file.write(new_source)
            self.output_text.insert("end", f"Spyder Cell {cell_index} patched successfully.\n")
        else:
            # Append a new cell at the end of the file.
            # If the file does not end with a newline, add one.
            if not file_lines or not file_lines[-1].endswith("\n"):
                file_lines[-1] = file_lines[-1] + "\n"
            # Ensure the patch content starts with a cell marker.
            if not patch_content.lstrip().startswith("#%%"):
                # If not, prepend a default marker.
                new_cell_content = "#%% New Cell\n" + patch_content
            else:
                new_cell_content = patch_content
            new_cell_lines = new_cell_content.splitlines(keepends=True)
            new_source = "".join(file_lines) + "\n" + "".join(new_cell_lines)
            with open(self.file_path, 'w') as file:
                file.write(new_source)
            self.output_text.insert("end", f"New Spyder Cell appended successfully.\n")
        self.update_dropdown(self.file_path)

if __name__ == "__main__":
    app = VibePatchApp()
    # If a file argument is provided on the command line, open that file.
    if len(sys.argv) > 1:
        app.open_file(sys.argv[1])
    app.mainloop()

