import os
import re
import sys
import glob
import json
import webview
import pyttsx3  # Для синтеза речи голосом робота (pip install pyttsx3)

class AScriptBridge:
    """Мост для связи JavaScript внутри window() с Python-базой данных"""
    def __init__(self, db_path="ascript_db.json"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f: 
                json.dump({}, f)

    def save_data(self, key, value):
        with open(self.db_path, "r") as f: 
            data = json.load(f)
        data[key] = value
        with open(self.db_path, "w") as f: 
            json.dump(data, f, indent=4)
        return f"[database] Сохранено: {key}"

    def get_data(self, key):
        with open(self.db_path, "r") as f: 
            data = json.load(f)
        return data.get(key, "Не найдено")


class AScriptInterpreter:
    def __init__(self):
        self.variables = {'User': os.getlogin()}
        self.lines = []
        self.current_line = 0
        
        # Инициализируем голосовой движок робота
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 170) 
        except:
            self.tts_engine = None

    def replace_variables(self, text):
        for var, val in self.variables.items():
            text = text.replace(f"${var}", str(val))
        return text

    def evaluate_condition(self, condition_str):
        condition_str = self.replace_variables(condition_str)
        if "==" in condition_str:
            left, right = condition_str.split("==")
            return left.strip().strip("'\"") == right.strip().strip("'\"")
        if "!=" in condition_str:
            left, right = condition_str.split("!=")
            return left.strip().strip("'\"") != right.strip().strip("'\"")
        return False

    def skip_block(self):
        """Пропускает блок { ... } если условие if ложно"""
        brace_count = 0
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].strip()
            if "{" in line:
                brace_count += line.count("{")
            if "}" in line:
                brace_count -= line.count("}")
                if brace_count <= 0:
                    self.current_line += 1
                    break
            self.current_line += 1

    def execute_block_content(self, end_trigger="}"):
        block_lines = []
        brace_count = 1
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            clean_line = line.strip()
            
            if "{" in clean_line: 
                brace_count += clean_line.count("{")
            if end_trigger in clean_line:
                brace_count -= clean_line.count(end_trigger)
                if brace_count == 0:
                    self.current_line += 1
                    break
                    
            block_lines.append(line)
            self.current_line += 1
        return "".join(block_lines)

    def run_file(self, filename):
        if not os.path.exists(filename):
            return False
            
        with open(filename, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

        self.current_line = 0
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            clean_line = line.strip()

            if not clean_line or clean_line.startswith("//") or clean_line.startswith("/*"):
                self.current_line += 1
                continue

            # --- 1. Класс звука и робота ---
            if clean_line.startswith("class sound {") or clean_line.startswith("class sound{"):
                self.current_line += 1
                sound_code = self.execute_block_content()
                self.process_sound(sound_code)

            # --- 2. Вывод текста echo ---
            elif clean_line.startswith("echo "):
                print(self.replace_variables(clean_line[5:].strip()))
                self.current_line += 1

            # --- 3. Переменные let ---
            elif clean_line.startswith("let "):
                match = re.match(r"let\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)", clean_line)
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2).strip("'\" ")
                    self.variables[var_name] = self.replace_variables(var_value)
                self.current_line += 1

            # --- 4. Условия if / else ---
            elif clean_line.startswith("if "):
                match = re.match(r"if\s+(.*)\s*\{", clean_line)
                if match:
                    condition = match.group(1)
                    self.current_line += 1
                    if self.evaluate_condition(condition):
                        continue
                    else:
                        self.skip_block()
                        if self.current_line < len(self.lines) and "else" in self.lines[self.current_line]:
                            self.current_line += 1
                            self.skip_block()
                else:
                    self.current_line += 1

            elif clean_line.startswith("else"):
                self.current_line += 1
                self.skip_block()

            # --- 5. Подключение файлов join ---
            elif clean_line.startswith("join "):
                match = re.match(r"join\s+['\"](.*?)['\"]\s*\{", clean_line)
                if match:
                    file_target = self.replace_variables(match.group(1))
                    self.current_line += 1
                    inner_code = self.execute_block_content()
                    
                    if "write" in inner_code:
                        text_to_write = re.search(r"write\s+['\"](.*?)['\"]", inner_code)
                        if text_to_write:
                            with open(file_target, "w", encoding="utf-8") as wf:
                                wf.write(self.replace_variables(text_to_write.group(1)))
                else:
                    self.current_line += 1

            # --- 6. База данных database() ---
            elif clean_line.startswith("database("):
                self.current_line += 1
                _ = self.execute_block_content(end_trigger=")")
                print("[aScript DB] База данных инициализирована.")

            # --- 7. Системная инфа ---
            elif clean_line == "show sys.info":
                print(f"\n--- aScript System Info ---\nUser: {self.variables['User']}\nOS: {sys.platform}\n")
                self.current_line += 1

            # --- 8. Поиск/открытие файлов по маске ---
            elif clean_line.startswith("open "):
                raw_path = clean_line[5:].strip()
                resolved_path = self.replace_variables(raw_path)
                print(f"[aScript] Сканирование директории: {resolved_path}")
                files = glob.glob(resolved_path)
                if files:
                    for f in files:
                        print(f"-> Доступ открыт: {os.path.basename(f)}")
                else:
                    print("-> Файлы не найдены.")
                self.current_line += 1

            # --- 9. Окна и графика window() ---
            elif clean_line.startswith("window("):
                self.current_line += 1
                ui_code = self.execute_block_content(end_trigger=")")
                self.render_window(ui_code)
            else:
                self.current_line += 1
        return True

    def process_sound(self, code):
        lines = code.split("\n")
        for l in lines:
            l = l.strip()
            if l.startswith("echo "):
                text_to_speak = self.replace_variables(l[5:].strip().strip("'\""))
                print(f"[Робот говорит]: {text_to_speak}")
                if self.tts_engine:
                    self.tts_engine.say(text_to_speak)
                    self.tts_engine.runAndWait()
            
            elif l.startswith("tone "):
                parts = l[5:].split()
                if len(parts) >= 1:
                    freq = int(self.replace_variables(parts[0]))
                    if sys.platform == "win32":
                        import winsound
                        winsound.Beep(freq, 400)

    def render_window(self, full_code):
        css_style = ""
        html_content = full_code

        style_match = re.search(r"const style\s*=\s*`([\s\S]*?)`", full_code)
        if style_match:
            css_style = style_match.group(1)
            html_content = full_code.replace(style_match.group(0), "")

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ margin: 0; padding: 20px; font-family: 'Segoe UI', sans-serif; background: #111216; color: #fff; display: flex; flex-direction: column; align-items: center; }}
                {css_style}
            </style>
        </head>
        <body>
            {html_content}
            <script>
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                
                function playBeep(freq, vol) {{
                    let osc = audioCtx.createOscillator();
                    let gain = audioCtx.createGain();
                    osc.type = 'sine';
                    osc.frequency.value = freq;
                    gain.gain.value = vol || 0.1;
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);
                    osc.start();
                    setTimeout(() => osc.stop(), 150);
                }}

                function saveToDB(key, val) {{ pywebview.api.save_data(key, val); }}
                function getFromDB(key) {{ pywebview.api.get_data(key).then(alert); }}
            </script>
        </body>
        </html>
        """
        bridge = AScriptBridge()
        webview.create_window("aScript Gaming & Audio Engine", html=html_template, width=900, height=650, js_api=bridge)
        webview.start()

if __name__ == "__main__":
    # --- ТИХАЯ АВТОУСТАНОВКА В PATH ДЛЯ WINDOWS ---
    if sys.platform == "win32":
        import winreg
        import ctypes

        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""

            if exe_dir not in current_path:
                new_path = f"{current_path};{exe_dir}" if current_path else exe_dir
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                winreg.CloseKey(key)
                
                # Обновляем переменные окружения в Windows
                ctypes.windll.user32.SendMessageTimeoutW(
                    0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, ctypes.byref(ctypes.c_long())
                )
                print("[aScript] Путь добавлен в PATH.")
            else:
                winreg.CloseKey(key)
        except:
            pass
    # ----------------------------------------------

    interpreter = AScriptInterpreter()

    # Если файл передан аргументом в консоли (aScript index.asc)
    if len(sys.argv) > 1:
        interpreter.run_file(sys.argv[1])
    else:
        # Если запустили кликом, ищем дефолтные файлы по очереди
        if not interpreter.run_file("index.asc"):
            if not interpreter.run_file("index.ascript"):
                print("Asanali Script (aScript) v1.0")
                print("Использование: aScript <имя_файла.asc>")
                print("Ошибка: Рядом не найден файл index.asc или index.ascript")
                input("\nНажми Enter для выхода...")
