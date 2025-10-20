# A simple RAG for VTK 

This project creates a database out of the existing Python examples of VTK and allows to ask questions related to VTK.

## Set up
1. By default it uses the OpenAI API. Make sure you  get an API key and set
your environmental variable appropriately. To use other an other model see
[below](#supported-llm-models).

2. Get the code of the vtk-examples. We will use this to generate our database.

```bash
git clone https://gitlab.kitware.com/vtk/vtk-examples 
```

3. Create a virtual environment and install the dependencies.

```bash
git clone https://gitlab.kitware.com/vtk/vtk-examples 
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

4. Populate the database. This is required only once or if you want to experiment with a different embedding function.
It will take some time depending on the hardware you are using.

```bash
python populate_db.py --dir ./vtk-examples/src/Python 
```

5. Now ask your question !

```bash
$ python chat.py --database ./db/codesage-codesage-large-v2
User: How to read a vti file
 To read a VTK image data file (.vti), you can use the `vtkXMLImageDataReader` class. Here is a basic example:

import vtk

# Create a reader for your vti file
reader = vtk.vtkXMLImageDataReader()
reader.SetFileName('your_file.vti')
reader.Update()

# The output of reader.GetOutput() is your vtkImageData object
image_data = reader.GetOutput()

In this code, replace `'your_file.vti'` with the path to your .vti file. The
`reader.Update()` call is necessary to actually perform the reading operation.
After this, you can use `reader.GetOutput()` to get the `vtkImageData` object
that was read from the file.

References:
https://examples.vtk.org/site/Python/Medical/GenerateModelsFromLabels
https://examples.vtk.org/site/Python/ImageData/WriteReadVtkImageData
...
```

### Supported LLM models
`chat.py` uses by default "gpt-4" model to switch to a different one pass the name of the model via the `--model=<model name>` parameter.
Currently supported models:
- OpenAI models. See exact model names [here](https://platform.openai.com/docs/models#current-model-aliases). To use them you need an OpenAI API [key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key).
- Anthropic models. See exact names [here](https://docs.anthropic.com/en/docs/about-claude/models/all-models#model-names). To use them you need an Anthropic API [key](https://docs.anthropic.com/en/api/getting-started#accessing-the-api).
- Models supported by the Ollama framework. To use these models make sure you have [ollama](https://github.com/ollama/ollama) installed and that it
  is running in another terminal (via `ollama serve`) and the you have already
  pulled the model you want to use (via `ollama pull <model-name>`). You can find available models [here](https://ollama.com/). 
