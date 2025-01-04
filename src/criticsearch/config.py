from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["settings.yaml", ".secrets.yaml"],
    envvar_prefix=False,
    ignore_unknown_envvars=True,
)

# from dynaconf import inspect_settings
# print(inspect_settings(settings))
