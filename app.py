from flask import Flask, request, jsonify
import os
import threading
import uuid

app = Flask(__name__)

BRIDGE_KEY = os.environ.get("BRIDGE_KEY")

orders = []
lock = threading.Lock()


def authorized():
    return (
        BRIDGE_KEY
        and request.headers.get("X-Bridge-Key") == BRIDGE_KEY
    )


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "ok": True,
        "service": "VoidCraft Rank API",
        "status": "online"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "status": "healthy"
    })


# سایت سفارش جدید را اینجا ارسال می‌کند
@app.route("/create", methods=["POST"])
def create_order():
    if not authorized():
        return jsonify({
            "ok": False,
            "error": "Access denied"
        }), 403

    data = request.get_json(silent=True) or {}

    username = str(data.get("minecraft_username", "")).strip()
    rank = str(data.get("rank_name", "")).strip()
    amount = data.get("amount")
    website_order_id = data.get("website_order_id")

    if not username:
        return jsonify({
            "ok": False,
            "error": "minecraft_username is required"
        }), 400

    if not rank:
        return jsonify({
            "ok": False,
            "error": "rank_name is required"
        }), 400

    with lock:
        # جلوگیری از ثبت دوباره یک سفارش سایت
        if website_order_id is not None:
            for old_order in orders:
                if old_order.get("website_order_id") == website_order_id:
                    return jsonify({
                        "ok": True,
                        "duplicate": True,
                        "order": old_order
                    })

        order = {
            "id": str(uuid.uuid4()),
            "website_order_id": website_order_id,
            "minecraft_username": username,
            "rank_name": rank,
            "amount": amount,
            "status": "paid",
            "error": None
        }

        orders.append(order)

    return jsonify({
        "ok": True,
        "order": order
    }), 201


# Bridge سفارش‌های پرداخت‌شده را می‌گیرد
@app.route("/queue", methods=["GET"])
def queue():
    if not authorized():
        return jsonify({
            "ok": False,
            "error": "Access denied"
        }), 403

    with lock:
        pending = [
            order for order in orders
            if order["status"] == "paid"
        ]

    return jsonify({
        "ok": True,
        "orders": pending
    })


# Bridge نتیجه اجرای LuckPerms را اعلام می‌کند
@app.route("/complete", methods=["POST"])
def complete():
    if not authorized():
        return jsonify({
            "ok": False,
            "error": "Access denied"
        }), 403

    data = request.get_json(silent=True) or {}

    order_id = str(data.get("order_id", "")).strip()
    success = bool(data.get("success"))
    error = str(data.get("error", "")).strip()

    if not order_id:
        return jsonify({
            "ok": False,
            "error": "order_id is required"
        }), 400

    with lock:
        for order in orders:
            if str(order["id"]) == order_id:

                if success:
                    order["status"] = "completed"
                    order["error"] = None
                else:
                    order["status"] = "paid"
                    order["error"] = error or "Unknown error"

                return jsonify({
                    "ok": True,
                    "order": order
                })

    return jsonify({
        "ok": False,
        "error": "Order not found"
    }), 404


# مشاهده یک سفارش برای مدیریت/بررسی
@app.route("/order/<order_id>", methods=["GET"])
def get_order(order_id):
    if not authorized():
        return jsonify({
            "ok": False,
            "error": "Access denied"
        }), 403

    with lock:
        for order in orders:
            if str(order["id"]) == str(order_id):
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
    app.run(
        host="0.0.0.0",
        port=port
    )
