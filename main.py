import os
import yaml
import argparse
from api import API
from config import Config
from doods import Doods

def main():
    parser = argparse.ArgumentParser(description='DOODS2 - Dedicated Open Object Detection Service')
    parser.add_argument('--config', '-c', help='Configuration File', default='config.yaml')
    parser.add_argument('action', nargs='?', help='Action: api=Start REST api', default='api')
    args = parser.parse_args()

    # Use environment, followed by arguments, followed by default config.yaml
    config_file = os.environ.get('CONFIG_FILE', args.config)

    # Load config file
    with open(config_file, 'r') as stream:
        try:
            config = Config(**yaml.safe_load(stream))
        except yaml.YAMLError as exc:
            print(exc)

    # Initialize doods
    doods = Doods(config.doods)

    if args.action == 'api':
        # Start the server
        api = API(config.server, doods)
        api.run()
    else:
        print('Unknown action: '+args.action)

if __name__ == "__main__":
    main()
