#!/usr/bin/env python3
"""Cold Wallet — консольный холодный кошелёк для XMR / TON / USDT-TRC20.

Запуск:
    python main.py

Все приватные ключи и мнемоники хранятся только локально, в зашифрованном
файле ~/.coldwallet/vault.dat (AES-256-GCM, пароль -> scrypt). Ничего не
уходит на сторону, кроме явных, помеченных сетевых операций (просмотр
баланса/курса через публичные API, отправка уже подписанной транзакции,
обмен через ChangeNOW).
"""
import getpass
import sys

from core import vault
from chains import xmr, ton, usdt_trc20, rates, balance, send_trc20, send_ton, send_xmr, swap

CHAINS = ["xmr", "ton", "usdt_trc20"]
CHAIN_LABELS = {"xmr": "Monero (XMR)", "ton": "TON", "usdt_trc20": "USDT (TRC20 / Tron)"}


def pause():
    input("\nНажмите Enter, чтобы продолжить...")


def ask_password(prompt="Пароль: ") -> str:
    return getpass.getpass(prompt)


def cmd_create_wallet():
    print("\n=== Создание нового кошелька ===")
    if vault.vault_exists():
        confirm = input(
            "Хранилище уже существует. Создать заново и ПЕРЕЗАПИСАТЬ его? (да/нет): "
        )
        if confirm.strip().lower() not in ("да", "yes", "y"):
            print("Отменено.")
            return

    print("Генерирую ключи офлайн для всех трёх сетей...")
    data = {
        "xmr": xmr.generate(),
        "ton": ton.generate(),
        "usdt_trc20": usdt_trc20.generate(),
    }

    print("\n!!! ВАЖНО !!!")
    print("Ниже — секретные мнемонические фразы. Запишите их на бумаге и")
    print("храните в надёжном месте. Это единственный способ восстановить")
    print("кошелёк. Никому их не показывайте и не вводите на сайтах.\n")
    for chain in CHAINS:
        print(f"--- {CHAIN_LABELS[chain]} ---")
        print(f"Адрес:    {data[chain]['address']}")
        print(f"Мнемоника: {data[chain]['mnemonic']}")
        print()

    while True:
        pw1 = ask_password("Придумайте пароль для локального хранилища: ")
        pw2 = ask_password("Повторите пароль: ")
        if pw1 != pw2:
            print("Пароли не совпадают, попробуйте снова.")
            continue
        if len(pw1) < 8:
            print("Пароль слишком короткий (минимум 8 символов).")
            continue
        break

    vault.create_vault(pw1, data)
    print(f"\nХранилище сохранено: {vault.VAULT_FILE}")
    pause()


def cmd_restore_wallet():
    print("\n=== Восстановление кошелька из мнемоник ===")
    data = {}
    for chain in CHAINS:
        print(f"\n--- {CHAIN_LABELS[chain]} ---")
        phrase = input("Введите мнемоническую фразу (или Enter, чтобы пропустить): ").strip()
        if not phrase:
            continue
        try:
            if chain == "xmr":
                data[chain] = xmr.restore(phrase)
            elif chain == "ton":
                data[chain] = ton.restore(phrase)
            elif chain == "usdt_trc20":
                data[chain] = usdt_trc20.restore(phrase)
            print(f"Адрес восстановлен: {data[chain]['address']}")
        except Exception as e:
            print(f"Ошибка восстановления: {e}")

    if not data:
        print("Нечего сохранять.")
        return

    while True:
        pw1 = ask_password("Придумайте пароль для локального хранилища: ")
        pw2 = ask_password("Повторите пароль: ")
        if pw1 != pw2:
            print("Пароли не совпадают.")
            continue
        break

    vault.create_vault(pw1, data)
    print(f"\nХранилище сохранено: {vault.VAULT_FILE}")
    pause()


def unlock() -> dict:
    if not vault.vault_exists():
        print("Хранилище не найдено. Сначала создайте или восстановите кошелёк.")
        return None
    pw = ask_password()
    try:
        return vault.load_vault(pw)
    except vault.VaultError as e:
        print(f"Ошибка: {e}")
        return None


def cmd_show_addresses():
    data = unlock()
    if data is None:
        return
    print("\n=== Ваши адреса ===")
    for chain in CHAINS:
        if chain in data:
            print(f"{CHAIN_LABELS[chain]}: {data[chain]['address']}")
    pause()


def cmd_show_balances():
    data = unlock()
    if data is None:
        return
    print("\n=== Балансы ===")
    if "usdt_trc20" in data:
        try:
            b = balance.tron_balance(data["usdt_trc20"]["address"])
            print(f"TRX:  {b['TRX']}")
            print(f"USDT: {b['USDT']}")
        except Exception as e:
            print(f"Не удалось получить баланс TRON/USDT: {e}")
    if "ton" in data:
        try:
            b = balance.ton_balance(data["ton"]["address"])
            print(f"TON:  {b}")
        except Exception as e:
            print(f"Не удалось получить баланс TON: {e}")
    if "xmr" in data:
        try:
            b = balance.xmr_balance(data["xmr"]["address"], data["xmr"]["view_key"])
            print(f"XMR:  {b['total']} (доступно: {b['unlocked']})")
        except Exception as e:
            print(f"Не удалось получить баланс XMR через лёгкий кошелёк: {e}")
            print("(Для приватного просмотра используйте свой monero-wallet-rpc.)")
    pause()


def cmd_show_rates():
    print("\n=== Курсы ===")
    try:
        r = rates.get_rates()
        print(rates.format_rates_table(r))
    except Exception as e:
        print(f"Не удалось получить курсы: {e}")
    pause()


def cmd_send():
    data = unlock()
    if data is None:
        return
    print("\n=== Отправка ===")
    print("1. TRX")
    print("2. USDT (TRC20)")
    print("3. TON")
    print("4. XMR (требует запущенный локальный monero-wallet-rpc)")
    choice = input("Выберите монету: ").strip()

    to_addr = input("Адрес получателя: ").strip()
    try:
        amount = float(input("Сумма: ").strip())
    except ValueError:
        print("Некорректная сумма.")
        return

    try:
        if choice == "1":
            txid = send_trc20.send_trx(data["usdt_trc20"]["private_key"], to_addr, amount)
        elif choice == "2":
            txid = send_trc20.send_usdt(data["usdt_trc20"]["private_key"], to_addr, amount)
        elif choice == "3":
            txid = send_ton.send_ton(data["ton"]["mnemonic"], to_addr, amount)
        elif choice == "4":
            if not send_xmr.is_rpc_available():
                print("monero-wallet-rpc не запущен на 127.0.0.1:18082. См. SETUP.md.")
                return
            txid = send_xmr.send_xmr(to_addr, amount)
        else:
            print("Неизвестный выбор.")
            return
        print(f"\nОтправлено. TX: {txid}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")
    pause()


def cmd_swap():
    data = unlock()
    if data is None:
        return
    print("\n=== Обмен (через ChangeNOW, некастодиально) ===")
    api_key = data.get("changenow_api_key") or input(
        "API-ключ ChangeNOW (получить на changenow.io): "
    ).strip()

    print("Доступные активы: xmr, ton, usdt_trc20")
    from_asset = input("Из чего меняем: ").strip()
    to_asset = input("Во что меняем: ").strip()
    try:
        amount = float(input("Сумма (в исходной монете): ").strip())
    except ValueError:
        print("Некорректная сумма.")
        return

    if from_asset not in data or to_asset not in data:
        print("Актив недоступен в этом кошельке.")
        return

    try:
        est = swap.get_estimate(api_key, from_asset, to_asset, amount)
        print(f"Расчётная сумма к получению: {est}")
        confirm = input("Создать обмен? (да/нет): ").strip().lower()
        if confirm not in ("да", "yes", "y"):
            print("Отменено.")
            return

        exch = swap.create_exchange(
            api_key,
            from_asset,
            to_asset,
            amount,
            to_address=data[to_asset]["address"],
            refund_address=data[from_asset]["address"],
        )
        payin_address = exch["payinAddress"]
        print(f"Адрес для отправки: {payin_address}")
        print(f"ID обмена: {exch['id']}")

        auto = input("Отправить средства автоматически прямо сейчас? (да/нет): ").strip().lower()
        if auto in ("да", "yes", "y"):
            if from_asset == "usdt_trc20":
                txid = send_trc20.send_usdt(data["usdt_trc20"]["private_key"], payin_address, amount)
            elif from_asset == "ton":
                txid = send_ton.send_ton(data["ton"]["mnemonic"], payin_address, amount)
            elif from_asset == "xmr":
                if not send_xmr.is_rpc_available():
                    print("monero-wallet-rpc не запущен. Отправьте вручную на адрес выше.")
                    return
                txid = send_xmr.send_xmr(payin_address, amount)
            print(f"Отправлено, TX: {txid}. Отслеживайте статус обмена по ID выше.")
        else:
            print("Отправьте указанную сумму на адрес выше вручную, чтобы завершить обмен.")
    except Exception as e:
        print(f"Ошибка обмена: {e}")
    pause()


MENU = """
=======================================
   COLD WALLET — XMR / TON / USDT
=======================================
1. Создать новый кошелёк
2. Восстановить кошелёк из мнемоник
3. Показать адреса
4. Показать балансы
5. Показать курсы валют
6. Отправить
7. Обменять
0. Выход
"""


def main():
    while True:
        print(MENU)
        choice = input("Выберите пункт: ").strip()
        if choice == "1":
            cmd_create_wallet()
        elif choice == "2":
            cmd_restore_wallet()
        elif choice == "3":
            cmd_show_addresses()
        elif choice == "4":
            cmd_show_balances()
        elif choice == "5":
            cmd_show_rates()
        elif choice == "6":
            cmd_send()
        elif choice == "7":
            cmd_swap()
        elif choice == "0":
            print("До свидания.")
            sys.exit(0)
        else:
            print("Неизвестный пункт меню.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
