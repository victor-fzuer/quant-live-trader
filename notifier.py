import os
import requests

webhook = os.getenv("WECHAT_WEBHOOK")

def notify(content):
    data = {
        "msgtype": "text",
        "text": {"content": content}
    }
    requests.post(webhook, json=data)
