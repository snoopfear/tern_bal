import requests
import pandas as pd
from datetime import datetime
import json
import schedule
import time

# ANSI escape codes for colors
GREEN = '\033[92m'
RESET = '\033[0m'

# Ваш API ключ и токен бота
API_KEY = ""
BOT_TOKEN = ""
CHAT_ID = ""

# URLs для сетей
NETWORK_URLS = {
    "arbitrum_sepolia": f"https://arb-sepolia.g.alchemy.com/v2/{API_KEY}",
    "optimism_sepolia": f"https://opt-sepolia.g.alchemy.com/v2/{API_KEY}",
    "base_sepolia": f"https://base-sepolia.g.alchemy.com/v2/{API_KEY}",
    "blast_sepolia": f"https://blast-sepolia.g.alchemy.com/v2/{API_KEY}",
}

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print(f"Message sent to chat {chat_id}: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message to Telegram: {e}")

def wei_to_eth(wei):
    return wei / 10**18

def format_balance(balance):
    """Форматирование баланса до двух знаков после запятой."""
    return f"{balance:.2f}"

def check_proxy(proxy):
    try:
        response = requests.get("https://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
        response.raise_for_status()
        return True  # Прокси работает
    except requests.exceptions.RequestException:
        return False  # Прокси не работает

def get_balance(account, proxy, network=None):
    if network:
        url = NETWORK_URLS.get(network)
        if not url:
            raise ValueError(f"Unsupported network: {network}")

        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [account, "latest"],
            "id": 1
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), proxies={"http": proxy, "https": proxy})
            response.raise_for_status()  # Проверка на успешный ответ

            result = response.json()
            balance_hex = result.get("result", "0x0")
            balance_wei = int(balance_hex, 16)  # Преобразование из hex в wei
            balance_eth = wei_to_eth(balance_wei)  # Преобразование из wei в eth

            return format_balance(balance_eth)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching balance for account {GREEN}{account}{RESET} using proxy {proxy} on network {GREEN}{network}{RESET}: {e}")
            return None

    else:
        url = f"https://pricer.t1rn.io/user/brn/balance?account={account}"

        try:
            response = requests.get(url, proxies={"http": proxy, "https": proxy})
            response.raise_for_status()  # Проверка на успешный ответ

            data = response.json()  # Преобразование ответа в JSON
            balance = data.get('BRNBalance', 'N/A')  # Извлечение баланса из поля 'BRNBalance'
            return format_balance(float(balance))

        except requests.exceptions.RequestException as e:
            print(f"Error fetching balance for account {GREEN}{account}{RESET} using proxy {proxy}: {e}")
            return None

def read_wallets(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def read_proxies(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def append_to_csv(data, filename='results.csv'):
    # Сохраняем данные в CSV
    df = pd.DataFrame(data)
    df.to_csv(filename, mode='a', header=not pd.io.common.file_exists(filename), index=False)

def check_balances_and_send_report():
    wallets = read_wallets('wallets.txt')
    proxies = read_proxies('proxies.txt')

    if len(wallets) > len(proxies):
        print("Warning: Not enough proxies for all accounts. Some accounts may be skipped.")

    results = []  # Инициализация переменной results
    message_to_send = ""  # Сообщение для Telegram

    # Перебор аккаунтов и прокси
    for i, account in enumerate(wallets):
        if i >= len(proxies):
            print("Not enough proxies for all accounts.")
            break
        
        proxy = proxies[i]

        if check_proxy(proxy):
            print(f"Using working proxy: {GREEN}{proxy}{RESET} for account: {GREEN}{account}{RESET}")

            # Запрос баланса через API pricer
            balance_info_pricer = get_balance(account, proxy)
            network_results = {}

            if balance_info_pricer is not None:
                network_results['BRN'] = balance_info_pricer

            # Запрос баланса для всех сетей
            for network in NETWORK_URLS:
                balance_info_network = get_balance(account, proxy, network)
                
                if balance_info_network is not None:
                    network_results[network] = balance_info_network
                
            if network_results:
                date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\nAccount: {GREEN}{account}{RESET}")
                
                # Формирование сообщения для Telegram
                message_to_send += f"\n<b>Account:</b> {account}\n"
                
                if 'BRN' in network_results:
                    message_to_send += f"Balance on BRN: {network_results['BRN']}\n"
                
                for network, balance in network_results.items():
                    if network != 'BRN':  # Пропуск уже выведенного BRN
                        message_to_send += f"Balance on {network}: {balance}\n"

                # Добавляем результат в CSV
                result = {
                    'Date': date_now,
                    'Account': account,
                    'Results': network_results
                }
                append_to_csv([result])
                results.append({'Account': account, 'Results': network_results})
        else:
            print(f"Proxy {GREEN}{proxy}{RESET} is not working. Skipping...")

    # Отправка итогового сообщения в Telegram
    if message_to_send:
        send_telegram_message(BOT_TOKEN, CHAT_ID, message_to_send)

# Планировщик для запуска каждые 60 минут
schedule.every(60).minutes.do(check_balances_and_send_report)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)
