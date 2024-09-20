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
