import os
import re
import sys
import glob
import json
import subprocess
import webview
import pyttsx3


class AScriptBridge:
    """Мост для связи JavaScript внутри window() с Python-базой данных"""
    def __init__(self, db_path="ascript_db.json"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def save_data(self, key, value):
        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[key] = value
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return f"[database] Сохранено: {key}"

    def get_data(self, key):
        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, "Не найдено")


class AScriptInterpreter:
    def __init__(self):
        self.variables = {
            'User': os.getlogin(),
            'ARCH': sys.platform,
            'VERSION': '2.1.0-TS'
        }
        self.interfaces = {}
        self.lines = []
        self.current_line = 0

        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 170)
        except Exception:
            self.tts_engine = None

    def strip_comments(self, code: str) -> str:
        parts = re.split(r'(window\s*\(.*?\))', code, flags=re.DOTALL)
        processed_parts = []

        for part in parts:
            if part.startswith("window"):
                processed_parts.append(part)
            else:
                cleaned = re.sub(r'/\*[\s\S]*?\*/', '', part)
                cleaned = re.sub(r'//.*', '', cleaned)
                processed_parts.append(cleaned)

        return "".join(processed_parts)

    def replace_variables(self, text: str) -> str:
        def replace_nested(match):
            obj_name = match.group(1)
            prop_name = match.group(2)
            if obj_name in self.variables and isinstance(self.variables[obj_name], dict):
                return str(self.variables[obj_name].get(prop_name, f"${obj_name}.{prop_name}"))
            return match.group(0)

        text = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)', replace_nested, text)

        for var, val in self.variables.items():
            if not isinstance(val, dict):
                text = text.replace(f"${var}", str(val))

        return text

    def check_type(self, val_str: str, expected_type: str) -> tuple[bool, object]:
        val_str = val_str.strip()
        expected_type = expected_type.strip()

        if expected_type == "string":
            if (val_str.startswith('"') and val_str.endswith('"')) or \
               (val_str.startswith("'") and val_str.endswith("'")):
                return True, val_str[1:-1]
            return False, "Значение должно быть строкой в кавычках"

        elif expected_type == "number":
            if val_str.isdigit():
                return True, int(val_str)
            try:
                return True, float(val_str)
            except ValueError:
                return False, "Значение должно быть числом"

        elif expected_type == "boolean":
            if val_str in ["true", "false"]:
                return True, val_str == "true"
            return False, "Значение должно быть true или false"

        return True, val_str

    def evaluate_condition(self, condition_str: str) -> bool:
        condition_str = self.replace_variables(condition_str)
        if "==" in condition_str:
            left, right = condition_str.split("==")
            return left.strip().strip("'\"") == right.strip().strip("'\"")
        if "!=" in condition_str:
            left, right = condition_str.split("!=")
            return left.strip().strip("'\"") != right.strip().strip("'\"")
        return False

    def skip_block(self):
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

    def execute_block_content(self, end_trigger="}") -> str:
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

    def parse_object(self, raw_str: str) -> dict:
        json_like = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', raw_str)
        json_like = json_like.replace("true", "true").replace("false", "false")
        return json.loads(json_like)

    def run_file(self, filename: str) -> bool:
        if not os.path.exists(filename):
            return False

        with open(filename, 'r', encoding='utf-8') as f:
            raw_code = f.read()

        clean_code = self.strip_comments(raw_code)
        self.lines = [line for line in clean_code.splitlines() if line.strip()]

        self.current_line = 0
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            clean_line = line.strip()

            if clean_line.startswith("interface "):
                match = re.match(r"interface\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{", clean_line)
                if match:
                    if_name = match.group(1)
                    self.current_line += 1
                    if_body = self.execute_block_content()
                    self.interfaces[if_name] = if_body
                else:
                    self.current_line += 1

            elif clean_line.startswith("let ") or clean_line.startswith("const "):
                content = re.sub(r'^(let|const)\s+', '', clean_line)
                match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)(?:\s*:\s*([a-zA-Z0-9_<>|]+))?\s*=\s*(.*)", content)
                
                if match:
                    var_name = match.group(1)
                    var_type = match.group(2)
                    raw_val = match.group(3).strip()

                    if raw_val.startswith("{"):
                        obj_str = raw_val
                        while not obj_str.endswith("}") and self.current_line + 1 < len(self.lines):
                            self.current_line += 1
                            obj_str += " " + self.lines[self.current_line].strip()
                        
                        try:
                            parsed_obj = self.parse_object(obj_str)
                            self.variables[var_name] = parsed_obj
                        except Exception as e:
                            print(f"[aScript Error] Ошибка синтаксиса объекта '{var_name}': {e}")
                            sys.exit(1)

                    else:
                        if var_type:
                            is_valid, parsed_val = self.check_type(raw_val, var_type)
                            if not is_valid:
                                print(f"[TypeError] Ошибка в строке {self.current_line + 1}: '{var_name}' ожидает тип '{var_type}', получено: {raw_val}")
                                sys.exit(1)
                            self.variables[var_name] = parsed_val
                        else:
                            var_value = raw_val.strip("'\" ")
                            self.variables[var_name] = self.replace_variables(var_value)

                self.current_line += 1

            elif clean_line.startswith("echo "):
                print(self.replace_variables(clean_line[5:].strip()))
                self.current_line += 1

            elif clean_line.startswith("cli."):
                if clean_line.startswith("cli.args"):
                    print(f"[CLI Args]: {sys.argv[1:]}")
                elif clean_line.startswith("cli.exec "):
                    cmd = self.replace_variables(clean_line[9:].strip().strip("'\""))
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    print(res.stdout)
                elif clean_line == "cli.exit()":
                    sys.exit(0)
                self.current_line += 1

            elif clean_line.startswith("class sound {") or clean_line.startswith("class sound{"):
                self.current_line += 1
                sound_code = self.execute_block_content()
                self.process_sound(sound_code)

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

            elif clean_line.startswith("database("):
                self.current_line += 1
                _ = self.execute_block_content(end_trigger=")")
                print("[aScript DB] База данных инициализирована.")

            elif clean_line == "show sys.info":
                print(f"\n--- aScript System Info ---\nUser: {self.variables['User']}\nOS: {sys.platform}\nVersion: {self.variables['VERSION']}\n")
                self.current_line += 1

            elif clean_line.startswith("open "):
                raw_path = clean_line[5:].strip()
                resolved_path = self.replace_variables(raw_path)
                files = glob.glob(resolved_path)
                if files:
                    for f in files:
                        print(f"-> Доступ открыт: {os.path.basename(f)}")
                else:
                    print("-> Файлы не найдены.")
                self.current_line += 1

            elif clean_line.startswith("window("):
                self.current_line += 1
                ui_code = self.execute_block_content(end_trigger=")")
                self.render_window(ui_code)
            else:
                self.current_line += 1
        return True

    def process_sound(self, code: str):
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

    def render_window(self, full_code: str):
        # Переменные AsanaliScript ($var) парсятся напрямую в HTML
        html_content = self.replace_variables(full_code)

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
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
        webview.create_window("aScript Engine v2.1", html=html_template, width=900, height=650, js_api=bridge)
        webview.start()


if __name__ == "__main__":
    if sys.platform == "win32":
        import winreg
        import ctypes

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
                ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, ctypes.byref(ctypes.c_long()))
            else:
                winreg.CloseKey(key)
        except Exception:
            pass

    interpreter = AScriptInterpreter()

    if len(sys.argv) > 1:
        interpreter.run_file(sys.argv[1])
    else:
        for default_file in ["index.asc", "index.ascript", "main.asc", "main.ascript"]:
            if interpreter.run_file(default_file):
                sys.exit(0)

        print("Asanali Script (aScript) v2.1 TS Engine")
        print("Использование: aScript <файл.asc|файл.ascript>")
        input("\nНажми Enter для выхода...")
