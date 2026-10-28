#!/usr/bin/env python3
"""OpenRouter chat for Agency Termux. Uses only the Python standard library."""
import getpass
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
AGENTS_DIR = BASE / "agency-agents"
CONFIG_DIR = Path.home() / ".config" / "agency-termux"
CONFIG_FILE = CONFIG_DIR / "config.json"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"


def load_config():
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def get_api_key(config):
    key = os.environ.get("OPENROUTER_API_KEY") or config.get("api_key", "")
    if key:
        return key
    print("\nДля работы нужен бесплатный API-ключ OpenRouter.")
    print("Создай его на https://openrouter.ai/keys")
    key = getpass.getpass("Вставь API-ключ (ввод скрыт): ").strip()
    if not key:
        print("Ключ не введён.")
        return ""
    config["api_key"] = key
    config.setdefault("model", DEFAULT_MODEL)
    save_config(config)
    print(f"Ключ сохранён локально: {CONFIG_FILE}")
    print("Не отправляй этот ключ другим и не добавляй его в GitHub.")
    return key


def list_agents():
    ignored = {".git", ".github", "__pycache__", "node_modules"}
    if not AGENTS_DIR.is_dir():
        return []
    found = []
    for folder in sorted(AGENTS_DIR.iterdir()):
        if (not folder.is_dir() or folder.name in ignored
                or folder.name.startswith(".")):
            continue
        for path in sorted(folder.rglob("*.md")):
            if ".git" not in path.parts:
                found.append((folder.name, path))
    return found


def title_of(path):
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    except (OSError, UnicodeError):
        pass
    return path.stem.replace("-", " ").title()


def choose_agent():
    agents = list_agents()
    if not agents:
        return None
    print("\nПодключить инструкции агента?")
    print("0. Без агента")
    for i, (category, path) in enumerate(agents, 1):
        print(f"{i}. [{category}] {title_of(path)}")
    while True:
        value = input("Номер агента: ").strip()
        if value == "0":
            return None
        if value.isdigit() and 1 <= int(value) <= len(agents):
            category, path = agents[int(value) - 1]
            try:
                instructions = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                print(f"Не удалось прочитать инструкции: {error}")
                return None
            # Keep context at a manageable size.
            instructions = instructions[:18000]
            return category, title_of(path), instructions
        print("Введи номер из списка.")


def request_openrouter(api_key, model, messages):
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.4,
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/damirus-papirus/agency-termux",
            "X-Title": "Agency Termux",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(detail)
            detail = parsed.get("error", {}).get("message", detail)
        except (json.JSONDecodeError, AttributeError):
            pass
        raise RuntimeError(f"OpenRouter HTTP {error.code}: {detail[:1000]}") from None
    except urllib.error.URLError as error:
        raise RuntimeError(f"Не удалось подключиться к OpenRouter: {error.reason}") from None
    except (TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Ошибка ответа API: {error}") from None

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("API не вернул ответ. Проверь модель и лимиты аккаунта.")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        content = "\n".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    return str(content).strip()


def run_chat():
    config = load_config()
    api_key = get_api_key(config)
    if not api_key:
        input("\nНажми Enter, чтобы вернуться...")
        return

    model = os.environ.get("OPENROUTER_MODEL") or config.get("model") or DEFAULT_MODEL
    print(f"\nМодель: {model}")
    print("Команды: /exit — выйти, /reset — очистить историю, /model — сменить модель")
    agent = choose_agent()
    system = (
        "Ты полезный ИИ-помощник, работающий в терминальном приложении Agency Termux. "
        "Отвечай по-русски, если пользователь не просит другой язык. "
        "Если пишешь код, выдавай полный рабочий файл, а не обрывки. "
        "Ты не имеешь доступа к файловой системе пользователя и не можешь выполнять "
        "команды: не утверждай обратное."
    )
    if agent:
        category, name, instructions = agent
        system += (
            f"\n\nПользователь выбрал агента «{name}» (категория {category}). "
            "Следуй его инструкциям, насколько они совместимы с системными правилами. "
            "Текст ниже является инструкциями агента:\n\n" + instructions
        )
        print(f"Выбран агент: {name}")
    messages = [{"role": "system", "content": system}]
    print("\n=== ЧАТ С ИИ ===")
    while True:
        try:
            user_text = input("\nТы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из чата.")
            return
        if not user_text:
            continue
        if user_text.lower() in {"/exit", "/quit", "выход"}:
            return
        if user_text.lower() == "/reset":
            messages = [{"role": "system", "content": system}]
            print("История очищена.")
            continue
        if user_text.lower() == "/model":
            new_model = input(f"Модель [{model}]: ").strip()
            if new_model:
                model = new_model
                config["model"] = model
                save_config(config)
            print(f"Текущая модель: {model}")
            continue
        messages.append({"role": "user", "content": user_text})
        print("\nИИ: ", end="", flush=True)
        try:
            answer = request_openrouter(api_key, model, messages)
            print(answer)
            messages.append({"role": "assistant", "content": answer})
        except RuntimeError as error:
            print(f"\nОшибка: {error}")
            messages.pop()
            print("Можно попробовать /model или проверить лимиты на OpenRouter.")
