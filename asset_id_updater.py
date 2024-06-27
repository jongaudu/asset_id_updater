from csclient import EventingCSClient
import time
import json

cp = EventingCSClient('asset_id_updater')

def check_uptime(uptime_req):
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
        time.sleep(1)
        client_usage_enabled = cp.get('status/client_usage/enabled')

    cp.log('Client data usage enabled, continuing...')

    return client_usage_enabled


def get_sdk_params():
    cp.log('Getting SDK parameters...')
    include_ip_found = False
    sdk_params = False
    sdk_appdata = cp.get('config/system/sdk/appdata')
   
    for item in sdk_appdata:
        if item['name'].upper() == 'INCLUDE_IP':
            cp.log(f'{item["name"]} parameter found, continuing...')
            sdk_params = item['value']
            include_ip_found = True
            break

    if not include_ip_found:
        cp.log('INCLUDE_IP parameter not found, adding parameter...')
        sdk_appdata.append({'name': 'INCLUDE_IP', 'value': 'False'})
        cp.put('config/system/sdk/appdata', sdk_appdata)
        cp.log('INCLUDE_IP parameter added, continuing...')

    return sdk_params


def get_client_data(sdk_params):
    cp.log('Getting client data...')
    client_usage = cp.get('status/client_usage/stats')

    def sdk_params_true(client_usage):
        client_list = []
        for client in client_usage:
            client_list.append({client['name']: client['ip']})
        
        return client_list


    def sdk_params_false(client_usage):
        client_list = []
        for client in client_usage:
            client_list.append(client['name'])

        return client_list
    

    def client_data_length_validate(client_list, sdk_params):
        client_data = json.dumps({'total clients': len(client_list), 'clients': client_list})
        
        if len(client_data) > 255 and sdk_params.upper() == 'TRUE':
            reduced_client_list = sdk_params_false(client_list)
            reduced_client_data = json.dumps({'total clients': len(reduced_client_list), 'clients': reduced_client_list})
            
            if len(reduced_client_data) > 255:
                client_data = json.dumps({f'total clients: {len(client_list)}. See system log for details.'})
            else:
                client_data = reduced_client_data
        
        return client_data


    if sdk_params.upper() == 'TRUE':
        cp.log('include_ip parameter set to True, including IP addresses in client data...')
        client_list = sdk_params_true(client_usage)
    else:
        cp.log('include_ip parameter set to False, not including IP addresses in client data...')
        client_list = sdk_params_false(client_usage)

    client_data = client_data_length_validate(client_list, sdk_params)
    cp.log(f'Client data: {client_data}')

    return client_data


def set_asset_id(client_data):
    asset_id = cp.get('config/system/asset_id')

    if asset_id == client_data:
        cp.log('Router asset_id unchanged, continuing...')
    else:
        cp.log('Setting asset_id for router...')
        cp.put('config/system/asset_id', client_data)
        cp.log('Router asset_id set, continuing...')


if __name__ == '__main__':
    cp.log('Starting asset_id_updater script...')
    sleep_timer = 300
    uptime_req = 120
    check_uptime(uptime_req=uptime_req)
    client_usage_enabled = enable_client_usage()

    while client_usage_enabled:
        sdk_params = get_sdk_params()
        client_data = get_client_data(sdk_params=sdk_params)
        set_asset_id(client_data=client_data)
        cp.log(f'Sleeping for {sleep_timer} seconds...')
        time.sleep(sleep_timer)
