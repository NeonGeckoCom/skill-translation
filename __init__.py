# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from typing import Optional
from ovos_utils import classproperty
from ovos_utils.log import LOG
from ovos_utils.process_utils import RuntimeRequirements
from neon_utils.skills.neon_skill import NeonSkill
from neon_utils.user_utils import get_user_prefs
from neon_utils.language_utils import get_supported_output_langs
from lingua_franca import load_language, get_full_lang_code
from lingua_franca.internal import UnsupportedLanguageError
from lingua_franca.parse import extract_langcode
from lingua_franca.format import pronounce_lang

from ovos_workshop.decorators import intent_handler


class TranslationSkill(NeonSkill):
    def __init__(self, **kwargs):
        NeonSkill.__init__(self, **kwargs)
        self._tts_langs = None
        self._translator_langs = None

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(network_before_load=False,
                                   internet_before_load=False,
                                   gui_before_load=False,
                                   requires_internet=True,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=True)

    @property
    def supported_languages(self) -> Optional[set]:
        """
        Get the set of supported languages (None if not specified)
        """
        try:
            self._tts_langs = self._tts_langs or \
                get_supported_output_langs(False)
            self._translator_langs = self._translator_langs or \
                self.translator.available_languages
        except AttributeError:
            pass
        if not (self._tts_langs and self._translator_langs):
            LOG.warning("TTS and Translator langs not specified. "
                        "Assuming all supported")
            return None
        return set([lang for lang in self._tts_langs if lang in
                    self._translator_langs])

    @intent_handler("translate_phrase.intent")
    def handle_translate_phrase(self, message):
        phrase = message.data.get("phrase")
        language = message.data.get("language")
        LOG.info(f"language={language}|phrase={phrase}")
        load_language(self.lang)
        try:
            short_code, language = self._get_lang_code_and_name(language)
        except UnsupportedLanguageError as e:
            LOG.warning(e)
            short_code = None
        if phrase and short_code:
            if self.supported_languages and \
                    short_code not in self.supported_languages:
                self.speak_dialog("language_not_supported",
                                  {"lang": language})
                return
            try:
                translated = self.translator.translate(phrase, short_code, self.lang)
                gender = "male" if self.voc_match(language, "male") else \
                    "female" if self.voc_match(language, "female") else \
                    get_user_prefs(message)['speech'].get("tts_gender") or \
                    "female"
                LOG.info(f"translated={translated}")
                spoken_lang = pronounce_lang(short_code)
                self.speak_dialog("phrase_in_language", {"phrase": phrase,
                                                         "lang": spoken_lang})
                self.speak(translated, speaker={"language": short_code,
                                                "name": "Neon",
                                                "gender": gender,
                                                "override_user": True})
            except Exception as e:
                LOG.error(e)
                if "not supported" in repr(e):
                    lang = pronounce_lang(short_code)
                    self.speak_dialog("language_not_supported", {"lang": lang})
        else:
            LOG.warning("Failed to extract a valid language")

    def _get_lang_code_and_name(self, request: str) -> (str, str):
        """
        Extract the lang code and pronounceable name from a requested language
        :param request: user requested language
        :returns: lang code and pronounceable language name if found, else None
        """
        load_language(self.lang)

        code = None
        # Manually specified languages take priority
        request_overrides = self.translate_namedvalues("languages.value")
        for lang, c in request_overrides.items():
            if lang in request.lower().split():
                code = c
                break
        if not code:
            # Ask LF to determine the code
            short_code = extract_langcode(request)[0]
            code = get_full_lang_code(short_code)
            if code.split('-')[0] != short_code:
                LOG.warning(f"Got {code} from {short_code}. No valid code")
                code = None

        if not code:
            # Request is not a language, raise an exception
            raise UnsupportedLanguageError(f"No language found in {request}")
        code = code.split('-')[0]
        spoken_lang = pronounce_lang(code)
        return code, spoken_lang

    def stop(self):
        pass

