from deep_translator import GoogleTranslator
from langdetect import detect

class TranslatorEngine:
    def __init__(self):
        self.translator = GoogleTranslator()
        # Mapping for beautiful names to language codes
        self.languages = {
            "Auto Detect": "auto",
            "Vietnamese": "vi",
            "English": "en",
            "Japanese": "ja",
            "Korean": "ko",
            "Chinese (Simplified)": "zh-CN",
            "French": "fr",
            "German": "de",
            "Russian": "ru",
            "Spanish": "es"
        }

    def get_supported_languages(self):
        return list(self.languages.keys())

    def translate(self, text, source_lang_name, target_lang_name):
        try:
            source_code = self.languages.get(source_lang_name, "auto")
            target_code = self.languages.get(target_lang_name, "vi")
            
            translator = GoogleTranslator(source=source_code, target=target_code)
            return translator.translate(text)
        except Exception as e:
            return f"Error: {str(e)}"

    def detect_language(self, text):
        try:
            code = detect(text)
            if code == 'zh-cn': code = 'zh-CN'
            # Map code back to friendly name
            for name, lang_code in self.languages.items():
                if lang_code == code:
                    return name
            return "Auto Detect"
        except:
            return "Auto Detect"

if __name__ == "__main__":
    # Quick test
    engine = TranslatorEngine()
    print(engine.translate("Hello world", "English", "Vietnamese"))
