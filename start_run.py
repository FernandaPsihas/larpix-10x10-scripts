'''
Loads specified configuration file and collects data until killed (cleanly exits)

Usage:
  python3 -i start_run.py --config_name <config file/dir> --controller_config <controller config file>

'''
import larpix
import larpix.io
import larpix.logger

import base
import load_config

import argparse
import json
from collections import defaultdict
import time
from datetime import datetime

_default_config_name=None
_default_controller_config=None
_default_runtime=30*60 # 30-min run files
_default_disabled_channels=[
    6,7,8,9,
    22,23,24,25,
    38,39,40,
    54,55,56,57
]

def main(config_name=_default_config_name, controller_config=_default_controller_config, runtime=_default_runtime, disabled_channels={None:_default_disabled_channels}.copy()):
    print('START RUN')
    # create controller
    c = None
    filename = "datalog_%s_PST_start_run.h5" % datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    if config_name is None:
        c = base.main(controller_config, logger=True, filename=filename)
    else:
        if controller_config is None:
            c = load_config.main(config_name, logger=True, filename=filename)
        else:
            c = load_config.main(config_name, controller_config, logger=True, filename=filename)

    # who added this and does it work without it???
    # lets try to configure it to actually get data :)

    # c.io.group_packets_by_io_group = False
    # c.io.double_send_packets = True
    #
    # chip_keys = list(c.chips.keys())
    #
    # channels = range(64)
    # disabled_channels={None:[]}
    # periodic_trigger_cycles = 100000
    # for chip_key, chip in [(chip_key, chip) for (chip_key, chip) in c.chips.items() if chip_key in chip_keys]:
    #     # Disable channels
    #     print(' disabling channels: ')
    #     # for disabled_key in disabled_channels:
    #     #     if disabled_key == chip_key or disabled_key == 'All':
    #     #         for disabled_channel in disabled_channels[disabled_key]:
    #     #             chip.config.csa_enable[disabled_channel] = 0
    #     #             print('     ', disabled_channel)
    #     print(' --- chip_key:', chip_key, ' --- ')
    #     chip.config.periodic_trigger_mask = [1] * 64
    #     chip.config.channel_mask = [1] * 64
    #     for channel in channels:
    #         chip.config.periodic_trigger_mask[channel] = 0
    #         chip.config.channel_mask[channel] = 0
    #     chip.config.periodic_trigger_cycles = periodic_trigger_cycles
    #     chip.config.enable_periodic_trigger = 1
    #     chip.config.enable_rolling_periodic_trigger = 1
    #     chip.config.enable_periodic_reset = 1
    #     chip.config.enable_rolling_periodic_reset = 0
    #     chip.config.enable_hit_veto = 0
    #     chip.config.periodic_reset_cycles = 4096
    #
    #     # write configuration
    #     registers = list(range(155, 163))  # periodic trigger mask
    #     c.write_configuration(chip_key, registers)
    #     c.write_configuration(chip_key, registers)
    #     registers = list(range(131, 139))  # channel mask
    #     c.write_configuration(chip_key, registers)
    #     c.write_configuration(chip_key, registers)
    #     registers = list(range(166, 170))  # periodic trigger cycles
    #     c.write_configuration(chip_key, registers)
    #     c.write_configuration(chip_key, registers)
    #     registers = [128]  # periodic trigger, reset, rolling trigger, hit veto
    #     c.write_configuration(chip_key, registers)
    #     c.write_configuration(chip_key, registers)
    #     c.write_configuration(chip_key, 'enable_rolling_periodic_reset')
    #     c.write_configuration(chip_key, 'enable_rolling_periodic_reset')
    #     c.write_configuration(chip_key, 'periodic_reset_cycles')
    #     c.write_configuration(chip_key, 'periodic_reset_cycles')
    #     c.write_configuration(chip_key, 'csa_enable')
    #     c.write_configuration(chip_key, 'csa_enable')
    #
    # for chip_key in c.chips:
    #     ok, diff = c.enforce_configuration(chip_key, timeout=0.01, n=10, n_verify=10)
    #     if not ok:
    #         print('config error', diff)
    # c.io.double_send_packets = True
    # c.logger.record_configs(list(c.chips.values()))

    # ok back to the already existing stuff

    while True:
        counter = 0
        start_time = time.time()
        last_time = start_time
        c.logger = larpix.logger.HDF5Logger()
        print('new run file at ',c.logger.filename)
        c.logger.enable()
        c.start_listening()
        while True:
            try:
                pkts, bs = c.read()
                counter += len(pkts)
                c.reads = []
                now = time.time()
                if now > start_time + runtime: break
                if now > last_time + 1:
                    print('average rate: {:0.2f}Hz\r'.format(counter/(time.time()-start_time)),end='')
                    last_time = now
            except:
                c.logger.flush()
                raise
        c.stop_listening()
        c.read()
        c.logger.flush()

    print('END RUN')
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_name', default=_default_config_name, type=str, help='''Directory or filename to load chip configurations from''')
    parser.add_argument('--controller_config', default=_default_controller_config, type=str, help='''Hydra network configuration file''')
    parser.add_argument('--runtime', default=_default_runtime, type=float, help='''Time duration before flushing remaining data to disk and initiating a new run (in seconds) (default=%(default)s)''')
    args = parser.parse_args()
    c = main(**vars(args))
