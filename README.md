
````markdown
# ⚡ Real-Time Matching Engine with Flask + Socket.IO + ngrok

A high-performance order matching engine built with Python, Flask, and Flask-SocketIO, supporting limit, market, IOC, FOK, and stop orders. Designed to simulate a trading exchange with real-time WebSocket updates and RESTful APIs.

---

## 🚀 Features

- 📈 Limit / Market / IOC / FOK / Stop order support
- ⚖️ Price-time priority matching
- 🧠 Order book per symbol with depth view
- 🧮 Maker/Taker fee calculation
- 🔄 Real-time trade execution via WebSocket
- 💾 Persistent state save/load (optional)
- 🌐 Optional public exposure via ngrok

---

## 📦 Requirements

- Python 3.8+
- Flask
- Flask-SocketIO
- pyngrok
- sortedcontainers

Install dependencies:

```bash
pip install flask flask-socketio pyngrok sortedcontainers
````

---

## 🛠️ How to Run

### ▶️ Step 1: Start the Server

```bash
python your_script_name.py
```

You’ll see something like:

```
Running on http://127.0.0.1:5000
```

Optional (for external access): enable ngrok by uncommenting this section:

```python
from pyngrok import ngrok
public_url = ngrok.connect(5000).public_url
print(f" * Public URL: {public_url}")
```

---

## 📤 Submit an Order

### REST Endpoint

```bash
POST /order
```

### Sample cURL:

```bash
curl -X POST http://127.0.0.1:5000/order \
-H "Content-Type: application/json" \
-d '{
  "symbol": "BTCUSD",
  "order_type": "limit",
  "side": "buy",
  "quantity": 1,
  "price": 30000
}'
```

### Response:

```json
{
  "order_id": "b9f0d49e-xxxx",
  "status": "partial",
  "trades": []
}
```

---

## 📊 View Order Book

```bash
GET /orderbook/<symbol>
```

Example:

```bash
curl http://127.0.0.1:5000/orderbook/BTCUSD
```

Response:

```json
{
  "symbol": "BTCUSD",
  "bids": [{"price": 30000, "quantity": 1}],
  "asks": [],
  "timestamp": "2025-07-08T10:00:00Z"
}
```

---

## 🔔 Real-Time WebSocket Events

WebSocket Events:

* `trade_execution`: Emits whenever a trade is matched
* `orderbook_update`: Emits on `subscribe_orderbook` event

```javascript
const socket = io("http://127.0.0.1:5000");

socket.on("connect", () => {
  socket.emit("subscribe_orderbook", { symbol: "BTCUSD" });
});

socket.on("orderbook_update", (data) => {
  console.log("Orderbook:", data);
});

socket.on("trade_execution", (trade) => {
  console.log("Trade executed:", trade);
});
```

---

## 📂 File Structure

```
.
├── matching_engine.py   # Main file
├── orderbook_state.json # (Optional) Saved orderbook state
├── matching_engine.log  # Trade logs
└── README.md
```

---

## ✅ What to Do After Running the `.py` File

1. **Run `python matching_engine.py`** to start the server.
2. **Open terminal or Postman** and place orders via the `/order` endpoint.
3. **View orderbook** with `/orderbook/<symbol>` (e.g., BTCUSD).
4. (Optional) **Connect via frontend or WebSocket client** to receive real-time events.
5. (Optional) **Use `ngrok`** to share server via a public URL.

---

## 🧠 Future Improvements

* Add market order support
* Improve persistence (load from `orderbook_state.json`)
* Add cancellation/modification APIs
* Web UI dashboard
* Unit tests & benchmarking

---

## 📃 License

MIT License

---

## ✨ Author

Kunal Kumar | [GitHub](https://github.com/kunal14901)

```
