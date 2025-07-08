

!pip install flask flask-socketio sortedcontainers pyngrok

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from pyngrok import ngrok
import uuid
import time
import threading
import json
from datetime import datetime
from sortedcontainers import SortedDict
from collections import defaultdict, deque

# NGROK_AUTHTOKEN = "cr_2yMpEmINwgLP600fafsNY9HB0IL"
# ngrok.set_auth_token(NGROK_AUTHTOKEN)

import uuid
import time
import threading
import json
import logging
from datetime import datetime
from sortedcontainers import SortedDict
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit

# === Configuration === #
LOG_FILE = 'matching_engine.log'
MAX_ORDER_BOOK_DEPTH = 10
MAKER_FEE = 0.002  # 0.2%
TAKER_FEE = 0.003   # 0.3%

# Initialize logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# === Data Structures === #
class Order:
    def __init__(self, symbol, order_type, side, quantity, price=None, stop_price=None):
        self.order_id = str(uuid.uuid4())
        self.symbol = symbol
        self.order_type = order_type.lower()
        self.side = side.lower()
        self.quantity = float(quantity)
        self.price = float(price) if price else None
        self.stop_price = float(stop_price) if stop_price else None
        self.timestamp = time.time()
        self.is_active = True

    def __lt__(self, other):
        return self.timestamp < other.timestamp

class OrderBook:
    def __init__(self):
        self.bids = SortedDict()  # Price -> deque of orders
        self.asks = SortedDict()
        self.stop_orders = []
        self.bbo_lock = threading.Lock()
        self._best_bid = None
        self._best_ask = None

    @property
    def best_bid(self):
        with self.bbo_lock:
            return self._best_bid

    @property
    def best_ask(self):
        with self.bbo_lock:
            return self._best_ask

    def update_bbo(self):
        with self.bbo_lock:
            self._best_bid = self.bids.keys()[-1] if self.bids else None
            self._best_ask = self.asks.keys()[0] if self.asks else None

    def add_order(self, order):
        book = self.bids if order.side == 'buy' else self.asks
        price = order.price

        if price not in book:
            book[price] = deque()
        book[price].append(order)
        self.update_bbo()

    def remove_order(self, price, side, order_id):
        book = self.bids if side == 'buy' else self.asks
        if price in book:
            orders = book[price]
            for idx, o in enumerate(orders):
                if o.order_id == order_id:
                    del orders[idx]
                    if not orders:
                        del book[price]
                    self.update_bbo()
                    return True
        return False

    def get_depth(self, depth=MAX_ORDER_BOOK_DEPTH):
        bids = [(price, sum(o.quantity for o in orders))
               for price, orders in self.bids.items()[-depth:]]
        asks = [(price, sum(o.quantity for o in orders))
               for price, orders in self.asks.items()[:depth]]
        return bids, asks

# === Matching Engine Core === #
class MatchingEngine:
    def __init__(self):
        self.books = defaultdict(OrderBook)
        self.lock = threading.Lock()
        self.trade_id = 0

    def process_order(self, order):
        if order.order_type in ['ioc', 'fok'] and not self.check_immediate_execution(order):
            return []

        trades = []
        book = self.books[order.symbol]
        qty_remaining = order.quantity

        if order.side == 'buy':
            price_test = lambda px: px <= order.price if order.price else True
            levels = book.asks.keys()
        else:
            price_test = lambda px: px >= order.price if order.price else True
            levels = reversed(book.bids.keys())

        for px in levels:
            if not price_test(px):
                break
            if order.order_type == 'fok' and qty_remaining > 0:
                break

            while book.asks[px] if order.side == 'buy' else book.bids[px]:
                match_orders = book.asks[px] if order.side == 'buy' else book.bids[px]
                match_order = match_orders[0]

                trade_qty = min(qty_remaining, match_order.quantity)
                qty_remaining -= trade_qty
                match_order.quantity -= trade_qty

                # Generate trade report
                trade = self.create_trade_report(order, match_order, trade_qty, px)
                trades.append(trade)
                self.emit_trade(trade)

                # Remove filled orders
                if match_order.quantity == 0:
                    match_orders.popleft()
                    if not match_orders:
                        del (book.asks if order.side == 'buy' else book.bids)[px]
                        book.update_bbo()

                if qty_remaining == 0:
                    break

        # Handle remaining quantity
        if qty_remaining > 0:
            if order.order_type == 'limit':
                book.add_order(order)
            elif order.order_type == 'stop':
                book.stop_orders.append(order)

        return trades

    def check_immediate_execution(self, order):
        book = self.books[order.symbol]
        if order.order_type == 'fok':
            available = sum(o.quantity for px in self.get_relevant_prices(order)
                           for o in self.get_order_queue(book, order.side, px))
            return available >= order.quantity
        return True

    def create_trade_report(self, taker_order, maker_order, qty, px):
        self.trade_id += 1
        return {
            "trade_id": self.trade_id,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "symbol": taker_order.symbol,
            "price": px,
            "quantity": qty,
            "aggressor_side": taker_order.side,
            "maker_order_id": maker_order.order_id,
            "taker_order_id": taker_order.order_id,
            "maker_fee": qty * MAKER_FEE,
            "taker_fee": qty * TAKER_FEE
        }

    def emit_trade(self, trade):
        socketio.emit('trade_execution', trade)
        logging.info(f"Trade executed: {trade}")

    def handle_order(self, data):
        try:
            order = Order(
                symbol=data['symbol'],
                order_type=data['order_type'],
                side=data['side'],
                quantity=data['quantity'],
                price=data.get('price'),
                stop_price=data.get('stop_price')
            )

            with self.lock:
                trades = self.process_order(order)

            return {
                "order_id": order.order_id,
                "status": "filled" if len(trades) > 0 else "partial",
                "trades": trades
            }, 200

        except Exception as e:
            logging.error(f"Order error: {str(e)}")
            return {"error": str(e)}, 400

# === API Endpoints === #
engine = MatchingEngine()

@app.route('/order', methods=['POST'])
def submit_order():
    data = request.get_json()
    response, status = engine.handle_order(data)
    return jsonify(response), status

@app.route('/orderbook/<symbol>', methods=['GET'])
def get_orderbook(symbol):
    book = engine.books.get(symbol)
    if not book:
        return jsonify({"error": "Symbol not found"}), 404

    bids, asks = book.get_depth()
    return jsonify({
        "symbol": symbol,
        "bids": [{"price": p, "quantity": q} for p, q in bids],
        "asks": [{"price": p, "quantity": q} for p, q in asks],
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    })

# === WebSocket Handlers === #
@socketio.on('connect')
def handle_connect():
    logging.info("Client connected")

@socketio.on('subscribe_orderbook')
def handle_orderbook_subscription(data):
    symbol = data.get('symbol')
    book = engine.books.get(symbol)
    if book:
        bids, asks = book.get_depth()
        emit('orderbook_update', {
            "symbol": symbol,
            "bids": bids,
            "asks": asks
        })

# === Persistence === #
def save_state():
    state = {
        symbol: {
            "bids": [(p, [o.__dict__ for o in q]) for p, q in book.bids.items()],
            "asks": [(p, [o.__dict__ for o in q]) for p, q in book.asks.items()],
            "stops": [o.__dict__ for o in book.stop_orders]
        }
        for symbol, book in engine.books.items()
    }
    with open('orderbook_state.json', 'w') as f:
        json.dump(state, f)

def load_state():
    try:
        with open('orderbook_state.json', 'r') as f:
            state = json.load(f)
            for symbol, book_state in state.items():
                book = OrderBook()
                # Rebuild order book
                # ... (implementation omitted for brevity)
                engine.books[symbol] = book
    except FileNotFoundError:
        pass

# if __name__ == '__main__':
#     !rm -rf /root/.ngrok2/  # Clean previous config
#     public_url = ngrok.connect(5000).public_url
#     print(f" * Public URL: {public_url}")
#     socketio.run(app, host='0.0.0.0', port=5000,
#                 debug=False, use_reloader=False,
#                 allow_unsafe_werkzeug=True)
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000,
                debug=False, use_reloader=False,
                allow_unsafe_werkzeug=True)