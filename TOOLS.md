# vtk-mcp — MCP Tool Reference

25 tools in 5 groups.  Each group lists the delegating library.

---

## Class discovery — `vtk-knowledge`

Find classes by name, keyword, or module membership.

| Tool | What it does |
|---|---|
| `vtk_is_a_class(class_name)` | Returns true if the name is a known VTK class |
| `vtk_search_classes(query, limit)` | Substring search across all class names |
| `vtk_get_class_module(class_name)` | Returns the `vtkmodules.*` import path |
| `vtk_get_module_classes(module)` | Lists all classes in a given module |

---

## Class documentation — `vtk-knowledge`

Retrieve metadata about a specific class.

| Tool | What it does |
|---|---|
| `get_vtk_class_info_python(class_name)` | Full record: module, methods, role, datatypes, synopsis |
| `vtk_get_class_doc(class_name)` | Raw class docstring |
| `vtk_get_class_synopsis(class_name)` | One-sentence LLM-generated summary |
| `vtk_get_class_action_phrase(class_name)` | Short noun-phrase for the class's primary action |
| `vtk_get_class_role(class_name)` | Pipeline role: source, filter, mapper, output, utility, etc. |
| `vtk_get_class_input_datatype(class_name)` | Expected input data type (e.g. `vtkPolyData`) |
| `vtk_get_class_output_datatype(class_name)` | Produced output data type |
| `vtk_get_class_visibility(class_name)` | Score 0.0–1.0 for how often this class is used directly |
| `vtk_get_class_methods(class_name)` | All methods with signatures |
| `vtk_get_class_semantic_methods(class_name)` | Non-boilerplate methods only |

---

## Method documentation — `vtk-knowledge`

Drill into a specific method on a specific class.

| Tool | What it does |
|---|---|
| `vtk_get_method_info(class_name, method_name)` | Full method record: signatures + docstring |
| `vtk_get_method_doc(class_name, method_name)` | Docstring only |
| `vtk_get_method_signature(class_name, method_name)` | Canonical signature string only |

---

## Validation — `vtk-validate`

Check VTK Python code or imports for API mistakes.

| Tool | What it does |
|---|---|
| `validate_vtk_code(source)` | Full AST check: imports, constructors, methods, ordering, security — returns a `ValidationReport` |
| `vtk_validate_import(import_statement)` | Validates a single import line and suggests the correct module |

---

## Semantic search — `vtk-index` (Qdrant)

Retrieve relevant documentation or code by meaning, not by exact name.

| Tool | What it does |
|---|---|
| `vector_search_docs(query, k)` | Hybrid dense+BM25 search over documentation chunks |
| `vector_search_examples(query, k)` | Hybrid dense+BM25 search over VTK code example chunks |

---

## C++ documentation — vtk.org scraper (self-contained)

Live HTML scraping of the VTK C++ API docs.  No offline artifact required.

| Tool | What it does |
|---|---|
| `get_vtk_class_info_cpp(class_name)` | Fetches class info from vtk.org C++ docs |
| `search_vtk_classes_cpp(search_term)` | Searches class names in the C++ docs |

---

## Meta — `vtk-mcp` itself

| Tool | What it does |
|---|---|
| `vtk_version_info()` | Returns the loaded VTK version, class count, and which capabilities are enabled |
