#!/usr/bin/env python

import jinja2
import os
import pkgutil

from sonic_cli_gen.yang_parser import YangParser

class CliGenerator:
    """ SONiC CLI generator. This class provides public API
    for sonic-cli-gen python library. It can generate config,
    show, sonic-clear CLI plugins
    """

    def __init__(self):
        """ Initialize PackageManager. """

        self.loader = jinja2.FileSystemLoader(['/usr/share/sonic/templates/sonic-cli-gen/'])
        self.env = jinja2.Environment(loader=self.loader)

    def generate_cli_plugin(self, yang_model_name, cli_group, output_stream=None):
        """ Generate CLI plugin. """
        parser = YangParser(yang_model_name)
        yang_dict = parser.parse_yang_model()
        template = self.env.get_template(cli_group + '.py.j2')

        if output_stream is None:
            plugin_name = yang_module_name.replace('-', '_')
            plugin_path = get_cli_plugin_path(cli_group, plugin_name + '_auto.py')
            with open(plugin_path, 'w') as output_stream:
                output_stream.write(template.render(yang_dict))
        else:
            output_stream.write(template.render(yang_dict))

def get_cli_plugin_path(command, plugin_name):
    pkg_loader = pkgutil.get_loader(f'{command}.plugins')
    if pkg_loader is None:
        raise PackageManagerError(f'Failed to get plugins path for {command} CLI')
    plugins_pkg_path = os.path.dirname(pkg_loader.path)

    return os.path.join(plugins_pkg_path, plugin_name)