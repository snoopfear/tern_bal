import requests
import random

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

if __name__ == "__main__":
    wallets = read_wallets('wallets.txt')
    proxies = read_proxies('proxies.txt')
    
    for account in wallets:
        proxy = random.choice(proxies)  # Выбор случайного прокси
        balance_info = get_balance(account, proxy)
        
        if balance_info is not None:
            print(f"Balance Information for {account}:")
            print(balance_info)
