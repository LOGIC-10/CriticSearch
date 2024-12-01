# critic_search/config.py
from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["settings.yaml", ".secrets.yaml"],
)

# from dynaconf import inspect_settings
# print(inspect_settings(settings))
