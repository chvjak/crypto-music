import time
import pygame.midi
import heapq
import matplotlib.pyplot as plt

class MinPQ:
    def __init__(self):
        self.data = []

    def enque(self, val):
        heapq.heappush(self.data, val)

    def deque(self):
        val = heapq.heappop(self.data)
        return val

class MaxPQ:
    def __init__(self):
        self.data = []

    def enque(self, val):
        heapq.heappush(self.data, -val)

    def deque(self):
        val = heapq.heappop(self.data)
        return -val



pygame.midi.init()
player = pygame.midi.Output(0)

coin = 'BTC'
instrument = 30            # 30 - guitar, 32 - bass, 118 - drums
channel = 1                 # 114 steel drum, 18 - synth (try 103), 116 - bass drum

player.set_instrument(instrument, channel )


import concurrent.futures

tpe = concurrent.futures.ThreadPoolExecutor(max_workers=5)


def play(note, duration):
    player.note_on(note, 127, channel)
    time.sleep(duration)
    player.note_off(note, 127, channel)


import requests
def ts_2_s(ts):
    dot_ix = ts.find('.')
    ts = ts[:dot_ix]
    ts = ts.replace('T', ' ')
    time_struct = time.strptime(ts, '%Y-%m-%d %H:%M:%S')
    return time.mktime(time_struct) # time in seconds

def get_trades(req={'currencyPair':'USDT-BTC'}):
    # {"success":true,"message":"","result":[{"Id":36624373,"TimeStamp":"2018-01-17T14:06:04.123","Quantity":0.03963298,"Price":9600.00000000,"Total":380.47660800,"FillType":"FILL","OrderType":"BUY"}]}
    ret = requests.get('https://bittrex.com/api/v1.1/public/getmarkethistory?market=' + str(req['currencyPair']))
    return ret.json()

def get_trades_bf(req={'currencyPair':'btcusd'}):
    # [{"timestamp":1516197748,"tid":170032058,"price":"9923.1","amount":"0.43462803","exchange":"bitfinex","type":"sell"}]
    ret = requests.get('https://api.bitfinex.com/v1/trades/' + str(req['currencyPair']))
    return ret.json()

last_id = None
while True:
    trades = get_trades({'currencyPair':'USDT-' + coin})['result']

    if last_id is not None:
        trades = [t for t in trades if t['Id'] > last_id]

    if len(trades) == 0:
        continue


    trades_start = ts_2_s(trades[-1]['TimeStamp'])
    trades_end = ts_2_s(trades[0]['TimeStamp'])

    trades_duration = trades_end - trades_start

    print('---------------------------------')
    print('{} {} trades to play in {} sec'.format(len(trades), coin, trades_duration))
    print('---------------------------------')

    quantities = [t['Quantity'] for t in trades]
    prices = [t['Price'] for t in trades]

    plt.figure(1)
    plt.subplot(211)
    plt.hist(quantities, bins=16)
    plt.subplot(212)
    plt.hist(prices, bins=21)
    plt.show()

    #exit()

    minq_price = MinPQ()
    maxq_price = MaxPQ()

    minq_quantity = MinPQ()
    maxq_quantity = MaxPQ()



    last_id = trades[0]['Id']
    for t in trades:
        quantity = float(t['Quantity'])
        price = float(t['Price'])

        minq_price.enque(price)
        maxq_price.enque(price)

        minq_quantity.enque(quantity)
        maxq_quantity.enque(quantity)

    min_price = minq_price.deque()

    maxq_price.deque()
    maxq_price.deque()
    max_price = maxq_price.deque()

    min_quantity = minq_quantity.deque()

    maxq_quantity.deque()
    maxq_quantity.deque()
    max_quantity = maxq_quantity.deque()

    notes = []
    for t in trades:
        price = min(max_price, float(t['Price']))
        quantity = min(max_quantity, float(t['Quantity']))
        time1 = ts_2_s(t['TimeStamp'])

        n = int((price - min_price) / (max_price - min_price) * 21)             # 14 - two octaves

        d = (quantity - min_quantity) / (max_quantity - min_quantity) * 16      # max 8 sec
        t = (time1 - trades_start) / 2.0                                          # 2 - speedup x2

        notes.insert(0, ([n, d, t]))

    t1 = time.time()
    base = 60
    for n, d, t in notes:
        print(n, d, t)

        while True:
            if time.time() - t1 >= t:
                break

        tpe.submit(play, base + n, d)

