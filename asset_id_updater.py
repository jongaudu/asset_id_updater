from csclient import EventingCSClient
import time

cp = EventingCSClient('asset_id_updater')

def check_uptime():
    uptime_req = 120

    uptime  = int(cp.get('status/system/uptime'))
    cp.log(f'Current uptime: {uptime} seconds')

    if uptime < uptime_req:
        cp.log(f'Sleeping for {uptime_req - uptime} seconds')  
        time.sleep(uptime_req - uptime)
    
    cp.log('Uptime check passed, continuing...')


def enable_client_usage():
    client_usage_enabled = cp.get('status/client_usage/enabled')

    while not client_usage_enabled:
        cp.log('Enabling client data usage...')
        cp.put('config/stats/client_usage/enabled', True)
        time.sleep(5)
        client_usage_enabled = cp.get('status/client_usage/enabled')

    cp.log('Client data usage enabled, continuing...')

    return client_usage_enabled


def get_client_data():
    cp.log('Getting client data...')
    client_usage_data = cp.get('status/client_usage/stats')
    client_usage_list = []

    for client in client_usage_data:
        client_usage_list.append({client['mac']: client['name']})

    lan_client_data = cp.get('status/lan/clients')
    lan_client_list = []
    for client in lan_client_data:
        lan_client_list.append(client['mac'])
    
    wlan_client_data = cp.get('status/wlan/clients')
    wlan_client_list = []
    for client in wlan_client_data:
        wlan_client_list.append(client['mac'])
    
    merged_mac_list = list(set(lan_client_list + wlan_client_list))

    client_name_list = []
    for client in merged_mac_list:
        for item in client_usage_data:
            if client in item.values():
                client_name_list.append(item['name'])

    client_name_list = list(set(client_name_list))

    return client_name_list


def update_asset_id(client_data):
    sleep_timer = 300

    current_asset_id = cp.get('config/system/asset_id')
    new_asset_id = f'total clients: {len(client_data)}, clients: {client_data}'

    if len(new_asset_id) > 255:
        new_asset_id = f'total clients: {len(client_data)}. See system log for details.'
        cp.log(f'Client data exceeds 255 characters. Total clients: {len(client_data)}, clients: {client_data}')
        cp.log('Setting asset_id for router...')
        cp.put('config/system/asset_id', new_asset_id)
        cp.log('Router asset_id set, continuing...')
    
    elif current_asset_id == new_asset_id:
        cp.log('Router asset_id unchanged, continuing...')

    else:
        cp.log('Setting asset_id for router...')
        cp.put('config/system/asset_id', new_asset_id)
        cp.log('Router asset_id set, continuing...')

    cp.log(f'Sleeping for {sleep_timer} seconds...')
    time.sleep(sleep_timer)


if __name__ == '__main__':
    cp.log('Starting LAN client alert tool')
    check_uptime()
    enable_client_usage()
    while True: 
        client_data = get_client_data()
        update_asset_id(client_data)
