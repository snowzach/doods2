import os
import yaml
import argparse
import logging
from api import API
from mqtt import MQTT
from config import Config
from doods import Doods

# Allows you to pass a flattened dict into an unflattened one for things like
# Hass.IO that only allows config a single level deep for some reason.
def unflatten_dict(d):
    ret = {}
    def sub_unflatten_dict(subd, keys, value):
        if len(keys) > 0:
            key = keys[0]
            if not key in subd:
                subd[key] = {}
            subd[key] = sub_unflatten_dict(subd[key], keys[1:], value)
            return subd
        else:
            return value

    for path, val in d.items():
        keys = path.split(".")
        key = keys[0]
        if not key in ret:
            ret[key] = {}
        ret[key] = sub_unflatten_dict(ret[key], keys[1:], val)

    return ret

def main():
    parser = argparse.ArgumentParser(description='DOODS2 - Dedicated Open Object Detection Service')
    parser.add_argument('--config', '-c', help='Configuration File', default='config.yaml')
    parser.add_argument('action', nargs='?', help='Action: api=Start REST api, mqtt=Start MQTT forwarder', default='api')
    args = parser.parse_args()

    # Use environment, followed by arguments, followed by default config.yaml
    config_file = os.environ.get('CONFIG_FILE', args.config)

    # Load config file
    with open(config_file, 'r') as stream:
        try:
            config = Config(**unflatten_dict(yaml.safe_load(stream)))
        except yaml.YAMLError as exc:
            print(exc)

    # Setup logging
    level = logging.getLevelName(config.logger.level.upper())
    logger = logging.getLogger("doods")
    logger.propagate = False
    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Initialize doods
    doods = Doods(config.doods)

    if args.action == 'api':
        # Start the server
        api = API(config.server, doods)
        api.run()
    elif args.action == 'mqtt':
        # Start the server
        mqtt = MQTT(config.mqtt, doods, metrics_server_config=config.server)
        mqtt.run()
    else:
        print('Unknown action: '+args.action)

if __name__ == "__main__":
    main()
