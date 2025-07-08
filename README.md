# Real-Time Matching Engine with Flask + Socket.IO + ngrok

A high-performance order matching engine built with Python, Flask, and Flask-SocketIO, supporting Limit, Market, IOC, FOK, and Stop orders.

---

## Features

- Supports **Limit**, **Market**, **IOC**, **FOK**, and **Stop** orders
- Price-time priority matching
- Order book per symbol with depth view
- Maker/Taker fee calculation
- Real-time trade execution via WebSocket
- Optional persistent state save/load
- Optional public exposure via ngrok

---

## Requirements

- Python 3.8+
- Flask
- Flask-SocketIO
- pyngrok
- sortedcontainers

Install dependencies using:

```bash
pip install flask flask-socketio pyngrok sortedcontainers
```

---

## 🛠️ How to Run

### Step 1: Start the Server

```bash
python your_script_name.py
```

Output:

```
Running on http://127.0.0.1:5000
```

To expose publicly via ngrok, **uncomment** the following lines:

```python
from pyngrok import ngrok
public_url = ngrok.connect(5000).public_url
print(f" * Public URL: {public_url}")
```

---

## 📤 Submit an Order

### POST `/order`

Sample request:

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

Sample response:

```json
{
  "order_id": "b9f0d49e-xxxx",
  "status": "partial",
  "trades": []
}
```

---

## 📊 View Order Book

### GET `/orderbook/<symbol>`

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

## 📡 WebSocket Usage

Events:

* `subscribe_orderbook` → Subscribes to live updates for a symbol
* `orderbook_update` → Receives order book changes
* `trade_execution` → Receives executed trade details

Example (JavaScript):

```javascript
const socket = io("http://127.0.0.1:5000");

socket.on("connect", () => {
  socket.emit("subscribe_orderbook", { symbol: "BTCUSD" });
});

socket.on("orderbook_update", (data) => {
  console.log("Orderbook update:", data);
});

socket.on("trade_execution", (trade) => {
  console.log("Trade executed:", trade);
});
```

---

## 🧾 File Structure

```
.
├── matching_engine.py         # Main server file
├── orderbook_state.json       # (Optional) Saved orderbook state
├── matching_engine.log        # Log of trades
└── README.md
```

---

## ✅ After Running the Python File

1. **Start server**: `python matching_engine.py`
2. **Place orders**: via `curl`, Postman, or custom frontend
3. **Track state**: use `/orderbook/<symbol>` and WebSocket
4. (Optional) **Enable ngrok** for public access
5. (Optional) **Build frontend UI** to visualize the book and trades

---

## 🧠 Future Enhancements

* ❌ Order cancelation/modification support
* 📉 Historical charting
* 🌍 REST + WebSocket API docs (Swagger/OpenAPI)
* 📈 Web-based live dashboard
* 📦 Docker support

---

## 🧑‍💻 Author

**Kunal Kumar**  
📧 [iknir1234@gmail.com](mailto:iknir1234@gmail.com)  
🌐 [github.com/iknir1234](https://github.com/kunal14901)

---

## 📃 License

**MIT License**

```text
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
```
