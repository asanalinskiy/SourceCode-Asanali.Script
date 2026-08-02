# asanaliscript code
```JSX
let appName : string = "AsanaliScript Studio"
let version : number = 2.1
let isDevMode : boolean = true

let config = {
    theme: "dark",
    autoSave: true
}

show sys.info
echo Запуск приложения $appName (v$version)...
echo Текущий пользователь: $User

if $isDevMode == true {
    echo Режим разработчика активен.
} else {
    echo Запущено в продакшн режиме.
}

cli.args
join "system_log.txt" {
    write "Сессия $User успешно инициализирована в $appName."
}

class sound {
    echo "Система готова к работе"
    tone 440
    tone 880
}

window(
    <div style="font-family: sans-serif; padding: 20px; background: #0d1117; color: #c9d1d9; border-radius: 10px;">
        <h1 style="color: #58a6ff;">🚀 $appName v$version</h1>
        <p>Разработчик/Пользователь: <b>$User</b></p>
        <hr style="border-color: #30363d;" />
        
        <h3>Управление базой данных</h3>
        <button onclick="saveToDB('last_login', '$User')" style="background: #238636; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
            Сохранить сессию в DB
        </button>
        <button onclick="getFromDB('last_login')" style="background: #1f6beb; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-left: 10px;">
            Проверить DB
        </button>

        <h3 style="margin-top: 20px;">Тест звука</h3>
        <button onclick="playBeep(523, 0.2)" style="background: #89b4fa; color: #11111b; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
            🔊 Воспроизвести Beep (C5)
        </button>
    </div>
)
```
