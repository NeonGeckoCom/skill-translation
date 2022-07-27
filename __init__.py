# -*- coding: utf-8 -*-
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

from neon_utils.skills.neon_skill import NeonSkill, LOG
from neon_utils.user_utils import get_user_prefs
from lingua_franca import load_language
from lingua_franca.parse import extract_langcode
from lingua_franca.format import pronounce_lang

from mycroft.skills.core import intent_handler


class Translation(NeonSkill):
    def __init__(self):
        super(Translation, self).__init__(name="Translation")

    @intent_handler("translate_phrase.intent")
    def handle_translate_phrase(self, message):
        phrase = message.data.get("phrase")
        language = message.data.get("language")
        LOG.info(f"language={language}|phrase={phrase}")
        load_language(self.lang)
        if language:
            short_code = extract_langcode(language)[0]
        else:
            short_code = None
        if phrase and short_code:
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

    def stop(self):
        pass


def create_skill():
    return Translation()
