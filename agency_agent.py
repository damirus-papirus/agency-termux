#!/usr/bin/env python3
"""Agency Agents browser for Termux. Keeps the upstream repository unchanged."""
import os
import shutil
import subprocess
from pathlib import Path

from ai_chat import run_chat

BASE = Path(__file__).resolve().parent
REPO = BASE / "agency-agents"
EXPORTS = BASE / "exported"


def clear():
    os.system("clear")


def categories():
    if not REPO.is_dir():
        return []
    ignored = {".git", ".github", "__pycache__", "node_modules"}
    return sorted(
        p for p in REPO.iterdir()
        if p.is_dir() and p.name not in ignored and not p.name.startswith(".")
        and any(p.rglob("*.md"))
    )


def files_in(folder):
    return sorted(
        p for p in folder.rglob("*.md")
        if p.is_file() and ".git" not in p.parts
    )


def all_agents():
    return [(category.name, path) for category in categories()
            for path in files_in(category)]


def title_of(path):
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    except (OSError, UnicodeError):
        pass
    return path.stem.replace("-", " ").title()


def read_agent(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return f"Не удалось прочитать файл: {error}"


def choose(items):
    for i, (category, path) in enumerate(items, 1):
        print(f"{i:4}. [{category}] {title_of(path)}")
    print("\n0. Назад")
    while True:
        value = input("\nНомер: ").strip()
        if value == "0":
            return None
        if value.isdigit() and 1 <= int(value) <= len(items):
            return items[int(value) - 1]
        print("Неверный номер.")


def export_agent(agent):
    category, source = agent
    EXPORTS.mkdir(parents=True, exist_ok=True)
    target = EXPORTS / f"{category}__{source.name}"
    shutil.copy2(source, target)
    print(f"\nЭкспортировано: {target}")


def show_agent(agent):
    category, path = agent
    clear()
    print("=" * 64)
    print(title_of(path))
    print(f"Категория: {category}")
    print(f"Файл: {path.relative_to(REPO)}")
    print("=" * 64 + "\n")
    print(read_agent(path))
    print("\n1. Экспортировать Markdown")
    print("2. Скопировать инструкцию в буфер обмена")
    print("0. Назад")
    choice = input("> ").strip()
    if choice == "1":
        export_agent(agent)
        input("\nНажми Enter...")
    elif choice == "2":
        clipboard = shutil.which("termux-clipboard-set")
        if not clipboard:
            print("Буфер недоступен. Установи приложение Termux:API и пакет termux-api.")
        else:
            try:
                subprocess.run(
                    [clipboard], input=read_agent(path), text=True, check=True
                )
                print("Инструкция скопирована.")
            except (OSError, subprocess.SubprocessError) as error:
                print(f"Ошибка буфера: {error}")
        input("\nНажми Enter...")


def browse():
    while True:
        clear()
        cats = categories()
        print("=== КАТЕГОРИИ ===\n")
        for i, category in enumerate(cats, 1):
            print(f"{i:3}. {category.name} ({len(files_in(category))} файлов)")
        print("\n0. Назад")
        value = input("\nВыбери категорию: ").strip()
        if value == "0":
            return
        if not value.isdigit() or not 1 <= int(value) <= len(cats):
            continue
        category = cats[int(value) - 1]
        agent = choose([(category.name, p) for p in files_in(category)])
        if agent:
            show_agent(agent)


def search():
    query = input("Поиск по названию или содержимому: ").strip().lower()
    if not query:
        return
    results = []
    for category, path in all_agents():
        if query in title_of(path).lower() or query in read_agent(path).lower():
            results.append((category, path))
    clear()
    print(f"Найдено: {len(results)}\n")
    if results:
        agent = choose(results)
        if agent:
            show_agent(agent)
    else:
        print("Ничего не найдено.")
        input("\nНажми Enter...")


def update():
    if not (REPO / ".git").exists():
        print("Вложенный каталог agency-agents не найден.")
    else:
        result = subprocess.run(["git", "-C", str(REPO), "pull", "--ff-only"])
        print("Обновление завершено." if result.returncode == 0
              else "Не удалось обновить каталог.")
    input("\nНажми Enter...")


def main():
    if not REPO.is_dir():
        print("Каталог оригинальных агентов не найден.")
        print("Запусти ./start.sh, чтобы установить его.")
        return
    while True:
        clear()
        print("""
  AGENCY AGENTS — TERMUX

  1. Каталог агентов
  2. Поиск агентов
  3. Обновить оригинальный каталог
  4. Экспортированные файлы
  5. Статистика
  6. Чат с ИИ (OpenRouter)
  0. Выход
""")
        choice = input("> ").strip()
        if choice == "1":
            browse()
        elif choice == "2":
            search()
        elif choice == "3":
            update()
        elif choice == "4":
            EXPORTS.mkdir(parents=True, exist_ok=True)
            print(f"\nПапка: {EXPORTS}")
            for path in sorted(EXPORTS.glob("*.md")):
                print(path.name)
            input("\nНажми Enter...")
        elif choice == "5":
            print(f"Категорий: {len(categories())}")
            print(f"Агентов Markdown: {len(all_agents())}")
            print(f"Экспортировано: {len(list(EXPORTS.glob('*.md'))) if EXPORTS.exists() else 0}")
            input("\nНажми Enter...")
        elif choice == "6":
            run_chat()
        elif choice == "0":
            break


if __name__ == "__main__":
    main()
