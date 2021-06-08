import os
import sys
from glob import glob

base_path = os.path.dirname(os.path.realpath(__file__)) + '/../../'
module_paths = []

for module_path in glob(base_path + '/*'):
    sys.path.append(module_path)
    module_paths.append(module_path)


# export environment for usage in subprocess
os.environ['PYTHONPATH'] = os.getenv('PYTHONPATH', '') + ':' + (':'.join(module_paths))
os.putenv('PYTHONPATH', os.environ['PYTHONPATH'])
