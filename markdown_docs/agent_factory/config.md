## FunctionDef read_config(file_path)
**read_config**: The function of read_config is to read a configuration file in YAML format and return its contents as a Python dictionary.

**parameters**: The parameters of this Function.
· file_path: A string representing the path to the configuration file. The default value is '../config/config.yaml'.

**Code Description**: The read_config function opens a specified YAML configuration file in read mode and utilizes the `yaml.safe_load` method to parse the contents of the file into a Python dictionary. This function is designed to facilitate the loading of configuration settings that can be used throughout the application. The default file path points to a configuration file located in a 'config' directory, which is one level up from the current directory.

In the context of its usage, the read_config function is called within the __init__ method of the Manager class located in the agent_factory/manager.py file. During the initialization of a Manager object, the read_config function is invoked without any arguments, which means it will use the default file path to load the configuration settings. The resulting dictionary is stored in the `self.config` attribute of the Manager instance. This configuration dictionary is then used to retrieve various settings, such as the default model and the path to the prompt folder, which are essential for the operation of the Manager class.

**Note**: It is important to ensure that the specified configuration file exists at the given path and is formatted correctly in YAML. Failure to do so will result in an error when attempting to open or parse the file.

**Output Example**: A possible appearance of the code's return value could be:
```python
{
    'default_model': 'gpt-4o-mini',
    'prompt_folder_path': '/path/to/prompts',
    'other_setting': 'value'
}
```
