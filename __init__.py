# -*- coding: utf-8 -*-
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

import pickle
# import time
import urllib.request

from os.path import join, abspath, dirname, isfile
from adapt.intent import IntentBuilder
from bs4 import BeautifulSoup
from neon_utils import web_utils
from neon_utils.parse_utils import clean_quotes

# from NGI.utilities import tkHelper
from mycroft_bus_client import Message
from mycroft.skills.core import intent_handler
from neon_utils.skills.neon_skill import NeonSkill, LOG


class TranslationNGI(NeonSkill):
    def __init__(self):
        super(TranslationNGI, self).__init__(name="TranslationNGI")
        self.region = 'us-west-2'
        self.check_for_signal("TR_secondary_language_options")

        self.voc_path = join(dirname(__file__), "vocab", "en-us", "language.voc")
        # self.temp_dir = self.configuration_available['dirVars']['tempDir']
        self.default_gender = "female"
        self.extra_default = {"english": "en-us", "portuguese": "pt-pt", "spanish": "es-mx",
                              "chinese": "zh-zh", 'french': "fr-fr", "welsh": "cy-gb"}
        # self.tts_language = self.user_info_available['speech']["tts_language"].lower()
        # self.tts_gender = self.user_info_available['speech']["tts_gender"] \
        #     if self.user_info_available['speech']["tts_gender"] else self.default_gender
        # self.two_gender = self.user_info_available['speech']["secondary_tts_gender"] \
        #     if self.user_info_available['speech']["secondary_tts_gender"] else self.default_gender
        # self.voice = self.user_info_available['speech']["neon_voice"]
        self.alreadySpoke = False

        if self.check_for_signal("TTS_update") or not isfile(self.voc_path) or not \
                isfile(join(abspath(dirname(__file__)), 'language_from_polly.txt')):
            self.get_entity()
            # LOG.info("\n \n getting voc or init \n \n ")
        else:
            with open(join(abspath(dirname(__file__)), 'language_from_polly.txt'),
                      'rb') as language_from_polly_file:
                self.language_list = pickle.load(language_from_polly_file)
                # LOG.info(self.ll)
                # LOG.info(type(self.ll))

        if self.check_for_signal("STT_update") or not isfile(join(abspath(dirname(__file__)),
                                                                   "vocab", "en-us", "stt_language.voc")) \
                or not isfile(join(abspath(dirname(__file__)), 'language_from_stt.txt')):
            self.stt_dict = {}
            self.get_entity(stt=True)
            LOG.info("\n \n getting voc or init \n \n ")
        else:
            with open(join(abspath(dirname(__file__)), 'language_from_stt.txt'),
                      'rb') as language_from_stt:
                self.stt_dict = pickle.load(language_from_stt)

    def initialize(self):
        self.disable_intent("I_prefer")
        self.disable_intent("LangMenu")

    @intent_handler(IntentBuilder("OnlyOne").require("OnlyOne"))
    def handle_no_secondary(self, message):
        if self.server:
            user_dict = self.build_user_dict(message)
            user_dict['secondary_tts_language'] = user_dict['tts_language']
            user_dict['secondary_tts_gender'] = user_dict['tts_gender']
            user_dict['secondary_neon_voice'] = ""

            LOG.info(user_dict)
            self.socket_emit_to_server("update profile", ["skill", user_dict,
                                                          message.context["klat_data"]["request_id"]])
        else:
            self.user_config.update_yaml_file("speech", "secondary_tts_language", "", True)
            self.user_config.update_yaml_file("speech", "secondary_neon_voice", "", True)
            self.user_config.update_yaml_file("speech", "secondary_tts_gender", "", final=True)
            self.bus.emit(Message('check.yml.updates',
                                  {"modified": ["ngi_user_info"]}, {"origin": "translation.neon"}))

            # self.create_signal("TTS_voice_switch")
        self.speak_dialog("OnlyOneLanguage", private=True)

    @intent_handler(IntentBuilder("SettingsLanguage").require("Settings"))
    def handle_settings(self, message):
        preference_speech = self.preference_speech(message)
        lang = preference_speech["tts_language"].lower()
        lang2 = preference_speech["secondary_tts_language"].lower()

        language_name = list(self.language_list.keys())[list(self.language_list.values()).index(lang)]
        tts_gender = preference_speech["tts_gender"]

        try:
            secondary_language_name = list(self.language_list.keys())[list(self.language_list.values()).index(lang2)]
            secondary_tts_gender = preference_speech["secondary_tts_gender"]
        except Exception as e:
            LOG.debug(e)
            secondary_language_name = None
            secondary_tts_gender = None

        self.speak_dialog("LanguageSetting", {"primary": "primary",
                                              "gender": tts_gender,
                                              "language": language_name.title()}, private=True) if \
            language_name and tts_gender else LOG.error("No primary language settings found!")

        if secondary_language_name and secondary_tts_gender \
                and secondary_language_name != language_name and secondary_tts_gender != tts_gender:
            self.speak_dialog("LanguageSetting", {"primary": "secondary",
                                                  "gender": secondary_tts_gender,
                                                  "language": secondary_language_name.title()}, private=True)
        else:
            LOG.info("One language only")

    @intent_handler(IntentBuilder("STTChange").optionally("Neon").
                    require("TalkToYouKeyword").optionally("gender").require("stt_language")
                    .optionally("gender"))
    def handle_stt_language(self, message):
        LOG.info(str(message))
        from pprint import pprint
        pprint(vars(message))
        language = self.stt_dict[message.data.get("stt_language")]
        if language:
            LOG.info(language)
        else:
            for lang in self.stt_dict:
                if message.data.get("stt_language") in lang:
                    language = self.stt_dict[lang]
                    break
        self.speak_dialog("ChangeSttLanguage", {"language": message.data.get("stt_language")}, private=True)
        self._write_stt_change(language, message)

    def _check_if_valid_language(self, language):
        LOG.info(language)
        final_language = ""
        if language:
            split_language = language.split(" ")
            word_count = len(split_language)
            LOG.info(split_language)

            if word_count > 1:
                final_language = {a: b for (a, b) in list(self.language_list.items()) if
                                  a == (split_language[0] + " " + split_language[1]) or
                                  a == split_language[1] + " " + split_language[0]}
                LOG.info(final_language)
                LOG.info(split_language[0])

            if not final_language:
                final_language = {a: b for (a, b) in list(self.language_list.items()) if a == language}
                for i in range(word_count):
                    LOG.info(final_language)
                    if final_language:
                        break
                    final_language = {a: b for (a, b) in list(self.language_list.items()) if language in a
                                      or split_language[i] == a}
                    LOG.info(split_language[i])
        return final_language if final_language else {"not_valid": ""}

    @intent_handler(IntentBuilder("SetMyLanguage").optionally("Neon").require("first_language").optionally("gender")
                    .optionally("Two").require("second_language").optionally("gender").build())
    def handle_set_my_language(self, message):
        """
        Intent handler for regex matched primary and secondary language change.
        Handles something like "I want to set my primary language to French and set my secondary language to English"
        @param message: messagebus object associated with intent match
        @return:
        """

        LOG.info((message.data.get("utterance")))
        LOG.info(message.data.get('first_language'))
        LOG.info(message.data.get('second_language'))
        primary = self._check_if_valid_language(message.data.get('first_language'))
        secondary = self._check_if_valid_language(message.data.get('second_language'))
        if not primary and not secondary:
            self.speak_dialog('NotValidLanguage', {"language": "either of your requested languages"}, private=True)
            return

        LOG.info(primary)
        LOG.info(secondary)
        gender = [x for x in message.data.get("utterance").split(" ") if x in ["male", "female"]]
        LOG.info(gender)
        primary, secondary = self._parse_two_languages([next(iter(primary)), next(iter(secondary))],
                                                       gender, message)
        LOG.info(f"{primary} | {secondary}")
        if not primary:
            # if not silent:
            self.speak_dialog('NotValidLanguage', {"language": "your requested primary language"}, private=True)
            self._finish_language_change(message, second=secondary)
            return
        if not secondary:
            # if not silent:
            self.speak_dialog('NotValidLanguage', {"language": "your requested secondary language"}, private=True)
            self._finish_language_change(message, first=primary)
            return
        LOG.info(primary)
        LOG.info(secondary)
        self._finish_language_change(message, first=primary, second=secondary)

    @intent_handler(IntentBuilder("SetMySecondaryLanguage").optionally("Neon").require("second_language")
                    .optionally("gender").build())
    def handle_set_my_secondary(self, message):
        """
        Intent handler for regex matched secondary language change.
        Handles something like "I want to set my secondary language to English"
        @param message: messagebus object associated with intent match
        @return:
        """
        LOG.info((message.data.get("utterance")))
        silent = "silent" in message.data.get("utterance")
        requested_language = message.data.get('second_language')
        LOG.info(requested_language)
        secondary = self._check_if_valid_language(message.data.get('second_language'))
        if secondary:
            gender = [x for x in message.data.get("utterance").split(" ") if x in ["male", "female"]]
            if not gender:
                gender = [self.default_gender]

            secondary = [next(iter(secondary)), gender[0]]
            if secondary[0] == "not_valid":
                if not silent:
                    self.speak_dialog('NotValidLanguage', {"language": requested_language}, private=True)
            else:
                self._finish_language_change(message, second=secondary)
        else:
            if not silent:
                self.speak_dialog('NotValidLanguage', {"language": "your requested secondary language"}, private=True)

    @intent_handler(IntentBuilder("SetMyPrimaryLanguage").optionally("Neon").require("first_language")
                    .optionally("gender").build())
    def handle_set_my_primary(self, message):
        """
        Intent handler for regex matched primary and secondary language change.
        Handles something like "I want to set my primary language to French"
        @param message: messagebus object associated with intent match
        @return:
        """
        if "secondary" in message.data.get("utterance"):
            LOG.info(message.data.get("utterance"))
            message.data["second_language"] = str(message.data.get("utterance")).split("secondary", 1)[1]
            LOG.info(message.data.get("second_language"))
            self.handle_set_my_language(message)
            return
        requested_language = message.data.get('first_language')
        LOG.info((message.data.get("utterance")))
        LOG.info(requested_language)
        silent = "silent" in message.data.get("utterance")
        LOG.info(silent)
        primary = self._check_if_valid_language(requested_language)
        if primary:
            gender = [x for x in message.data.get("utterance").split(" ") if x in ["male", "female"]]
            if not gender:
                gender = [self.default_gender]
            primary = [next(iter(primary)), gender[0]]
            LOG.info(primary)
            if primary[0] == "not_valid":
                if not silent:
                    self.speak_dialog('NotValidLanguage', {"language": requested_language}, private=True)
            else:
                self._finish_language_change(message, first=primary)
        else:
            if not silent:
                self.speak_dialog('NotValidLanguage', {"language": message.data.get('first_language')}, private=True)

    @intent_handler(IntentBuilder("TalkToMeKeyword").optionally("Neon").
                    require("TalkToMeKeyword").optionally("Two").optionally("gender").require("language")
                    .optionally("gender").optionally("Two").optionally("language").optionally("gender"))
    def handle_talk_to_me(self, message):
        LOG.debug(f"DM: {message.data}")

        LOG.debug(f'DM: {message.data.get("utterance").split()}')
        gender = message.data.get("gender", self.default_gender)

        # This is the secondary language only
        if "also" in str(message.data.get("utterance")).split():
            LOG.debug(f"add secondary language: {message.data}")
            primary = None
            secondary = [message.data.get("language"), gender]
        # This is two languages, parse them
        elif "and" in str(message.data.get("utterance")).split():
            # Handle two languages (i.e. "speak to me in english and spanish")
            LOG.info(message.data.get("utterance").split(" "))
            gender = [x for x in message.data.get("utterance").split(" ") if x in ["male", "female"]]
            primary, secondary = self._parse_two_languages([x for x in message.data.get("utterance").split(" ")
                                                            if x in self.language_list.keys()], gender, message) \
                if gender else self._parse_two_languages([x for x in message.data.get("utterance").split(" ") if x in
                                                          self.language_list.keys()], message=message)
        # This is the primary language only
        else:
            primary = [message.data.get("language"), gender]
            secondary = None
        LOG.info(f"{primary} | {secondary}")
        if not primary and not secondary:
            LOG.warning(f"No language found in {message.data}")
            return
        self._finish_language_change(message, primary, secondary)

    def _finish_language_change(self, message, first=None, second=None):
        """
        Finish changing languages after utterance has been parsed and languages are determined
        @param message (Message): message object associated with intent match
        @param first (list): first language data
        @param second (list): second language data
        @return: None
        """
        # Determine if second language should be cleared
        if "only" in str(message.data.get("utterance")).split():
            overwrite_second = True
        else:
            overwrite_second = False

        self.create_signal("TTS_voice_switch")  # TODO: Depreciated as of Core 2103 DM
        # utt = str(message.data.get("utterance"))
        LOG.debug(f"{first} | {second}")  # ['japanese', 'female'] | ['english', 'female']

        # Get languages and genders for primary/secondary languages
        primary_gender, second_gender, primary_language, second_language = None, None, None, None
        if first and first[1] in ("male", "female"):
            primary_gender = first[1]
            primary_language = first[0]
        elif first:
            primary_gender = message.data.get("gender", self.default_gender)
            primary_language = message.data.get("language")
        if second and second[1] in ("male", "female"):
            second_gender = second[1]
            second_language = second[0]
        elif second:
            second_gender = message.data.get("gender", self.default_gender)
            second_language = message.data.get("language")

        options_available = False
        options_language = None

        # Get language code for primary language
        if first:
            proposed = primary_language
            LOG.info(f"proposed in self.language_list={proposed in self.language_list}")
            LOG.info(f"proposed in self.extra_default={proposed in self.extra_default}")
            options = {x: y for (x, y) in list(self.language_list.items()) if proposed in x and x not in
                       self.extra_default}
            LOG.info(f"DM: {options}")
            LOG.info(f"genders={primary_gender}, {second_gender}")

            default_options = {x: y for (x, y)
                               in list(self.extra_default.items()) if x == proposed or proposed in x}
            LOG.debug(f"DM: default_options={default_options}")
            if len(options) > 1:
                if default_options:
                    first[0] = default_options[proposed]
                    if not self.server:
                        options_language = proposed
                        self.options = options
                        options_available = True
            else:
                if proposed in default_options:
                    first[0] = default_options[proposed]
                elif proposed in options:
                    first[0] = options[proposed]
                elif proposed in self.extra_default:
                    first[0] = self.extra_default[proposed]
                else:
                    LOG.error(f"{proposed} not found in languages!")
                    return

        # Get language code for secondary language
        if second:
            proposed = second_language
            LOG.info(f"proposed in self.language_list={proposed in self.language_list}")
            LOG.info(f"proposed in self.extra_default={proposed in self.extra_default}")
            options = {x: y for (x, y) in list(self.language_list.items()) if proposed in x and x not in
                       self.extra_default}
            LOG.info(f"DM: {options}")
            LOG.info(f"genders={primary_gender}, {second_gender}")

            default_options = {x: y for (x, y)
                               in list(self.extra_default.items()) if x == proposed or proposed in x}
            LOG.debug(f"DM: default_options={default_options}")
            if len(options) > 1:
                if default_options:
                    second[0] = default_options[proposed]
                    if not self.server and not first:
                        self.create_signal("TR_secondary_language_options")
                        self.options = options
                        options_language = proposed
                        options_available = True
            else:
                if proposed in default_options:
                    second[0] = default_options[proposed]
                elif proposed in options:
                    second[0] = options[proposed]
                elif proposed in self.extra_default:
                    second[0] = self.extra_default[proposed]
                else:
                    LOG.error(f"{proposed} not found in languages!")
                    return

        LOG.debug(f"{first} | {second}")
        self.switch_tts_voice(first, second, message, overwrite_second)

        # Language options are available
        if options_available:
            # two languages with options for one
            if first and second:
                self.speak_dialog("SwitchPrimaryAndSecondary", {"primary_gender": primary_gender,
                                                                "primary_language": primary_language,
                                                                "second_gender": second_gender,
                                                                "second_language": second_language}, private=True)
                self.speak_dialog("TwoLanguagesDialectOptions", {"language": options_language.capitalize()},
                                  True, private=True)
            # one language with options
            else:
                self.speak_dialog("SwitchLanguageDialectOptions", {"language": options_language.capitalize()},
                                  True, private=True)
            self.enable_intent("LangMenu")
            self.request_check_timeout(self.default_intent_timeout, "LangMenu")

        # Standard switch language dialog
        else:
            if first and second:
                self.speak_dialog("SwitchPrimaryAndSecondary", {"primary_gender": primary_gender,
                                                                "primary_language": primary_language,
                                                                "second_gender": second_gender,
                                                                "second_language": second_language}, private=True)
            elif first:
                self.speak_dialog("SwitchLanguage", {"language": primary_language,
                                                     "gender": primary_gender,
                                                     "primary": "primary"}, private=True)
            elif second:
                self.speak_dialog("SwitchLanguage", {"language": second_language,
                                                     "gender": second_gender,
                                                     "primary": "secondary"}, private=True)

    @intent_handler(IntentBuilder("SetPreferredLanguage").optionally("Neon").require("PreferredLanguage")
                    .require("language").build())
    def handle_set_preferred(self, message):
        """
        Intent to set a "preferred" language to be used for stt and tts
        @param message: message object associated with intent match
        @return:
        """
        self.create_signal("TTS_voice_switch")  # TODO: Depreciated as of Core 2103 DM
        new_lang = self._check_if_valid_language(message.data.get('language'))
        LOG.info(new_lang)
        language = list(new_lang.values())[0]
        gender = self.preference_speech(message).get("tts_gender", self.default_gender)
        self._write_stt_change(language, message, do_emit=False)
        self.switch_tts_voice([language, gender], message=message, overwrite_second=True)
        self.speak_dialog("ChangePreferredLanguage", {"language": list(new_lang.keys())[0].capitalize()}, private=True)

    @intent_handler(IntentBuilder("TranslatePhrase").optionally("Neon").
                    require("Translate").require("language").optionally("gender"))
    def handle_translate_phrase(self, message):
        utt = message.data.get("utterance")
        language = message.data.get("language")
        gender = message.data.get("gender", self.preference_speech(message)["tts_gender"])
        # Trim off language for "translate [phrase] to [lang]"
        words: list = utt.split()
        language_idx = words.index(language)
        # Remove 'to language'
        words.pop(language_idx)
        words.pop(language_idx - 1)
        request = " ".join(words)
        LOG.debug(request)
        proposed = language

        options = {x: y for (x, y) in list(self.language_list.items()) if proposed in x and x not in
                   self.extra_default}
        LOG.info(f"DM: {options}")
        default_options = {x: y for (x, y)
                           in list(self.extra_default.items()) if x == proposed or proposed in x}

        LOG.debug(f"DM: {proposed}")
        LOG.debug(request)
        phrase_to_say = request.replace(message.data.get("Translate", ''), '').replace(message.data.get("Neon", ''), "")
        LOG.debug(f"DM: {phrase_to_say}")
        phrase_to_say = phrase_to_say.strip()
        LOG.info(phrase_to_say)
        lang = options.get(proposed)
        if not lang:
            lang = default_options.get(proposed)

        # LOG.info(list(self.language_list.keys())[list(self.language_list.values()).index(lang)].title())
        self.speak_dialog('WordInLanguage',
                          {'word': phrase_to_say.strip(),
                           'language': list(self.language_list.keys())[
                               list(self.language_list.values()).index(lang)].title().capitalize()})
        if gender:
            tts_gender = gender
        else:
            tts_gender = self.default_gender
        translated = clean_quotes(self.translator.translate(phrase_to_say, lang, "en"))  # TODO: Internal lang DM
        LOG.info(translated)
        if self.gui_enabled:
            self.gui.show_text(translated, phrase_to_say)
            self.clear_gui_timeout()
        self.speak(translated, speaker={"name": "Neon",
                                        "language": lang,
                                        "gender": tts_gender,
                                        "override_user": True,
                                        "translated": True},
                   meta={"untranslated": phrase_to_say,
                         "is_translated": True})

    def _parse_two_languages(self, languages, gender=None, message=None):
        """
        Internal function to handle parsing languages from an utterance
        @param languages: parsed list of languages to use
        @param gender: passed list of genders to use
        @param message: message associated with this request
        @return: [primary lang, primary gender], [second lang, second gender]
        """
        LOG.info(languages)
        LOG.info(gender)
        utterance = message.data.get("utterance")
        LOG.info(utterance)
        if len(languages) != 2:
            self.speak_dialog("TwoLanguageError", private=True)
            return
        if message and not gender:
            speech = self.preference_speech(message)
            primary_pair = [languages[0], speech.get("tts_gender", self.default_gender)]
            secondary_pair = [languages[1], speech.get("secondary_tts_gender", self.default_gender)]
            for pair in (primary_pair, secondary_pair):
                if pair[1] not in ("male", "female"):
                    pair[1] = self.default_gender
            # LOG.debug(primary_pair)
            # LOG.debug(secondary_pair)
        elif gender:
            LOG.info("has gender")
            LOG.info(gender)
            LOG.info(len(gender))
            LOG.info(gender[0])
            if len(gender) == 2:
                primary_pair = [languages[0], gender[0]]
                secondary_pair = [languages[1], gender[1]]
            else:
                primary_pair = [languages[0], self.default_gender]
                secondary_pair = [languages[1], self.default_gender]
                gender = str(gender[0])
                LOG.info("has gender" + gender)
                if (str(languages[0]) + " " + gender or gender + " " + str(languages[0])) in utterance:

                    primary_pair = [languages[0], gender]
                    secondary_pair = [languages[1], self.default_gender]
                    LOG.info(primary_pair)
                    LOG.info(secondary_pair)
                elif len(languages[0].split()) > 1:
                    if (languages[0].split(" ")[0] + " " + gender or gender + " " + languages[0].
                            split(" ")[0] or languages[0].split(" ")[1] + " " + gender or gender + " " + languages[0].
                            split(" ")[1]) in utterance:
                        LOG.info(primary_pair)
                        LOG.info(secondary_pair)
                        primary_pair = [languages[0], gender]
                        secondary_pair = [languages[1], self.default_gender]
                else:
                    LOG.info(primary_pair)
                    LOG.info(secondary_pair)
                    primary_pair = [languages[0], self.default_gender]
                    secondary_pair = [languages[1], gender]
                    LOG.info(primary_pair)
                    LOG.info(secondary_pair)
        else:
            LOG.warning(f"No gender info available! Fallback to default. message={message.data}")
            primary_pair = [languages[0], self.default_gender]
            secondary_pair = [languages[1], self.default_gender]

        LOG.info(primary_pair)
        LOG.info(secondary_pair)
        if primary_pair[0] != "not_valid" and secondary_pair[0] != "not_valid":
            return primary_pair, secondary_pair
        else:
            LOG.error(f"Invalid language setting: primary={primary_pair} secondary={secondary_pair}")
            if (primary_pair[0]) == "not_valid":
                return "", secondary_pair
            return primary_pair, ""

    @intent_handler(IntentBuilder("LangMenu").optionally("Neon").require("ShowLanguageMenu"))
    def lang_menu(self, message):  # TODO: Handle in converse DM
        self.disable_intent("LangMenu")
        self.speak_dialog("LanguageMenu", private=True)
        # self.create_signal("TK_active")
        self.multiple_options()

    @intent_handler(IntentBuilder("I_prefer").optionally("Neon").
                    require("I_prefer").optionally("gender").optionally("language")
                    .optionally("gender"))
    def choose_lang(self, message=None, selection_made=None):
        self.create_signal("TTS_voice_switch")  # TODO: Depreciated as of Core 2103 DM
        preference_speech = self.preference_speech(message)
        self.check_for_signal("TK_active")
        self.bus.emit(Message("mycroft.stop"))
        if message:
            gender_choice = message.data.get("gender", self.default_gender)
        else:
            gender_choice = self.default_gender
        proposed = str(message.data.get("language")) if not selection_made else selection_made
        LOG.info(proposed)
        if len(proposed.split()) > 1:
            if proposed.split()[1] in ["english", "spanish", "french", "portuguese", "chinese"]:
                proposed = " ".join([proposed.split()[1], proposed.split()[0]])
        if self.options[proposed]:
            if not self.check_for_signal("TR_secondary_language_options"):
                gender_choice = preference_speech['tts_gender'] if not gender_choice else gender_choice
                primary = [self.options[proposed], gender_choice]
                secondary = None
            else:
                gender_choice = preference_speech['secondary_tts_gender'] if not \
                    gender_choice else gender_choice
                primary = None
                secondary = [self.options[proposed], gender_choice]
                # self.switch_tts_voice(self.options[proposed], self.gender_choice, secondary=True, message=message)
            LOG.debug(f"Update: {primary} | {secondary}")
            self.switch_tts_voice(primary, secondary, message, False)
            self.speak_dialog("Confirmed", private=True)
            self.disable_intent("I_prefer")
        else:
            self.speak_dialog("SelectionNotValid", private=True)

    def get_entity(self, stt=None):
        # TODO: This should be per-engine DM
        if stt:
            LOG.info("Getting Switch STT update")
            stt_dict = self.local_config.get("sttSpokenOpts")
            try:
                with open(join(abspath(dirname(__file__)), 'vocab/en-us/stt_language.voc'),
                          'w+') as stt_language:
                    for language, key in list(stt_dict.items()):
                        language = language.replace(",", "").replace("(", "").replace(")", "").lower().split(' ')[0]
                        stt_language.write(language + "\n")
                        self.stt_dict[language] = key
                        with open(join(abspath(dirname(__file__)), 'language_from_stt.txt'),
                                  'wb+') as language_from_stt:
                            pickle.dump(self.stt_dict, language_from_stt)
            except FileNotFoundError as e:
                LOG.error(e)
            return
        try:
            html = urllib.request.urlopen("https://docs.aws.amazon.com/polly/latest/dg/SupportedLanguage.html").read()
            bs = BeautifulSoup(html, "html.parser")
            area_table = bs.find(lambda tag: tag.name == 'table' and tag.has_attr('id') and
                                 tag['id'] == "w179aac13c13b7")
            LOG.debug(html)
            LOG.debug(area_table)
            self.language_list = (dict((web_utils.chunks([i.text.lower().replace("\n", "").replace(",", "") for i
                                                          in area_table.findAll('td') if i.text != "\xa0"], 2))))
            self.language_list = {**self.language_list, **self.extra_default}
        except Exception as e:
            LOG.error(e)
            self.language_list = self.extra_default
        try:
            with open(join(abspath(dirname(__file__)), 'language_from_polly.txt'),
                      'wb+') as language_from_polly_file:
                pickle.dump(self.language_list, language_from_polly_file)
                # TODO: Handle additions only? scraped list is incomplete..
                # with open(self.voc_path, 'w+') as entity:
                #     for i in list(self.language_list.keys()):
                #         entity.write(i + "\n")

        except FileNotFoundError as e:
            LOG.error(e)

    def switch_tts_voice(self, primary=None, secondary=None, message=None, overwrite_second=False):
        """
        Function for writing out tts configuration changes
        @param primary: nullable list of [language, gender]
        @param secondary: nullable list of [language, gender]
        @param message: message object associated with request
        @param overwrite_second: boolean to overwrite secondary language if not present
        @return:
        """
        LOG.info(f"primary={primary} | secondary={secondary}")
        # if not self.server:
        #     self.user_config.check_for_updates()
        nick = self.get_utterance_user(message)
        user_dict = self.build_user_dict(message)

        # Set Default Voice Values
        primary_voice, secondary_voice = "", ""
        if self.server:
            languages_matched = user_dict['tts_language'] == user_dict['secondary_tts_language']
            genders_matched = user_dict['tts_gender'] == user_dict['secondary_tts_gender']
            LOG.debug(f"checking: overwrite_second={overwrite_second} "
                      f"languages_matched={languages_matched} genders_matched={genders_matched}")

            # Update primary if present
            if primary:
                user_dict['tts_language'] = primary[0]
                user_dict['tts_gender'] = primary[1]
                # user_dict['neon_voice'] = primary_voice
            # Update secondary if present
            if secondary:
                user_dict['secondary_tts_language'] = secondary[0]
                user_dict['secondary_tts_gender'] = secondary[1]
                # user_dict['secondary_neon_voice'] = secondary_voice
            # Overwrite secondary if option specified or if secondary matched primary
            elif overwrite_second or (languages_matched and genders_matched):
                user_dict['secondary_tts_language'] = primary[0]
                user_dict['secondary_tts_gender'] = primary[1]
                # user_dict['secondary_neon_voice'] = ""

            # Update nick_profiles for the rest of this interaction
            message.context["nick_profiles"][nick]["speech"]["tts_language"] = user_dict['tts_language']
            message.context["nick_profiles"][nick]["speech"]["tts_gender"] = user_dict['tts_gender']
            # message.context["nick_profiles"][nick]["speech"]["neon_voice"] = user_dict['neon_voice']
            message.context["nick_profiles"][nick]["speech"]["secondary_tts_language"] =\
                user_dict['secondary_tts_language']
            message.context["nick_profiles"][nick]["speech"]["secondary_tts_gender"] = user_dict['secondary_tts_gender']

            # Emit updated profile to server
            LOG.debug(user_dict)
            self.socket_emit_to_server("update profile", ["skill", user_dict,
                                                          message.context["klat_data"]["request_id"]])
        else:
            if primary:
                self.user_config.update_yaml_file("speech", "tts_language", primary[0], True, False)
                self.user_config.update_yaml_file("speech", "tts_gender", primary[1], True, False)
                # if secondary or overwrite_second:
                self.user_config.update_yaml_file("speech", "neon_voice", primary_voice, True, False)
                # else:
                #     self.user_config.update_yaml_file("speech", "neon_voice", primary_voice, False, True)
            if secondary:
                self.user_config.update_yaml_file("speech", "secondary_tts_language", secondary[0], True, False)
                self.user_config.update_yaml_file("speech", "secondary_tts_gender", secondary[1], True, False)
                self.user_config.update_yaml_file("speech", "secondary_neon_voice", secondary_voice, False, True)
            elif overwrite_second:
                self.user_config.update_yaml_file("speech", "secondary_tts_language", "", True, False)
                self.user_config.update_yaml_file("speech", "secondary_tts_gender", "", True, False)
                self.user_config.update_yaml_file("speech", "secondary_neon_voice", "", False, True)
                # LOG.debug("Overwrite second")
            try:
                self.user_config.write_changes()
            except Exception as e:
                LOG.error(e)
                self.user_config.update_yaml_file(final=True)
            # self.bus.emit(Message('check.yml.updates',
            #                       {"modified": ["ngi_user_info"]}, {"origin": "translation.neon"}))

    def multiple_options(self):
        def populate_method(m=None):
            # self.check_for_signal("TK_active")
            self.bus.emit(Message("mycroft.stop"))
            self.choose_lang(selection_made=m)

        for i in list(self.options.keys()):
            self.speak(str(i).capitalize(), private=True)

        self.speak_dialog("AskPreferred", expect_response=True, private=True)
        self.enable_intent("I_prefer")  # TODO: Handle in converse DM

        # if not self.server:
        #     test = tkHelper.CreateTable()
        #     test.add_buttons(list(self.options.keys()))
        #
        #     param = test.start_table()
        #     LOG.info(param)
        #     self.check_for_signal("TK_active")
        #     self.check_for_signal("Button_Press")
        #     time.sleep(1)
        #     self.populate_method(param) if param else LOG.info("I prefer used")

    def stop(self):
        pass

    def _write_stt_change(self, setting, message, do_emit=True):
        """
        Writes new STT setting to user profile
        @param setting: (str) new language setting (i.e. "en-US")
        @param message: (Message) message associated with intent
        @param do_emit: (Boolean) server use, emit updated profile to server (False if more changes expected)
        @return: None
        """
        # import os
        LOG.info(setting)
        stt_language, stt_region = setting.split('-', 1)
        if self.server:
            nick = self.get_utterance_user(message)
            message.context["nick_profiles"][nick]["speech"]["stt_language"] = stt_language
            message.context["nick_profiles"][nick]["speech"]["stt_region"] = stt_region
            if do_emit:
                user_dict = self.build_user_dict(message)
                user_dict["stt_language"] = stt_language
                user_dict["stt_region"] = stt_region
                LOG.debug(user_dict)
                self.socket_emit_to_server("update profile", ["skill", user_dict,
                                                              message.context["klat_data"]["request_id"]])
                self.bus.wait_for_response(Message("css.emit",
                                                   {"event": "ai stt language change",
                                                    "data": (f"{stt_language}-{stt_region}", nick,
                                                             message.context["klat_data"]["request_id"])}),
                                           "ai_stt_language_change", timeout=2)
        else:
            self.user_config.update_yaml_file("speech", "stt_language", stt_language, True)
            self.user_config.update_yaml_file("speech", "stt_region", stt_region, final=True)
            # os.system("sudo -H -u " + self.configuration_available['devVars']['installUser'] + ' ' +
            #           self.configuration_available['dirVars']['coreDir'] + "/start_neon.sh voice")


def create_skill():
    return TranslationNGI()
