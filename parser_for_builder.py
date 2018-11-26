import argparse
import subprocess
import re
import sys
import textwrap
import yaml

def config_value(config, path, default):
    branch = config
    path_list = path.split(".")
    for element in path_list:
        try:
            branch = branch[element]
        except(KeyError):
            if default:
                return default
            else:
                return None
    return branch

def run(command):
    print 'Executing: ' + command
    child = subprocess.Popen(command.split(),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    output = child.stdout.read()
    streamdata = child.communicate()[0]
    print output
    assert child.returncode == 0

def find(expr, line):
    return re.search(expr, line)

def find_first_in_file(expr, file):
    with open(file, 'r') as fh:
        for line in fh:
            match = find(expr, line)
            if match:
                return match

def load_config(file):
    with open(file) as read_file:
        config = load_yaml(read_file)
    return config

def load_yaml(read_file):
    yaml.add_constructor('!join', join_yaml_tag)
    try:
        return yaml.load(read_file)
    except yaml.YAMLError:
        print 'Yaml syntax error in {file}'.format(file=read_file.name)
        sys.exit(1)

def join_yaml_tag(loader, node):
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_path", help="path to config.yml")
    ### We are not using the credential and state files yet, but we will in next versions of code
    parser.add_argument("-s", "--secret_path", help="path to secret.yml")
    parser.add_argument("-i", "--instate", help="path to state input file", default=None)
    parser.add_argument("-o", "--outstate", help="path to state output file", default='state.yml')
    return parser.parse_args(args)

def validate_args(parser):
    if not parser.config_path:
        argparse.ArgumentParser().error(
            '''Missing required input to proceed...
            Please provide configuration file,
            use -h(--help) for more help''')
