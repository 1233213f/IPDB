import os
import requests

# 从 GitHub Secrets 中获取 API URL 和其他敏感信息
api_url = os.environ.get('BESTPROXY')  # 将 BestIPAPI 更改为 BESTPROXY
api_token = os.environ.get('YMYCLOUDFLARE_API_TOKEN')
zone_id = os.environ.get('YMYZONE_ID')
telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
use_telegram_notification = True  # 设置为True以启用Telegram通知，设置为False以禁用

# 输出调试信息
print("api_url:", api_url)


# 检查是否成功获取敏感信息
if not (api_url and api_token and zone_id):
    print("YMY以下环境变量缺失:")
    if not api_url:
        print("BESTPROXY")  # 将 BestIPAPI 更改为 BESTPROXY
    if not api_token:
        print("YMYCLOUDFLARE_API_TOKEN")
    if not zone_id:
        print("YMYZONE_ID")
    if use_telegram_notification and not (telegram_bot_token and telegram_chat_id):
        if not telegram_bot_token:
            print("TELEGRAM_BOT_TOKEN")
        if not telegram_chat_id:
            print("TELEGRAM_CHAT_ID")
    print("请确保YMY环境变量已正确配置。")
    exit()

# DNS记录基本URL
base_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

# 构建API请求头
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# 函数用于发送Telegram通知
def send_telegram_notification(message):
    if use_telegram_notification:
        telegram_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        data = {
            "chat_id": telegram_chat_id,
            "text": message
        }
        response = requests.post(telegram_url, data=data)
        if response.status_code != 200:
            print("YMY无法发送Telegram通知。响应代码:", response.status_code)

# 删除所有'A'记录
print("\n正在删除所有 DNS 'A'记录")
response = requests.get(base_url, headers=headers)
if response.status_code == 200:
    data = response.json()
    for record in data["result"]:
        record_type = record["type"]
        if record_type == "A":  # 仅删除'A'记录
            delete_url = f"{base_url}/{record['id']}"
            response = requests.delete(delete_url, headers=headers)
            if response.status_code != 200:
                send_telegram_notification(f"YMY删除'A'记录时出错，HTTP响应代码：{response.status_code}")
                print("YMY删除'A'记录时出错，HTTP响应代码：", response.status_code)
                exit()
    print("已删除所有DNS 'A'记录")
else:
    send_telegram_notification(f"YMY无法获取DNS记录信息。响应代码: {response.status_code}")
    print("YMY无法获取DNS记录信息。响应代码:", response.status_code)
    exit()

# 发送GET请求到API获取反代IP
print("\n正在获取反代IP并DNS推送\n")
response = requests.get(api_url)  # 使用 BESTPROXY 替代 BestIPAPI

# 检查反代IP请求是否成功
if response.status_code == 200:
    ip_addresses = [ip.strip() for ip in response.text.split('\n') if ip.strip() and '.' in ip]
    for ip_address in ip_addresses:
        dns_record = {
            "type": "A",
            "name": "0101",
            "content": ip_address,
            "ttl": 60,
            "proxied": False
        }

        # 发送POST请求创建DNS记录
        response = requests.post(base_url, headers=headers, json=dns_record)

        if response.status_code != 200:
            send_telegram_notification(f"YMY创建DNS记录时出错，HTTP响应代码：{response.status_code}")
            print(f"YMY创建DNS记录时出错，HTTP响应代码：{response.status_code}")
            exit()
        else:
            print(f"Successfully updated,{ip_address}")
else:
    send_telegram_notification(f"YMY无法获取反代IP地址信息。响应代码: {response.status_code}")
    print("YMY无法获取反代IP地址信息。响应代码:", response.status_code)
    exit()
