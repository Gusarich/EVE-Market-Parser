import requests
import random
import json
import time


def get_items(ids):
    req = requests.get(
        'https://api.evemarketer.com/ec/marketstat/json?typeid=' + ','.join([str(id) for id in ids]))
    items = req.json()
    items = {
        items[j]['buy']['forQuery']['types'][0]: {
            'sell': items[j]['sell']['fivePercent'],
            'buy': items[j]['buy']['fivePercent'],
            'volume': min(items[j]['buy']['volume'], items[j]['sell']['volume'])
        } for j in range(len(items))
    }
    items = {
        k: v for k, v in items.items() if v['volume'] > 0
    }
    return items


def parse(ids):
    result = {}
    for i in range(0, len(ids), 200):
        items = get_items(ids[i:i + 200])
        result.update(items)
    return result


def get_path(system1, system2):
    if system1 == system2:
        return 0, 0.5

    url = f'https://evemaps.dotlan.net/route/{system1}:{system2}'.replace(
        ' ', '_')
    req = requests.get(url)
    html = req.text
    try:
        table = html.split('<h2>Route: ')[1].split('</table>')[0]
        jumps = table.count('<tr') - 1
        secs = [
            float(i.split('">')[0].split('="')[1]) for i in table.split('<td align="right"><span class=')[1:]
        ]
    except Exception as e:
        print(e)
        return None

    return jumps, min(secs)


def filter_items(items, min_cap=1e6, min_profit=1.5):
    return {
        k: v for k, v in items.items() if (
            v['volume'] * v['buy'] >= min_cap and
            v['buy'] / v['sell'] >= min_profit
        )
    }


def get_item_detail(id):
    try:
        req = requests.get(
            f'https://evemarketer.com/api/v1/markets/types/{id}?language=en')
        res = req.json()
        name = res['type']['name']
        cargo = res['type']['volume']
        buy_price = res['buy_stats']['five_percent'] * 0.9
        sell_price = res['sell_stats']['five_percent'] * 1.1

        total_buy_quantity = total_sell_quantity = 0
        total_buy_cap = total_sell_cap = 0
        buy_cap_by_system = {}
        sell_cap_by_system = {}

        for order in res['buy']:
            if order['price'] <= buy_price:
                break
            if not order['station']['name']:
                continue
            total_buy_cap += order['volume_remain'] * order['price']
            total_buy_quantity += order['volume_remain']
            system = order['station']['name'].split(' - ')[0]
            if system[-1] == ')':
                system = system[:system.rindex(' ')]
            if ' ' in system:
                system = system[:system.rindex(' ')]
            if system not in buy_cap_by_system:
                buy_cap_by_system[system] = 0
            buy_cap_by_system[system] += order['volume_remain'] * \
                order['price']

        for order in res['sell']:
            if order['price'] >= sell_price:
                break
            if not order['station']['name']:
                continue
            total_sell_cap += order['volume_remain'] * order['price']
            total_sell_quantity += order['volume_remain']
            system = order['station']['name'].split(' - ')[0]
            if system[-1] == ')':
                system = system[:system.rindex(' ')]
            if ' ' in system:
                system = system[:system.rindex(' ')]
            if system not in sell_cap_by_system:
                sell_cap_by_system[system] = 0
            sell_cap_by_system[system] += order['volume_remain'] * \
                order['price']

        if min(total_buy_quantity, total_sell_quantity) <= 0:
            return None
        avg_buy_price = total_buy_cap / total_buy_quantity
        avg_sell_price = total_sell_cap / total_sell_quantity

        random_buy_systems = set()
        random_sell_systems = set()
        for i in range(3):
            rand = random.random() * total_buy_cap
            psum = 0
            for k, v in buy_cap_by_system.items():
                psum += v
                if psum >= rand:
                    random_buy_systems.add(k)
                    break
        for i in range(3):
            rand = random.random() * total_sell_cap
            psum = 0
            for k, v in sell_cap_by_system.items():
                psum += v
                if psum >= rand:
                    random_sell_systems.add(k)
                    break

        total_jumps = total_paths = 0
        lowest_secs = []

        for buy_system in random_buy_systems:
            for sell_system in random_sell_systems:
                path = get_path(buy_system, sell_system)
                if path is None:
                    continue
                total_paths += 1
                total_jumps += path[0]
                lowest_secs.append(path[1])

        if total_paths <= 0:
            return None

        avg_jumps = total_jumps / total_paths
        avg_lowest_sec = sum(lowest_secs) / len(lowest_secs)

        return [
            name,
            cargo,
            total_buy_cap,
            total_sell_cap,
            avg_buy_price,
            avg_sell_price,
            avg_jumps,
            avg_lowest_sec
        ]

    except Exception as e:
        print(e)
        return None


def format_number(n):
    if n >= 1e12:
        return f'{n / 1e12:.2f}T'
    if n >= 1e9:
        return f'{n / 1e9:.2f}B'
    if n >= 1e6:
        return f'{n / 1e6:.2f}M'
    if n >= 1e3:
        return f'{n / 1e3:.2f}K'
    return f'{n:.2f}'


def update_data():
    with open('items.txt', 'r') as f:
        items = [int(id) for id in f.read().split(',')]

    p = parse(items)
    p = filter_items(p, min_cap=1e7, min_profit=1.1)

    print(f'Parsing {len(p)} items...')

    result = {
        'items': []
    }

    for id, item in p.items():
        print(id, end='\r')

        details = get_item_detail(id)

        if details is None:
            continue

        if min(details[2], details[3]) < 1e7:
            continue

        result['items'].append([id] + details)

    result['lastUpdate'] = time.time()

    with open('data.json', 'w') as f:
        f.write(json.dumps(result))


if __name__ == '__main__':
    while True:
        update_data()
        print('Success!')
