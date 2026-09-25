#!/usr/bin/env python3
"""Cold Wallet — консольный холодный кошелёк для XMR / TON / USDT-TRC20.

Запуск:
    python main.py

Все приватные ключи и мнемоники хранятся только локально, в зашифрованном
файле ~/.coldwallet/vault.dat (AES-256-GCM, пароль -> scrypt). Пароль
запрашивается один раз за запуск программы, дальше расшифрованные ключи
живут только в памяти этого процесса и исчезают при выходе. Из сети
приложение обращается только к публичным API для просмотра баланса/курса
и для отправки уже подписанных локально транзакций — приватные ключи
никогда никуда не передаются.
"""
import getpass
import sys

from core import vault
from chains import xmr, ton, usdt_trc20, rates, balance, send_trc20, send_ton, send_xmr, swap

CHAINS = ["xmr", "ton", "usdt_trc20"]
CHAIN_LABELS = {"xmr": "Monero (XMR)", "ton": "TON", "usdt_trc20": "USDT (TRC20)"}

BANNER = r'''
   ██████╗ ██████╗ ██╗     ██████╗
  ██╔════╝██╔═══██╗██║     ██╔══██╗
  ██║     ██║   ██║██║     ██║  ██║
  ██║     ██║   ██║██║     ██║  ██║
  ╚██████╗╚██████╔╝███████╗██████╔╝
   ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝
        W A L L E T   ·   XMR / TON / USDT

           .-~~~~~-.
          /         \
         |  o     o  |
         |     ▽     |
          \   ___   /
           `-------`
        холодное хранилище
'''


def clear_hint():
    print()


def pause():
    input("\n  ↵  Нажмите Enter, чтобы продолжить...")


def ask_password(prompt="  Пароль: ") -> str:
    return getpass.getpass(prompt)


def header(title: str):
    print(f"\n  ◆ {title}\n")


def generate_new_wallet_data() -> dict:
    print("  Генерирую ключи офлайн для всех трёх сетей...\n")
    data = {
        "xmr": xmr.generate(),
        "ton": ton.generate(),
        "usdt_trc20": usdt_trc20.generate(),
    }
    print("  !!! ВАЖНО !!!")
    print("  Ниже — секретные мнемонические фразы. Запишите их на бумаге и")
    print("  храните в надёжном месте. Это единственный способ восстановить")
    print("  кошелёк. Никому их не показывайте и не вводите на сайтах.\n")
    for chain in CHAINS:
        print(f"  ── {CHAIN_LABELS[chain]} ──")
        print(f"  Адрес:     {data[chain]['address']}")
        print(f"  Мнемоника: {data[chain]['mnemonic']}")
        print()
    return data


def ask_new_password() -> str:
    while True:
        pw1 = ask_password("  Придумайте пароль для локального хранилища: ")
        pw2 = ask_password("  Повторите пароль: ")
        if pw1 != pw2:
            print("  Пароли не совпадают, попробуйте снова.")
            continue
        if len(pw1) < 8:
            print("  Пароль слишком короткий (минимум 8 символов).")
            continue
        return pw1


def restore_wallet_data() -> dict:
    data = {}
    for chain in CHAINS:
        print(f"\n  ── {CHAIN_LABELS[chain]} ──")
        phrase = input("  Мнемоническая фраза (Enter — пропустить): ").strip()
        if not phrase:
            continue
        try:
            if chain == "xmr":
                data[chain] = xmr.restore(phrase)
            elif chain == "ton":
                data[chain] = ton.restore(phrase)
            elif chain == "usdt_trc20":
                data[chain] = usdt_trc20.restore(phrase)
            print(f"  Адрес восстановлен: {data[chain]['address']}")
        except Exception as e:
            print(f"  Ошибка восстановления: {e}")
    return data


def onboarding() -> dict:
    """First run (or explicit reset): create or restore, return decrypted data."""
    header("Хранилище не найдено — начнём")
    print("  1. Создать новый кошелёк")
    print("  2. Восстановить кошелёк из мнемоник")
    choice = input("\n  Выберите пункт: ").strip()

    if choice == "2":
        data = restore_wallet_data()
    else:
        data = generate_new_wallet_data()

    if not data:
        print("  Нечего сохранять.")
        return None

    pw = ask_new_password()
    vault.create_vault(pw, data)
    print(f"\n  Хранилище сохранено: {vault.VAULT_FILE}")
    pause()
    return data


def login() -> dict:
    if not vault.vault_exists():
        return onboarding()

    header("Вход")
    for attempt in range(3):
        pw = ask_password()
        try:
            return vault.load_vault(pw)
        except vault.VaultError as e:
            print(f"  {e}")
    print("  Слишком много неверных попыток.")
    return None


def cmd_show_balance(chain: str, data: dict):
    header(f"Баланс — {CHAIN_LABELS[chain]}")
    try:
        if chain == "usdt_trc20":
            b = balance.tron_balance(data[chain]["address"])
            print(f"  TRX:  {b['TRX']}")
            print(f"  USDT: {b['USDT']}")
        elif chain == "ton":
            b = balance.ton_balance(data[chain]["address"])
            print(f"  TON:  {b}")
        elif chain == "xmr":
            b = balance.xmr_balance(data[chain]["address"], data[chain]["view_key"])
            print(f"  XMR:  {b['total']} (доступно: {b['unlocked']})")
    except Exception as e:
        print(f"  Не удалось получить баланс: {e}")
        if chain == "xmr":
            print("  (Для приватного просмотра используйте свой monero-wallet-rpc.)")
    pause()


def cmd_show_rate(chain: str = None):
    header("Курс")
    try:
        r = rates.get_rates()
        print(rates.format_rates_table(r))
    except Exception as e:
        print(f"  Не удалось получить курсы: {e}")
    pause()


def cmd_send(chain: str, data: dict):
    header(f"Отправка — {CHAIN_LABELS[chain]}")
    to_addr = input("  Адрес получателя: ").strip()
    try:
        amount = float(input("  Сумма: ").strip())
    except ValueError:
        print("  Некорректная сумма.")
        return

    try:
        if chain == "usdt_trc20":
            print("  1. TRX")
            print("  2. USDT")
            sub = input("  Что отправляем: ").strip()
            if sub == "1":
                txid = send_trc20.send_trx(data["usdt_trc20"]["private_key"], to_addr, amount)
            else:
                txid = send_trc20.send_usdt(data["usdt_trc20"]["private_key"], to_addr, amount)
        elif chain == "ton":
            txid = send_ton.send_ton(data["ton"]["mnemonic"], to_addr, amount)
        elif chain == "xmr":
            if not send_xmr.is_rpc_available():
                print("  monero-wallet-rpc не запущен на 127.0.0.1:18082. См. SETUP.md.")
                return
            txid = send_xmr.send_xmr(to_addr, amount)
        print(f"\n  Отправлено. TX: {txid}")
    except Exception as e:
        print(f"  Ошибка отправки: {e}")
    pause()


def cmd_swap(chain: str, data: dict):
    header(f"Обмен — {CHAIN_LABELS[chain]} → ?")
    others = [c for c in CHAINS if c != chain and c in data]
    for i, c in enumerate(others, 1):
        print(f"  {i}. {CHAIN_LABELS[c]}")
    pick = input("  Во что меняем: ").strip()
    try:
        to_asset = others[int(pick) - 1]
    except (ValueError, IndexError):
        print("  Некорректный выбор.")
        return

    api_key = data.get("changenow_api_key") or input(
        "  API-ключ ChangeNOW (получить на changenow.io): "
    ).strip()
    try:
        amount = float(input(f"  Сумма ({CHAIN_LABELS[chain]}): ").strip())
    except ValueError:
        print("  Некорректная сумма.")
        return

    try:
        est = swap.get_estimate(api_key, chain, to_asset, amount)
        print(f"  Расчётная сумма к получению: {est}")
        confirm = input("  Создать обмен? (да/нет): ").strip().lower()
        if confirm not in ("да", "yes", "y"):
            print("  Отменено.")
            return

        exch = swap.create_exchange(
            api_key, chain, to_asset, amount,
            to_address=data[to_asset]["address"],
            refund_address=data[chain]["address"],
        )
        payin_address = exch["payinAddress"]
        print(f"  Адрес для отправки: {payin_address}")
        print(f"  ID обмена: {exch['id']}")

        auto = input("  Отправить автоматически прямо сейчас? (да/нет): ").strip().lower()
        if auto in ("да", "yes", "y"):
            if chain == "usdt_trc20":
                txid = send_trc20.send_usdt(data["usdt_trc20"]["private_key"], payin_address, amount)
            elif chain == "ton":
                txid = send_ton.send_ton(data["ton"]["mnemonic"], payin_address, amount)
            elif chain == "xmr":
                if not send_xmr.is_rpc_available():
                    print("  monero-wallet-rpc не запущен. Отправьте вручную на адрес выше.")
                    return
                txid = send_xmr.send_xmr(payin_address, amount)
            print(f"  Отправлено, TX: {txid}. Статус обмена отслеживайте по ID выше.")
        else:
            print("  Отправьте сумму на адрес выше вручную, чтобы завершить обмен.")
    except Exception as e:
        print(f"  Ошибка обмена: {e}")
    pause()


def currency_menu(chain: str, data: dict):
    while True:
        header(CHAIN_LABELS[chain])
        print(f"  Адрес: {data[chain]['address']}\n")
        print("  1. Баланс")
        print("  2. Курс")
        print("  3. Отправить")
        print("  4. Обменять на другую монету")
        print("  0. Назад")
        choice = input("\n  Выберите пункт: ").strip()

        if choice == "1":
            cmd_show_balance(chain, data)
        elif choice == "2":
            cmd_show_rate(chain)
        elif choice == "3":
            cmd_send(chain, data)
        elif choice == "4":
            cmd_swap(chain, data)
        elif choice == "0":
            return
        else:
            print("  Неизвестный пункт меню.")


def main_menu(data: dict):
    while True:
        header("Главное меню")
        for i, chain in enumerate(CHAINS, 1):
            mark = "✓" if chain in data else "—"
            print(f"  {i}. {CHAIN_LABELS[chain]}  [{mark}]")
        print("  4. Курсы всех валют")
        print("  0. Выход")
        choice = input("\n  Выберите пункт: ").strip()

        if choice in ("1", "2", "3"):
            chain = CHAINS[int(choice) - 1]
            if chain not in data:
                print("  Эта монета не настроена в текущем кошельке.")
                continue
            currency_menu(chain, data)
        elif choice == "4":
            cmd_show_rate()
        elif choice == "0":
            print("\n  До свидания.")
            sys.exit(0)
        else:
            print("  Неизвестный пункт меню.")


def main():
    print(BANNER)
    data = login()
    if data is None:
        sys.exit(1)
    main_menu(data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Прервано пользователем.")
