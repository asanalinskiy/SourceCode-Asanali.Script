# 😄 Asanali Script (aScript) v1.0

**aScript** — это легкий, фановый и мощный скриптовый язык программирования, построенный на базе гибридной архитектуры (Python, JavaScript и элементы C). Он сочетает в себе простоту системных команд `.bat` файлов, гибкость Python и возможности веб-интерфейсов.

## Главные фичи
* **Встроенный движок окон:** Через команду `window()` можно мгновенно развернуть графический интерфейс с поддержкой HTML5, CSS (включая эффекты glassmorphism, `backdrop-blur`) и JavaScript.
* **Голосовой и тональный класс:** Блок `class sound` умеет озвучивать текст голосом робота и генерировать чистые звуковые частоты.
* **Работа с системой и БД:** Встроенные команды для поиска файлов по маске (`open`), работы с файлами (`join`) и встроенная база данных (`database`), которая автоматически связывает фронтенд в окне с бэкендом на ПК.

## Пример кода (`index.asc/index.ascript`)

```TypeScript
/*
 * ===================================================
 *  AsanaliScript v1.0.0 — Демонстрационный пример кода
 * ===================================================
 */

/* 1. Объявление объектов через const и {} */
const product = {
    name: "Игровой ПК Quantium",
    price: 350000,
    inStock: true
}

/* 2. TypeScript-переменные со строгой типизацией */
let customer: string = $User
let discount: number = 5000

/* 3. Работа с CLI и системной информацией */
cli.args
show sys.info

/* 4. Вывод данных с обращением к полям через точку ($obj.prop) */
echo Покупатель: $customer
echo Товар: $product.name
echo Стандартная цена: $product.price ₸

/* 5. Использование голосового робота и звуковых сигналов */
class sound {
    echo Уважаемый $customer, ваш заказ $product.name оформлен!
    tone 523
    tone 659
}

/* 6. Автоматическое сохранение чека в файл */
join "order_receipt.txt" {
    write "Чек для $customer\nТовар: $product.name\nСумма: $product.price KZT"
}

/* 7. Графическое окно window() */
window(
    const style = `
        body { background: #0e1017; font-family: 'Segoe UI', sans-serif; }
        .card { 
            background: #181b26; 
            border: 1px solid #00ffcc; 
            border-radius: 12px; 
            padding: 24px; 
            box-shadow: 0 10px 30px rgba(0,255,204,0.1);
            max-width: 400px;
            margin: auto;
        }
        h2 { color: #00ffcc; margin-top: 0; }
        .price-tag { font-size: 20px; font-weight: bold; color: #fff; }
        button { 
            background: #00ffcc; 
            color: #0e1017; 
            border: none; 
            padding: 12px 20px; 
            border-radius: 6px; 
            font-weight: bold; 
            cursor: pointer; 
            width: 100%;
            margin-top: 15px;
        }
        button:hover { background: #00e6b8; }
    `
    <div class="card">
        <!-- Комментарий внутри HTML блока -->
        <h2>$product.name</h2>
        <p>Покупатель: <strong>$customer</strong></p>
        <p class="price-tag">Цена: $product.price ₸</p>
        <button onclick="playBeep(600, 0.2)">Подтвердить оплату</button>
    </div>
)
```