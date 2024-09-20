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
    wallets = read_wallets('wallets.txt')
    proxies = read_proxies('proxies.txt')

    if len(wallets) > len(proxies):
        print("Warning: Not enough proxies for all accounts. Some accounts may be skipped.")

    results = []  # Инициализация переменной results

    # Сет для обеспечения уникальности прокси
    used_proxies = set()

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
                date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"Balance Information from pricer for {GREEN}{account}{RESET}: {GREEN}{balance_info_pricer}{RESET}")

                # Добавляем результат в CSV и в список результатов
                result = {
                    'Date': date_now,
                    'Account': account,
                    'Network': 'pricer',
                    'Balance': balance_info_pricer
                }
                append_to_csv([result])
                results.append({'Account': account, 'Results': {'pricer': balance_info_pricer}})
                
            # Запрос баланса для всех сетей
            for network in NETWORK_URLS:
                balance_info_network = get_balance(account, proxy, network)
                
                if balance_info_network is not None:
                    date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    network_results[network] = balance_info_network
                    print(f"Balance Information for {GREEN}{account}{RESET} on {GREEN}{network}{RESET}: {GREEN}{balance_info_network}{RESET}")

                    # Добавляем результат в CSV и в список результатов
                    result = {
                        'Date': date_now,
                        'Account': account,
                        'Network': network,
                        'Balance': balance_info_network
                    }
                    append_to_csv([result])
                    results.append({'Account': account, 'Results': network_results})
                
            used_proxies.add(proxy)  # Добавляем прокси в набор использованных
        else:
            print(f"Proxy {GREEN}{proxy}{RESET} is not working. Skipping...")

    # Печать итоговой таблицы
    if results:
        df_results = pd.DataFrame(results)
        print("\nFinal Results:")
        print(df_results[['Account', 'Results']])
    else:
        print("No results to display.")
