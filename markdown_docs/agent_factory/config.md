## FunctionDef read_config(file_path)
**read_config**: The function of read_config is to load configuration settings from a specified YAML file.

**parameters**: The parameters of this Function.
· file_path: A string representing the path to the YAML configuration file. The default value is '../config/config.yaml'.

**Code Description**: The read_config function is designed to read configuration data from a YAML file. It takes a single parameter, file_path, which specifies the location of the configuration file. If no path is provided, it defaults to '../config/config.yaml'. The function opens the specified file in read mode and uses the yaml.safe_load method to parse the contents of the file into a Python dictionary. This dictionary, which contains the configuration settings, is then returned to the caller.

In the context of the project, the read_config function is called within the __init__ method of the BaseAgent class located in agent_factory/agent.py. When an instance of BaseAgent is created, the read_config function is invoked to load the configuration settings. The resulting configuration dictionary is stored in the instance variable self.config. Subsequently, specific configuration values are accessed, such as the default model name and the path to the prompt folder, which are used to initialize other components of the agent.

**Note**: It is important to ensure that the specified YAML file exists and is correctly formatted, as any issues with file access or parsing could lead to runtime errors.

**Output Example**: A possible appearance of the code's return value could be:
```yaml
{
  'default_model': 'gpt-4o-mini',
  'prompt_folder_path': '/path/to/prompts',
  ...
}
```
