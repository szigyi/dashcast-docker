"""
Run DashCast semi-persistently on a Chromecast while allowing other
Chromecast apps to work also by only launching when idle.
"""

from __future__ import print_function
import time
import os
import sys
import logging

import pychromecast
import pychromecast.controllers.dashcast as dashcast

print('DashCast')
print('Searching for Chromecasts...')

DASHBOARD_URL = os.getenv('DASHBOARD_URL', 'https://home-assistant.io')
DISPLAY_NAME = os.getenv('DISPLAY_NAME')
IGNORE_CEC = os.getenv('IGNORE_CEC') == 'True'

if IGNORE_CEC:
    print('Ignoring CEC for Chromecast', DISPLAY_NAME)
    pychromecast.IGNORE_CEC.append(DISPLAY_NAME)


if '--show-debug' in sys.argv:
    logging.basicConfig(level=logging.DEBUG)

class DashboardLauncher():

    def __init__(self, device, dashboard_url='https://home-assistant.io', dashboard_app_name='DashCast'):
        print('Attempting to launch dashboard on Chromecast', device.name, dashboard_url)

        self.device = device
        self.controller = dashcast.DashCastController()
        self.device.register_handler(self.controller)

        receiver_controller = device.socket_client.receiver_controller
        receiver_controller.register_status_listener(self)

        self.dashboard_url = dashboard_url
        self.dashboard_app_name = dashboard_app_name

        self.should_launch = False
        # Check status on init.
        receiver_controller.update_status()
        # Keep logic in main loop.
        while True:
            if self.should_launch:
                self.launch_dashboard()
            self.controller._socket_client.heartbeat_controller.is_expired()
            time.sleep(5)

    def new_cast_status(self, cast_status):
        """ Called when a new cast status has been received. """
        print('new_cast_status', self.device.name, cast_status)
        print('current_device_state', self.device)

        def should_launch():
            """ If the device is active, the dashboard is not already active, and no other app is active. """
            device_idle = self.is_device_idle()
            dashboard_active = self.is_dashboard_active()
            other_active = self.is_other_app_active()
            print('app_display_name', self.device.app_display_name)
            print('device_idle', device_idle, 'dashboard_active', dashboard_active, 'other_active', other_active)
            return (device_idle
                    and not dashboard_active
                    and not other_active)

        self.should_launch = should_launch()

    def is_device_idle(self):
        """ Returns if the the Chromecast is (probably) idle. """
        return (self.device.status is not None
                and self.device.app_display_name == 'Backdrop'
                and self.device.status.status_text == ''
                and self.device.status.is_stand_by
                and not self.device.status.is_active_input)

    def is_dashboard_active(self):
        """ Returns if the dashboard is (probably) visible. """
        return (self.device.status is not None
                and self.device.app_display_name == self.dashboard_app_name)

    def is_other_app_active(self):
        """ Returns if an app other than the dashboard or the Backdrop is (probably) visible. """
        return (self.device.status is not None
                and self.device.app_display_name not in ('Backdrop', self.dashboard_app_name))

    def launch_dashboard(self):
        print('launch_dashboard', self.device.name, self.dashboard_url)

        def callback(response):
            print('callback called', response)

        try:
            self.controller.load_url(self.dashboard_url, callback_function=callback)
        except Exception as e:
            print(e)
            pass

# Initial lookup for Chromecast.
casts = pychromecast.get_chromecasts()
if len(casts) == 0:
    print('No Devices Found')
    exit()

cast = next(cc for cc in casts if DISPLAY_NAME in (None, '') or cc.device.friendly_name == DISPLAY_NAME)

if not cast:
    print('Chromecast with name', DISPLAY_NAME, 'not found')
    exit()

DashboardLauncher(cast, dashboard_url=DASHBOARD_URL)
