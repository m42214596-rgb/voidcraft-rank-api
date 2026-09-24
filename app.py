from flask import Flask, request, jsonify
import os

app = Flask(__name__)

BRIDGE_KEY = os.environ.get("BRIDGE_KEY")

orders = []


def authorized():
    return request.headers.get("X-Bridge-Key") == BRIDGE_KEY


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "ok": True,
        "service": "VoidCraft Rank API",
        "status": "online"
    })


@app.route("/queue", methods=["GET"])
def queue():
    if not authorized():
        return jsonify({
            "ok": False,
            "error": "Access denied"
        }), 403

    return jsonify({
        "ok": True,
        "orders": orders
    })


@app.route("/create", methods=["GET"])
def create():
    if not authorized():
        return jsonify({
            "ok": False,
            "error": "Access denied"
        }), 403

    username = request.args.get("username")
    rank = request.args.get("rank")
    amount = request.args.get("amount")

    if not username or not rank:
        return jsonify({
            "ok": False,
            "error": "username and rank are required"
        }), 400

    order_id = len(orders) + 1

    order = {
        "id": order_id,
        "minecraft_username": username,
        "rank_name": rank,
        "amount": amount,
        "status": "paid"
    }

    orders.append(order)

    return jsonify({
        "ok": True,
        "order": order
    })


@app.route("/complete", methods=["GET"])
def complete():
    if not authorized():
        return jsonify({
            "ok": False,
            "error": "Access denied"
        }), 403

    order_id = request.args.get("order_id")
    success = request.args.get("ok") == "1"
    error = request.args.get("error", "")

    for order in orders:
        if str(order["id"]) == str(order_id):

            if success:
                order["status"] = "completed"
                order["error"] = None
            else:
                order["status"] = "error"
                order["error"] = error or "Unknown error"

            return jsonify({
                "ok": True,
                "order": order
            })

    return jsonify({
        "ok": False,
        "error": "Order not found"
    }), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
