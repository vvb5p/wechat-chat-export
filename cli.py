# -*- coding: utf-8 -*-
import argparse

from exporter_core import (
    clear_sensitive_cache,
    export_all_chats,
    export_chat,
    install_local_asr_model,
    install_rust_silk,
)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Экспорт сообщений WeChat для больших моделей")
    p.add_argument("name", nargs="?", help="Примечание к другу/ник или название группы")
    p.add_argument("--out", default="exports")
    p.add_argument(
        "--images",
        action="store_true",
        help="Также экспортировать кэшированные изображения из чатов",
    )
    p.add_argument(
        "--files",
        action="store_true",
        help="Также экспортировать кэшированные файлы из чатов",
    )
    p.add_argument("--voices", action="store_true", help="Также экспортировать голосовые; при наличии декодера создавать WAV")
    p.add_argument("--videos", action="store_true", help="Также экспортировать кэшированные видео")
    p.add_argument(
        "--transcribe-voices",
        action="store_true",
        help="Преобразовать экспортированные голосовые в текст локально с помощью SenseVoice; автоматически включает экспорт голосовых",
    )
    p.add_argument(
        "--media",
        action="store_true",
        help="Включить экспорт изображений, файлов, голосовых и видео",
    )
    p.add_argument(
        "--all",
        dest="export_all",
        action="store_true",
        help=(
            "Экспортировать все личные и групповые чаты, которые можно надёжно определить по локальным таблицам сообщений, "
            "и создать общий индекс all_chats_index.json / all_chats_index.md"
        ),
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Используется с --all: экспортировать только последние N чатов, чтобы сначала проверить на небольшом объёме",
    )
    p.add_argument(
        "--install-asr",
        action="store_true",
        help="Загрузить и установить локальную модель распознавания речи SenseVoice, затем выйти",
    )
    p.add_argument(
        "--install-rust-silk",
        action="store_true",
        help="Загрузить и установить декодер речи rust-silk, затем выйти",
    )
    p.add_argument(
        "--clear-sensitive-cache",
        action="store_true",
        help=(
            "Очистить временный чувствительный кэш текущей версии, а также ключи и кэш расшифрованных баз данных, "
            "оставленные версиями v1.3.3 и ранее / wechatauto-replica по умолчанию, затем выйти"
        ),
    )
    p.add_argument(
        "--db-dir",
        default=None,
        help=(
            "Папка данных WeChat (та, что показана в WeChat в «Настройки → Управление файлами»). "
            "По умолчанию определяется автоматически; укажите вручную, если папка была перенесена или автоопределение выбрало неправильную копию."
        ),
    )
    a = p.parse_args()

    if a.limit is not None and a.limit <= 0:
        p.error("--limit должен быть положительным целым числом.")
    if a.limit is not None and not a.export_all:
        p.error("--limit можно использовать только вместе с --all.")

    if a.install_asr:
        install_local_asr_model(progress=print)
        raise SystemExit(0)
    if a.install_rust_silk:
        install_rust_silk(progress=print)
        raise SystemExit(0)
    if a.clear_sensitive_cache:
        report = clear_sensitive_cache()
        for path in report.get("removed") or []:
            print("Очищено: " + path)
        if not report.get("removed"):
            print("Нет чувствительного кэша для очистки.")
        failed = report.get("failed") or []
        if failed:
            for item in failed:
                print(
                    "Очистка не удалась: "
                    + str(item.get("path"))
                    + ": "
                    + str(item.get("error"))
                )
            raise SystemExit(1)
        raise SystemExit(0)
    if a.export_all:
        if a.name:
            print(f"Внимание: указан --all, ключевое слово чата «{a.name}» игнорируется.")
        result = export_all_chats(
            a.out,
            progress=print,
            export_images=(a.images or a.media),
            export_files=(a.files or a.media),
            export_voices=(a.voices or a.media or a.transcribe_voices),
            export_videos=(a.videos or a.media),
            transcribe_voices=a.transcribe_voices,
            db_dir=a.db_dir,
            limit=a.limit,
        )
        print(
            f"Надёжно распознанных чатов {result['discovered_total']}, "
            f"обработано в этот раз {result['selected_total']}; "
            f"успешно {result['exported']}, без сообщений {result['skipped_empty']}, "
            f"ошибок {result['failed']}, всего сообщений {result['total_messages']}."
        )
        if result.get("unresolved_message_tables"):
            print(
                f"Ещё {result['unresolved_message_tables']} таблиц сообщений нельзя надёжно идентифицировать, "
                "пропущены без попыток угадать."
            )
        print("Папка вывода: " + result["output_dir"])
        print("Общий индекс: " + result["index_md"])
        if not result["sensitive_cache_cleanup"]:
            print(
                "Автоматическая очистка чувствительного временного кэша не удалась: "
                + str(result.get("sensitive_cache_cleanup_error"))
            )
            raise SystemExit(1)
        raise SystemExit(1 if result["failed"] else 0)

    if not a.name:
        p.error(
            "Укажите примечание к другу/ник или название группы; или используйте --all для экспорта всех чатов; "
            "или --install-asr / --install-rust-silk / "
            "--clear-sensitive-cache"
        )

    result = export_chat(
        a.name,
        a.out,
        progress=print,
        export_images=(a.images or a.media),
        export_files=(a.files or a.media),
        export_voices=(a.voices or a.media or a.transcribe_voices),
        export_videos=(a.videos or a.media),
        transcribe_voices=a.transcribe_voices,
        db_dir=a.db_dir,
    )
    print(result)
