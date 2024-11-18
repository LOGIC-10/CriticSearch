## FunctionDef read_config(file_path)
**read_config**: The function of read_config is to read configuration data from a YAML file and return it as a Python dictionary.

**parameters**: The parameters of this Function.
· file_path: A string representing the path to the YAML configuration file. The default value is '../config/config.yaml'.

**Code Description**: The read_config function is designed to load configuration settings from a specified YAML file. It takes one optional parameter, file_path, which defaults to '../config/config.yaml' if not provided. The function opens the specified file in read mode ('r') and utilizes the yaml.safe_load method to parse the contents of the file. This method safely loads the YAML data into a Python dictionary, which is then returned by the function. The use of safe_load is important as it prevents the execution of arbitrary code that could be present in the YAML file, thereby enhancing security.

**Note**: It is essential to ensure that the specified YAML file exists at the given path; otherwise, a FileNotFoundError will be raised. Additionally, the function requires the PyYAML library to be installed in the environment to function correctly.

**Output Example**: A possible appearance of the code's return value could be:
{
  'database': {
    'host': 'localhost',
    'port': 5432,
    'user': 'admin',
    'password': 'secret'
  },
  'logging': {
    'level': 'debug',
    'file': 'app.log'
  }
}
