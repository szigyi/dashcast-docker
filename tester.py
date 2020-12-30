import time
import os
import pychromecast
import pychromecast.controllers.dashcast as dashcast


DASHBOARD_URL = os.getenv('DASHBOARD_URL')
DISPLAY_NAME = os.getenv('DISPLAY_NAME')

print('List chromecasts on the network, but don\'t connect')
services, browser = pychromecast.discovery.discover_chromecasts()

print('Discover and connect to chromecasts named:', DISPLAY_NAME)
chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[DISPLAY_NAME])
[cc.device.friendly_name for cc in chromecasts]
print('Found:', chromecasts)
cast = chromecasts[0]
print('Selected:', cast)


print('Start worker thread and wait for cast device to be ready')
cast.wait()
controller = dashcast.DashCastController()
cast.register_handler(controller)
print()
time.sleep(1)
print(cast.device.friendly_name, ':', cast.status.status_text)
print()
print(cast.media_controller.status)
print()

if not cast.is_idle:
    print("Killing current running app")
    cast.quit_app()
    t = 5
    while cast.status.app_id is not None and t > 0:
        time.sleep(0.1)
        t = t - 0.1

time.sleep(1)


def callback(response):
    print()
    print('callback called:', response)
    # controller.load_url(DASHBOARD_URL)


print('Casting url:', DASHBOARD_URL)
controller.load_url(DASHBOARD_URL, force=True, reload_seconds=5, callback_function=callback)

print('Shut down discovery')
pychromecast.discovery.stop_discovery(browser)

