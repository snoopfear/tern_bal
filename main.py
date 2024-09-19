import requests
import pandas as pd
from datetime import datetime

def check_proxy(proxy):
    try:
        response = requests.get("https://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
        response.raise_for_status()
        return True  # Прокси работает
    except requests.exceptions.RequestException:
        return False  # Прокси не работает

def get_balance(account, proxy):
    url = f"https://pricer.t1rn.io/user/brn/balance?account={account}"
    
    try:
        response = requests.get(url, proxies={"http": proxy, "https": proxy})
        response.raise_for_status()  # Проверка на успешный ответ
        
        data = response.json()  # Преобразование ответа в JSON
        return data  # Возвращаем данные о балансе
    except requests.exceptions.RequestException as e:
        print(f"Error fetching balance for account {account} using proxy {proxy}: {e}")
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

    for account, proxy in zip(wallets, proxies):
        if check_proxy(proxy):
            print(f"Using working proxy: {proxy} for account: {account}")
            balance_info = get_balance(account, proxy)
            
            if balance_info is not None:
                date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"Balance Information for {account}: {balance_info}")
                
                # Добавляем результат в CSV и в список результатов
                result = {
                    'Date': date_now,
                    'Account': account,
                    'Balance': balance_info.get('balance', 'N/A')  # Добавляем только значение баланса
                }
                append_to_csv([result])
                results.append({'Account': account, 'Result': balance_info.get('balance', 'N/A')})
        else:
            print(f"Proxy {proxy} is not working for account {account}. Skipping...")

    # Печать итоговой таблицы
    if results:
        df_results = pd.DataFrame(results)
        print("\nFinal Results:")
        print(df_results[['Account', 'Result']])
    else:
        print("No results to display.")
