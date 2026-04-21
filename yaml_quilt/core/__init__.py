import yaml
import yaml_quilt.core.parser.config_parser as config_parser


def stitch(file_path: str, directory: str, Loader, variables=None):
    """Read a YAML file, process it with inheritance rules, and return the complete YAML data as dict or list."""
    if variables is None:
        variables = {}

    yaml_data = {}
    try:
        with open(file_path, 'r') as file:
            if Loader == yaml.FullLoader:
                yaml_data = yaml.full_load(file)
            elif Loader == yaml.SafeLoader:
                yaml_data = yaml.safe_load(file)
            elif Loader == yaml.Loader:
                yaml_data = yaml.load(file, Loader=Loader)
    except Exception as e:
        print(f"Error reading YAML file '{file_path}': {e}")
        return None

    yaml_data = config_parser.process_root_yaml(
        yaml_data=yaml_data,
        directory=directory,
        injected_variables=variables,
        loader=Loader,
        file_path=file_path)
    return yaml_data
