import requests
import pandas as pd
from datetime import datetime
import json

# ANSI escape codes for colors
GREEN = '\033[92m'
RESET = '\033[0m'

# Ваш API ключ
API_KEY = "lNTUkf8We6CAI3gpMaBGyPsSz7bRk2U1"

# URLs для сетей
NETWORK_URLS = {
    "arbitrum_sepolia": f"https://arb-sepolia.g.alchemy.com/v2/{API_KEY}",
    "optimism_sepolia": f"https://opt-sepolia.g.alchemy.com/v2/{API_KEY}",
    "base_sepolia": f"https://base-sepolia.g.alchemy.com/v2/{API_KEY}",
    "blast_sepolia": f"https://blast-sepolia.g.alchemy.com/v2/{API_KEY}",
}

def wei_to_eth(wei):
    return wei / 10**18

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

            # Вывод полного ответа для проверки в зелёном цвете
            print(f"Raw response for account {GREEN}{account}{RESET} on network {GREEN}{network}{RESET}: {GREEN}{result}{RESET}")

            return balance_eth

        except requests.exceptions.RequestException as e:
            print(f"Error fetching balance for account {GREEN}{account}{RESET} using proxy {proxy} on network {GREEN}{network}{RESET}: {e}")
            return None

    else:
        url = f"https://pricer.t1rn.io/user/brn/balance?account={account}"

        try:
            response = requests.get(url, proxies={"http": proxy, "https": proxy})
            response.raise_for_status()  # Проверка на успешный ответ

            data = response.json()  # Преобразование ответа в JSON

            # Вывод полного ответа для проверки в зелёном цвете
            print(f"Raw response for account {GREEN}{account}{RESET}: {GREEN}{data}{RESET}")

            # Пример: извлечение баланса из поля 'balance'
            return data.get('balance', 'N/A')  # Убедитесь, что используете правильный ключ

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

if __name__ == "__main__":
​⬤
