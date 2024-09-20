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

def check_proxy(proxy):
    try:
        response = requests.get("https://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
        response.raise_for_status()
        return True  # Прокси работает
    except requests.exceptions.RequestException:
        return False  # Прокси не работает

def get_balance(account, proxy, network):
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
        
        # Вывод полного ответа для проверки в зелёном цвете
        print(f"Raw response for account {GREEN}{account}{RESET} on network {GREEN}{network}{RESET}: {GREEN}{result}{RESET}")
        
        return balance_wei
    except requests.exceptions.RequestException as e:
        print(f"Error fetching balance for account {GREEN}{account}{RESET} using proxy {proxy} on network {GREEN}{network}{RESET}: {e}")
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
    wallets = read_wallets('wallets.txt')
    proxies = read_proxies('proxies.txt')

    if len(wallets) > len(proxies):
        print("Warning: Not enough proxies for all accounts. Some accounts may be skipped.")

    results = []  # Инициализация переменной results

    # Сет для обеспечения уникальности прокси
    used_proxies = set()

    for account in wallets:
        for proxy in proxies:
            if proxy in used_proxies:
                continue  # Пропускаем уже использованные прокси
            
            if check_proxy(proxy):
                print(f"Using working proxy: {GREEN}{proxy}{RESET} for account: {GREEN}{account}{RESET}")

                # Запрос баланса для всех сетей
                network_results = {}
                for network in NETWORK_URLS:
                    balance_info = get_balance(account, proxy, network)
                    
                    if balance_info is not None:
                        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        network_results[network] = balance_info
                        print(f"Balance Information for {GREEN}{account}{RESET} on {GREEN}{network}{RESET}: {GREEN}{balance_info}{RESET}")
                        
                        # Добавляем результат в CSV и в список результатов
                        result = {
                            'Date': date_now,
                            'Account': account,
                            'Network': network,
                            'Balance': balance_info
                        }
                        append_to_csv([result])
                results.append({'Account': account, 'Results': network_results})
                used_proxies.add(proxy)
                break  # Переходим к следующему аккаунту после успешного запроса
            else:
                print(f"Proxy {GREEN}{proxy}{RESET} is not working for account {GREEN}{account}{RESET}. Skipping...")
    
    # Печать итоговой таблицы
    if results:
        df_results = pd.DataFrame(results)
        print("\nFinal Results:")
        for index, row in df_results.iterrows():
            print(f"Account: {GREEN}{row['Account']}{RESET}")
            for network, balance in row['Results'].items():
                print(f"  {GREEN}{network}{RESET}: {GREEN}{balance}{RESET}")
    else:
        print("No results to display.")
