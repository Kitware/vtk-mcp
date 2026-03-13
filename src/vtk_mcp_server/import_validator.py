"""VTK import statement validation.

Ported from vtkapi-mcp/vtkapi_mcp/validation/import_validator.py.
"""

import re
from typing import Any, Dict, List


def _extract_used_classes(code: str, available_classes: set) -> List[str]:
    """Extract all VTK class names that are actually used in the code."""
    used_classes = set()

    pattern1 = r'\b(vtk[A-Z]\w+)\s*\('
    for match in re.finditer(pattern1, code):
        used_classes.add(match.group(1))

    lines = code.split('\n')
    for line in lines:
        if 'import' in line:
            continue
        for match in re.finditer(r'\b(vtk[A-Z]\w+)', line):
            class_name = match.group(1)
            if class_name in available_classes:
                used_classes.add(class_name)

    return list(used_classes)


class ImportValidator:
    """Validates VTK import statements against a VTKAPIIndex."""

    def __init__(self, api_index) -> None:
        self.api = api_index

    def validate_import(
        self, import_statement: str, code_context: str = None
    ) -> Dict[str, Any]:
        """Validate if an import statement is correct.

        Accepts three styles:
        - import vtk (monolithic)
        - import vtkmodules.all as vtk (modular all-in-one)
        - from vtkmodules.XXX import ClassName (modular selective)

        Returns: {valid: bool, message: str, suggested: str}
        """
        import_statement = import_statement.strip()

        if import_statement == 'import vtk':
            return {
                'valid': True,
                'message': 'Monolithic VTK import (valid)',
                'suggested': None,
            }

        if import_statement == 'import vtkmodules.all as vtk':
            return {
                'valid': True,
                'message': 'Modular all-in-one VTK import (valid)',
                'suggested': None,
            }

        import_clean = import_statement.split('#')[0].strip()
        if import_clean.startswith('import vtkmodules.'):
            module_name = import_clean.replace('import ', '').strip()

            allowed_direct_imports = {
                'vtkmodules.vtkRenderingOpenGL2',
                'vtkmodules.vtkInteractionStyle',
                'vtkmodules.vtkRenderingFreeType',
                'vtkmodules.vtkRenderingVolumeOpenGL2',
            }

            if module_name in allowed_direct_imports:
                return {
                    'valid': True,
                    'message': 'Backend module import (valid - required for initialization)',
                    'suggested': None,
                }
            else:
                return {
                    'valid': False,
                    'message': (
                        f"INVALID: Direct module import not allowed.\n"
                        f"  Use 'from {module_name} import ClassName' instead.\n\n"
                        f"  SMALLEST CHANGE: Replace with proper from-import style"
                    ),
                    'suggested': f"from {module_name} import <ClassName>",
                }

        if 'from' in import_statement and 'import' in import_statement:
            return self._validate_from_import(import_statement, code_context)

        return {
            'valid': False,
            'message': "Could not parse import statement",
            'suggested': None,
        }

    def _validate_from_import(
        self, import_statement: str, code_context: str = None
    ) -> Dict[str, Any]:
        """Validate 'from X import Y' style imports."""
        parts = import_statement.split('import')
        if len(parts) != 2:
            return {
                'valid': False,
                'message': "Could not parse from-import statement",
                'suggested': None,
            }

        class_part = parts[1].strip()
        class_names = []
        if '(' in class_part:
            class_part = class_part.replace('(', '').replace(')', '')
        for name in class_part.split(','):
            class_names.append(name.strip())

        if not class_names:
            return {
                'valid': False,
                'message': "No classes found in import statement",
                'suggested': None,
            }

        module_part_from = parts[0].replace('from', '').strip()

        modules_to_delete = []
        modules_with_usage = []

        for class_name in class_names:
            full_name = f"{module_part_from}.{class_name}"
            possible_module = f"vtkmodules.{class_name}"

            if full_name in self.api.modules or possible_module in self.api.modules:
                if code_context:
                    used_classes = _extract_used_classes(
                        code_context, set(self.api.classes.keys())
                    )
                    module_classes = self.api.get_module_classes(possible_module)
                    classes_from_module = [c for c in used_classes if c in module_classes]

                    if classes_from_module:
                        modules_with_usage.append(
                            (class_name, possible_module, classes_from_module)
                        )
                    else:
                        modules_to_delete.append(class_name)

        if modules_to_delete or modules_with_usage:
            return self._format_module_import_error(
                import_statement, modules_to_delete, modules_with_usage
            )

        class_name = class_names[0]
        info = self.api.get_class_info(class_name)

        if not info:
            return {
                'valid': False,
                'message': (
                    f"INVALID: Class '{class_name}' not found in VTK API.\n"
                    f"  This class doesn't exist - likely a hallucination or typo.\n"
                    f"  SMALLEST CHANGE: Remove or replace with a real VTK class name"
                ),
                'suggested': "DELETE or replace with valid class name (smallest fix)",
            }

        correct_module = info['module']

        if module_part_from == correct_module:
            return {
                'valid': True,
                'message': "Import is correct",
                'suggested': None,
            }
        else:
            if module_part_from == 'vtkmodules.all':
                return {
                    'valid': True,
                    'message': (
                        f"Import is valid (though importing from specific module "
                        f"{correct_module} is preferred)"
                    ),
                    'suggested': None,
                }

            suggested = f"from {correct_module} import {class_part}"
            return {
                'valid': False,
                'message': (
                    f"import: INVALID: Incorrect module.\n"
                    f"  '{class_name}' is in '{correct_module}', not '{module_part_from}'\n\n"
                    f"  REPLACE THIS EXACT LINE:\n"
                    f"    {import_statement.strip()}\n"
                    f"  WITH:\n"
                    f"    {suggested}\n\n"
                    f"  REQUIRED: Change module from '{module_part_from}' to '{correct_module}'"
                ),
                'suggested': suggested,
            }

    def _format_module_import_error(
        self,
        import_statement: str,
        modules_to_delete: List[str],
        modules_with_usage: List[tuple],
    ) -> Dict[str, Any]:
        """Format error message for module import issues."""
        if modules_to_delete and not modules_with_usage:
            module_list = ', '.join(modules_to_delete)
            return {
                'valid': False,
                'message': (
                    f"INVALID: Cannot import modules this way.\n"
                    f"  These are MODULES, not classes: {module_list}\n\n"
                    f"  Your code does NOT use any classes from these modules.\n\n"
                    f"  SMALLEST CHANGE: DELETE this entire line (unused code):\n"
                    f"    {import_statement.strip()}\n"
                    f"  Deleting unused imports is smaller than trying to fix them."
                ),
                'suggested': "DELETE this line (smallest change for unused imports)",
            }
        elif modules_with_usage and not modules_to_delete:
            new_imports = []
            for mod_name, mod_path, classes in modules_with_usage:
                class_list = ', '.join(classes[:3])
                new_imports.append(f"from {mod_path} import {class_list}")

            suggested_imports = '\n'.join(new_imports)
            return {
                'valid': False,
                'message': (
                    f"INVALID: Cannot import modules this way.\n"
                    f"  These are MODULES, not classes.\n\n"
                    f"  Your code uses classes from these modules.\n\n"
                    f"  SMALLEST CHANGE: Replace with proper imports:\n"
                    f"    {suggested_imports}"
                ),
                'suggested': f"{suggested_imports} (smallest fix - just change the import)",
            }
        else:
            unused = ', '.join(modules_to_delete)
            used_info = []
            for mod_name, mod_path, classes in modules_with_usage:
                class_list = ', '.join(classes[:3])
                used_info.append(f"from {mod_path} import {class_list}")

            suggested_imports = '\n'.join(used_info)
            return {
                'valid': False,
                'message': (
                    f"INVALID: Cannot import modules this way.\n"
                    f"  These are MODULES, not classes.\n\n"
                    f"  NOT USED (delete): {unused}\n"
                    f"  USED (need proper import):\n\n"
                    f"  SMALLEST CHANGE: Replace this line with:\n"
                    f"    {suggested_imports}\n"
                    f"  (removes unused {unused}, fixes the rest)"
                ),
                'suggested': f"{suggested_imports} (smallest fix)",
            }
