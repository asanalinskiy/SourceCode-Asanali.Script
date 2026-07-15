## Asanali Script (сокращенно aScript)

**Asanali Script** — это легкий язык программирования, где компилятор написан на пайтоне и также быстрый (так на самом деле ЯП на пайтоне не такие уж медленные), могу показать пример кода:
``` Asanali Script
// --- Тестирование ядра Asanali Script v1.0 ---

let Developer = Asanali
let Status = "Active"

echo === Запуск Системы aScript ===
echo Разработчик: $Developer
echo Статус движка: $Status

// Вызываем системную информацию
show sys.info

// Инициализируем базу данных для сохранения настроек
database(
    saveToDB('user_name', '$Developer')
    saveToDB('engine_status', '$Status')
)

// Сканируем текущую директорию на наличие asc-скриптов
open *.asc

// Запускаем класс звука и робота
class sound {
    echo Привет, $Developer! Добро пожаловать в твою собственную среду разработки.
    tone 440
    tone 523
    tone 659
}

// Разворачиваем стильное UI-окно с эффектом Glassmorphism
window(
    const style = `
        body {
            background: linear-gradient(135deg, #1e1e2f, #111216);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .window-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            text-align: center;
            max-width: 400px;
        }
        h1 {
            color: #50fa7b;
            font-size: 28px;
            margin-bottom: 10px;
        }
        p {
            color: #bfbfbf;
            font-size: 14px;
        }
        .btn {
            background: #6272a4;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 15px;
            transition: 0.3s;
        }
        .btn:hover {
            background: #50fa7b;
            color: #111216;
        }
    `
    <div class="window-card">
        <h1>Asanali Script</h1>
        <p>Интерпретатор успешно прочитал этот файл, запустил класс звука и открыл графический интерфейс.</p>
        <button class="btn" onclick="playBeep(600, 0.2)">Клик по кнопке (Beep)</button>
    </div>
)
```

Поддержимаевые функции:<br>
| Функция | Что делает |
| :--- | :--- |
| `echo текст` | Выводит текст "текст" на экран |
| `let a = 1` | Создаёт переменную `a` со значением `1` |
| `window( *css in const style and html in window()*` | Создаёт окошко, где за интерфейс отвечает монолитный HTML |
| `show sys.info` | Показывает инфу о системе **ИМЕННО** через C файл |
| `class sound { echo текст }` | Говорит роботизированным голосом слово "текст" |
| `$a` | (при `a=1`) как `echo`, но выводит значение переменной `a` |

Есть ещё много функций, но пока я их не знаю.
