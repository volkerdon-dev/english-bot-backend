import os
from telegraph import Telegraph

TELEGRAPH_AUTH_TOKEN = os.getenv("TELEGRAPH_AUTH_TOKEN")
telegraph = Telegraph(TELEGRAPH_AUTH_TOKEN) if TELEGRAPH_AUTH_TOKEN else Telegraph("EnglishHelperBot_Temp")

async def create_telegraph_page_for_verbs(verbs_data: list, title: str, author_name: str = "English Helper Bot") -> str:
    """
    Создает HTML-страницу на Telegra.ph из списка неправильных глаголов.
    Возвращает URL созданной страницы, используя более простой HTML.
    """
    if not verbs_data:
        print("DEBUG: create_telegraph_page_for_verbs: No verbs data provided.")
        return None

    # Формируем контент без тегов table, которые вызывают ошибку
    html_content = ["<h3 style='text-align: center;'>Таблица неправильных глаголов</h3>"]
    html_content.append("<p>Ниже представлена таблица неправильных глаголов:</p>")
    html_content.append("<hr>") # Разделитель

    # Заголовки (можем сделать жирным текстом)
    header = "<p><b>V1 (Base) | V2 (Past Simple) | V3 (Past Participle) | Перевод</b></p>"
    html_content.append(header)
    html_content.append("<hr>") # Разделитель

    for v in verbs_data:
        base = v.get('base', '')
        past = v.get('past', '')
        participle = v.get('participle', '')
        translation = v.get('translation', '')
        
        # Форматируем каждую строку как отдельный параграф или с переносами строк
        # Можно использовать <pre> для моноширинного текста, если хочется выравнивания
        # Но для простоты начнем с обычных параграфов.
        html_content.append(f"<p>{base} | {past} | {participle} | {translation}</p>")
    
    html_content.append("<hr>") # Разделитель
    html_content.append("<p style='font-size: 0.8em; color: #888;'><i>Данные взяты из словаря неправильных глаголов.</i></p>")

    try:
        response = telegraph.create_page(
            title=title,
            html_content="".join(html_content),
            author_name=author_name
        )
        print(f"DEBUG: Telegraph API Response: {response}")
        return response['url']
    except Exception as e:
        print(f"❌ Error creating Telegraph page: {e}")
        return None
