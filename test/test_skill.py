# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import pytest
import mock

from ovos_bus_client.message import Message
from neon_minerva.tests.skill_unit_test_base import SkillTestCase


class TestSkillMethods(SkillTestCase):
    @classmethod
    @mock.patch('neon_utils.language_utils.get_supported_output_langs')
    def setUpClass(cls, get_langs) -> None:
        get_langs.return_value = {'en', 'es'}
        SkillTestCase.setUpClass()
        cls.skill.config_core['language']['translation_module'] = \
            "libretranslate_plug"
        cls.skill.config_core['language']['detection_module'] = \
            "libretranslate_detection_plug"

    def test_00_skill_init(self):
        real_translator = self.skill._translator_langs
        real_tts = self.skill._tts_langs

        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill
        self.assertIsInstance(self.skill, NeonSkill)

        self.skill._translator_langs = {'tr'}
        self.skill._tts_langs = {'tts'}

        # No translator or tts
        self.assertEqual(self.skill.supported_languages, set())

        # tts, no translator
        self.skill._tts_langs = {'en'}
        self.assertEqual(self.skill.supported_languages, set())

        # tts and translator
        self.skill._tts_langs = {'en', 'es'}
        self.skill._translator_langs = {'en', 'fr'}
        self.assertEqual(self.skill.supported_languages, {'en'})

        self.skill._translator_langs = real_translator
        self.skill._tts_langs = real_tts

    def test_handle_translate_phrase(self):
        # TODO: Mock translator or specify testing endpoint
        valid_phrase = "hello"
        invalid_phrase = ""
        valid_language = "spanish"
        invalid_language = ""
        unsupported_language = "laothian"

        # Invalid language
        self.skill.handle_translate_phrase(Message(
            "test", {"phrase": valid_phrase, "language": invalid_language,
                     "lang": "en-us"}))
        self.skill.speak.assert_not_called()
        self.skill.speak_dialog.assert_not_called()

        # Invalid phrase
        self.skill.handle_translate_phrase(Message(
            "test", {"phrase": invalid_phrase, "language": valid_language,
                     "lang": "en-us"}))
        self.skill.speak.assert_not_called()
        self.skill.speak_dialog.assert_not_called()

        # Invalid phrase and language
        self.skill.handle_translate_phrase(Message(
            "test", {"phrase": invalid_phrase, "language": invalid_language,
                     "lang": "en-us"}))
        self.skill.speak.assert_not_called()
        self.skill.speak_dialog.assert_not_called()

        # Valid phrase and language
        self.skill.handle_translate_phrase(Message(
            "test", {"phrase": valid_phrase, "language": valid_language,
                     "lang": "en-us"}))
        self.skill.speak_dialog.assert_called_once_with(
            "phrase_in_language", {"phrase": "hello", "lang": "Spanish"})

        try:
            self.skill.speak.assert_called_once_with(
                "hola", speaker={"language": "es", "name": "Neon",
                                 "gender": "female", "override_user": True}
            )
        except AssertionError:
            self.skill.speak.assert_called_once_with(
                "Hola", speaker={"language": "es", "name": "Neon",
                                 "gender": "female", "override_user": True}
            )

        # Translation unsupported language
        real_translator = self.skill._translator_langs
        real_tts = self.skill._tts_langs
        self.skill._translator_langs = {'en', 'es'}
        self.skill._tts_langs = {'en', 'es', 'uk'}
        self.skill.handle_translate_phrase(Message(
            "test", {"phrase": valid_phrase, "language": 'ukrainian',
                     "lang": "en-us"}))
        self.skill.speak_dialog.assert_called_with("language_not_supported",
                                                   {'lang': "Ukrainian"})
        # TTS Unsupported language
        self.skill._translator_langs = {'en', 'es', 'fr'}
        self.skill._tts_langs = {'en', 'es', 'uk'}
        self.skill.handle_translate_phrase(Message(
            "test", {"phrase": valid_phrase, "language": 'french',
                     "lang": "en-us"}))
        self.skill.speak_dialog.assert_called_with("language_not_supported",
                                                   {'lang': "French"})

        # Unsupported language
        self.skill.handle_translate_phrase(Message(
            "test", {"phrase": valid_phrase, "language": unsupported_language,
                     "lang": "en-us"}))
        self.skill.speak_dialog.assert_called_with("language_not_supported",
                                                   {"lang": "Laothian"})
        # TODO: Test gender determination

        self.skill._translator_langs = real_translator
        self.skill._tts_langs = real_tts

    def test_get_lang_name_and_code(self):
        from lingua_franca.internal import UnsupportedLanguageError
        # Check all the Coqui TTS Supported Languages
        self.assertEqual(("en", "English"),
                         self.skill._get_lang_code_and_name("english"))
        self.assertEqual(("es", "Spanish"),
                         self.skill._get_lang_code_and_name("spanish"))
        self.assertEqual(("fr", "French"),
                         self.skill._get_lang_code_and_name("french"))
        self.assertEqual(("de", "German"),
                         self.skill._get_lang_code_and_name("german"))
        self.assertEqual(("it", "Italian"),
                         self.skill._get_lang_code_and_name("italian"))
        self.assertEqual(("pl", "Polish"),
                         self.skill._get_lang_code_and_name("polish"))
        self.assertEqual(("uk", "Ukrainian"),
                         self.skill._get_lang_code_and_name("ukrainian"))
        self.assertEqual(("ro", "Romanian"),
                         self.skill._get_lang_code_and_name("romanian"))
        self.assertEqual(("hu", "Hungarian"),
                         self.skill._get_lang_code_and_name("hungarian"))
        self.assertEqual(("el", "Greek"),
                         self.skill._get_lang_code_and_name("greek"))
        self.assertEqual(("sv", "Swedish"),
                         self.skill._get_lang_code_and_name("swedish"))
        self.assertEqual(("bg", "Bulgarian"),
                         self.skill._get_lang_code_and_name("bulgarian"))
        self.assertEqual(("nl", "Dutch"),
                         self.skill._get_lang_code_and_name("dutch"))
        self.assertEqual(("fi", "Finnish"),
                         self.skill._get_lang_code_and_name("finnish"))
        self.assertEqual(("sl", "Slovenian"),
                         self.skill._get_lang_code_and_name("slovenian"))
        self.assertEqual(("lv", "Latvian"),
                         self.skill._get_lang_code_and_name("latvian"))
        self.assertEqual(("et", "Estonian"),
                         self.skill._get_lang_code_and_name("estonian"))
        self.assertEqual(("ga", "Irish"),
                         self.skill._get_lang_code_and_name("irish"))

        # Check LibreTranslate supported languages
        self.assertEqual(("ar", "Arabic"),
                         self.skill._get_lang_code_and_name("arabic"))
        self.assertEqual(("az", "Azerbaijani"),
                         self.skill._get_lang_code_and_name("azerbaijani"))
        self.assertEqual(("zh", "Chinese"),
                         self.skill._get_lang_code_and_name("chinese"))
        self.assertEqual(("cs", "Czech"),
                         self.skill._get_lang_code_and_name("czech"))
        self.assertEqual(("da", "Danish"),
                         self.skill._get_lang_code_and_name("danish"))
        # self.assertEqual(("eo", "Esperanto"),
        #                  self.skill._get_lang_code_and_name("esperanto"))
        # self.assertEqual(("he", "Hebrew"),
        #                  self.skill._get_lang_code_and_name("hebrew"))
        self.assertEqual(("hi", "Hindi"),
                         self.skill._get_lang_code_and_name("hindi"))
        self.assertEqual(("id", "Indonesian"),
                         self.skill._get_lang_code_and_name("indonesian"))
        self.assertEqual(("ja", "Japanese"),
                         self.skill._get_lang_code_and_name("japanese"))
        self.assertEqual(("ko", "Korean"),
                         self.skill._get_lang_code_and_name("korean"))
        self.assertEqual(("fa", "Persian"),
                         self.skill._get_lang_code_and_name("persian"))
        self.assertEqual(("pt", "Portuguese"),
                         self.skill._get_lang_code_and_name("portuguese"))
        self.assertEqual(("ru", "Russian"),
                         self.skill._get_lang_code_and_name("russian"))
        self.assertEqual(("sk", "Slovak"),
                         self.skill._get_lang_code_and_name("slovak"))
        self.assertEqual(("tr", "Turkish"),
                         self.skill._get_lang_code_and_name("turkish"))
        # Check manually specified alternative language requests
        self.assertEqual(("ga", "Irish"),
                         self.skill._get_lang_code_and_name("gaelic"))
        self.assertEqual(("en", "English"),
                         self.skill._get_lang_code_and_name(
                             "australian english"))
        self.assertEqual(("fa", "Persian"),
                         self.skill._get_lang_code_and_name("farsi"))
        with self.assertRaises(UnsupportedLanguageError):
            self.skill._get_lang_code_and_name("nothing")


if __name__ == '__main__':
    pytest.main()
