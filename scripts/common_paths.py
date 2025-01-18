import os

def get_toolkit_dirs():

    base_dir = os.getcwd()

    dirs = {
        'base_dir': base_dir,
        'input_dir': os.path.join(base_dir, '_input'),
        'output_dir': os.path.join(base_dir, '_output'),
    }

    return dirs
