# -*- coding: utf-8 -*-
# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2020 Neongecko.com Inc. | All Rights Reserved
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
# US Patents 2008-2020: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import pathlib
import pickle
import time
import urllib.request
from os.path import join, abspath, dirname

from adapt.intent import IntentBuilder
from bs4 import BeautifulSoup
# from gitdb.util import join

from NGI.utilities import beautifulSoupHelper as bU
from NGI.utilities import tkHelper
# from mycroft.device import device

# TODO: Depreciate on next core update DM
try:
    from NGI.utilities.parseUtils import clean_quotes
except Exception:
    from NGI.utilities.parseUtils import clean_utterance as clean_quotes
from mycroft.language import AmazonTranslator
from mycroft.messagebus.message import Message
from mycroft.skills.core import MycroftSkill, intent_handler
# from mycroft.util import check_for_signal, create_signal, get_cache_directory
from mycroft.util.log import LOG

from NGI.utilities.chat_user_util import get_chat_nickname_from_filename
#     from socketIO_client import SocketIO
#
#     css = SocketIO('https://localhost', 8888, verify=False)

# try:
#     from mycroft.device import device as d_hw
# except ImportError:
#     d_hw = 'desktop'


class TranslationNGI(MycroftSkill):
    default_options: dict
    options: dict
    gender_choice: str

    def __init__(self):
        super(TranslationNGI, self).__init__(name="TranslationNGI")
        self.region = 'us-west-2'
        self.check_for_signal("TR_secondary_language_options")
        self.voc_path = pathlib.Path(self.configuration_available["dirVars"]["skillsDir"]
                                     + "/translation.neon/vocab/en-us/language.voc")
        self.temp_dir = self.configuration_available['dirVars']['tempDir']
        self.default_gender = "female"
        self.extra_default = {"english": "en-us", "portuguese": "pt-pt", "spanish": "es-mx",
                              "chinese": "zh-zh", 'french': "fr-fr", "welsh": "cy-gb"}
        self.tts_language = self.user_info_available['speech']["tts_language"].lower()
        self.tts_gender = self.user_info_available['speech']["tts_gender"] \
            if self.user_info_available['speech']["tts_gender"] else self.default_gender
        self.two_gender = self.user_info_available['speech']["secondary_tts_gender"] \
            if self.user_info_available['speech']["secondary_tts_gender"] else self.default_gender
        # self.voice = self.user_info_available['speech']["neon_voice"]
        self.alreadySpoke = False

        if self.check_for_signal("TTS_update") or not self.voc_path.exists() or not \
                pathlib.Path(join(abspath(dirname(__file__)), 'language_from_polly.txt')).exists():
            self.get_entity()
            # LOG.info("\n \n getting voc or init \n \n ")
        else:
            with open(join(abspath(dirname(__file__)), 'language_from_polly.txt'),
                      'rb') as language_from_polly_file:
                self.language_list = pickle.load(language_from_polly_file)
                # LOG.info(self.ll)
                # LOG.info(type(self.ll))

        if self.check_for_signal("STT_update") or not pathlib.Path(join(abspath(dirname(__file__)),
                                                                   "vocab/en-us/stt_language.voc")).exists() \
                or not pathlib.Path(join(abspath(dirname(__file__)), 'language_from_stt.txt')).exists():
            self.stt_dict = {}
            self.get_entity(stt=True)
            LOG.info("\n \n getting voc or init \n \n ")
        else:
            with open(join(abspath(dirname(__file__)), 'language_from_stt.txt'),
                      'rb') as language_from_stt:
                self.stt_dict = pickle.load(language_from_stt)
        # self.add_event("cc_lang:change_request", self.handle_set_my_language)

    def initialize(self):
        self.disable_intent("I_prefer")
        self.disable_intent("LangMenu")

    @intent_handler(IntentBuilder("OnlyOne").require("OnlyOne"))
    def handle_no_secondary(self, message):
        # self.create_signal("NGI_YAML_user_update")
        if self.server:
            flac_filename = message.context["flac_filename"]
            # nick = get_chat_nickname_from_filename(flac_filename)
            user_dict = self.build_user_dict(message)
            user_dict['secondary_tts_language'] = user_dict['tts_language']
            user_dict['secondary_tts_gender'] = user_dict['tts_gender']
            user_dict['secondary_neon_voice'] = ""

            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai tts secondary language change",
            #                                     "data": (user_dict['secondary_tts_language'], nick, flac_filename)}),
            #                            "ai_tts_secondary_language_change", timeout=2)
            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai tts secondary gender change",
            #                                     "data": (user_dict['secondary_tts_gender'], nick, flac_filename)}),
            #                            "ai_tts_secondary_gender_change", timeout=2)
            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai secondary voice change",
            #                                     "data": (user_dict['secondary_neon_voice'], nick, flac_filename)}),
            #                            "ai_secondary_voice_change", timeout=2)

            # css.emit('ai tts secondary language change', user_dict['tts_language'], nick, flac_filename)
            LOG.info(user_dict)
            ret = self.bus.wait_for_response(Message("css.emit",
                                                     {"event": "update profile",
                                                      "data": ("skill", user_dict, flac_filename)}),
                                             "language_related_change", timeout=2)
            LOG.debug(f"server response: {ret}")
            # self.socket_io_emit(event="update profile", kind="skill",
            #                     flac_filename=flac_filename, message=user_dict)
        else:
            self.user_config.update_yaml_file("speech", "secondary_tts_language", "", True)
            self.user_config.update_yaml_file("speech", "secondary_neon_voice", "", True)
            self.user_config.update_yaml_file("speech", "secondary_tts_gender", "", final=True)
            self.create_signal("TTS_voice_switch")
        self.speak_dialog("OnlyOneLanguage", private=True)

    @intent_handler(IntentBuilder("SettingsLanguage").require("Settings"))
    def handle_settings(self, message):
        # flac_filename = message.data.get("flac_filename")
        preference_speech = self.preference_speech(message)
        # self.speak("Your language settings are:", private=True)
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
        # self.speak("Your primary output language is {} {}".format(tts_gender, key_tt.title()), private=True) if \
        #     key_tt and tts_gender else self.speak("You don't have primary settings", private=True)
        # self.speak("And your secondary language is {} {}".format(secondary_tts_gender,
        #                                                          secondary_key_tt.title()), private=True) if \
        #     secondary_tts_gender and secondary_key_tt else LOG.info("One language only")

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
        self.write_stt_change(language, message)

        # if self.server:
        #     chat_filename = message.data.get('flac_filename')
        #     nick = get_chat_nickname_from_filename(chat_filename)
        #     user_dict = self.build_user_dict(message)
        #     # chat_user = ChatUser(nick)
        #     # self.tts_gender = chat_user.tts_gender
        #     self.tts_gender = user_dict["tts_gender"]
        #
        #     request = str(message.data.get("utterance"))
        #     self.gender_choice = message.data.get("gender")
        #     proposed = str(message.data.get("stt_language"))
        #     LOG.info(self.language_list)
        #     self.options = {x: y for (x, y) in list(self.language_list.items()) if proposed in x or proposed == x}
        #     LOG.info(request)
        #     LOG.info(proposed)
        #     LOG.info(self.options)
        #
        #     if len(self.options) > 1:
        #         self.default_options = {x: y for (x, y)
        #                                 in list(self.extra_default.items()) if x == proposed or proposed in x}
        #         LOG.info(self.default_options)
        #         if self.default_options:
        #             LOG.info(self.default_options[proposed].split("-")[0])
        #             css.emit('ai stt language change', self.default_options[proposed].split("-")[0], nick,
        #                      chat_filename)
        #             language_voice = \
        #                 self.configuration_available["ttsVoice"][self.default_options[proposed].split("-")[0]][
        #                     self.tts_gender]
        #             LOG.debug('language specific voice = ' + language_voice)
        #             self.voice = chat_user.ai_speech_voice
        #             if self.voice != language_voice:
        #                 self.voice = language_voice
        #                 css.emit('ai voice change', self.voice, nick,
        #                          chat_filename)
        #             self.speak("I am starting to listen for " + proposed.capitalize(), private=True)
        #         else:
        #             self.speak("I have a few options for you: ", private=True)
        #             self.multiple_options()
        #     else:
        #         # self.switch_tts_voice(self.options[proposed], self.gender_choice, chatFilename=chatFilename)
        #         LOG.info(self.options[proposed].split("-")[0])
        #         css.emit('ai stt language change', self.options[proposed].split("-")[0], nick, chat_filename)
        #         language_voice = \
        #             self.configuration_available["ttsVoice"][self.options[proposed].split("-")[0]][
        #                 self.tts_gender]
        #         LOG.debug('language specific voice = ' + language_voice)
        #         self.voice = chat_user.ai_speech_voice
        #         if self.voice != language_voice:
        #             self.voice = language_voice
        #             css.emit('ai voice change', self.voice, nick,
        #                      chat_filename)
        #         self.speak("Listening for " + proposed.capitalize(), private=True)
        # else:

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
        # silent = "silent" in message.data.get("utterance")
        primary = self._check_if_valid_language(message.data.get('first_language'))
        secondary = self._check_if_valid_language(message.data.get('second_language'))
        if not primary and not secondary:
            # if not silent:
            self.speak_dialog('NotValidLanguage', {"language": "either of your requested languages"}, private=True)
            return

        LOG.info(primary)
        LOG.info(secondary)
        gender = [x for x in message.data.get("utterance").split(" ") if x in ["male", "female"]]
        LOG.info(gender)
        primary, secondary = self._parse_two_languages([next(iter(primary)), next(iter(secondary))],
                                                       gender, message)
        LOG.info(f"{primary} | {secondary}")
        # LOG.info(secondary)
        if not primary:
            # if not silent:
            self.speak_dialog('NotValidLanguage', {"language": "your requested primary language"}, private=True)
            self._finish_language_change(message, second=secondary)  # , called=True, singular=True, silent=False)
            return
        if not secondary:
            # if not silent:
            self.speak_dialog('NotValidLanguage', {"language": "your requested secondary language"}, private=True)
            self._finish_language_change(message, first=primary)  # , called=True, singular=True, silent=False)
            return
        LOG.info(primary)
        LOG.info(secondary)
        self._finish_language_change(message, first=primary, second=secondary)  # , called=True, silent=False)

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
            # LOG.info("*****" + str(secondary))
            if secondary[0] == "not_valid":
                if not silent:
                    self.speak_dialog('NotValidLanguage', {"language": requested_language}, private=True)
            else:
                self._finish_language_change(message, second=secondary)  # , called=True, singular=True, silent=silent)
        else:
            if not silent:
                self.speak_dialog('NotValidLanguage', {"language": "your requested secondary language"}, private=True)

    # @intent_handler(IntentBuilder("SetMyAlsoLanguage").optionally("Neon").require("also_language")
    #                 .optionally("gender").build())
    # def handle_also_secondary(self, message):
    #     LOG.debug(message.data)
    #     message.data["second_language"] = message.data["also_language"]
    #     self.handle_set_my_secondary(message)

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
        # if from_two:
        #     primary = from_two[0]
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
                self._finish_language_change(message, first=primary)  # , called=True, singular=True, silent=silent)
        else:
            if not silent:
                self.speak_dialog('NotValidLanguage', {"language": message.data.get('first_language')}, private=True)

    @intent_handler(IntentBuilder("TalkToMeKeyword").optionally("Neon").
                    require("TalkToMeKeyword").optionally("Two").optionally("gender").require("language")
                    .optionally("gender").optionally("Two").optionally("language").optionally("gender"))
    def handle_talk_to_me(self, message):
        LOG.debug(f"DM: {message.data}")
        # word_to_say, secondary = None, None
        # self.alreadySpoke = False
        # LOG.info(f"second={second}")
        # LOG.info(f"silent={silent}")
        # chat_filename = message.data.get('flac_filename', None)
        # secondary = None

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
            # if message.data.get("Two"):
            # self.check_for_signal("isSpeaking")
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
            # while self.check_for_signal("isSpeaking", -1):
            #     time.sleep(.25)
        LOG.info(f"{primary} | {secondary}")
        if not primary and not secondary:
            LOG.warning(f"No language found in {message.data}")
            return
        self._finish_language_change(message, primary, secondary)

        # if self.server:
        #     try:
        #         nick = get_chat_nickname_from_filename(chat_filename)
        #         # chat_user = ChatUser(nick)
        #         # self.stt_language = chatUser.stt_language
        #         # self.tts_language = chat_user.tts_language
        #         # LOG.debug('tts language = ' + self.tts_language)
        #         # self.voice = chat_user.ai_speech_voice
        #         # LOG.debug('1 voice = ' + self.voice)
        #         # self.tts_gender = chat_user.tts_gender
        #         # LOG.debug('tts gender = ' + self.tts_gender)
        #         # # LOG.debug('config = ' + str(self.configuration_available))
        #         # if self.tts_language.startswith("zh-"):
        #         #     lookup_lang = "cmn"
        #         # else:
        #         #     lookup_lang = self.tts_language.split("-")[0]
        #         LOG.debug(f"first: {first}")
        #
        #         # language_voice = self.configuration_available["ttsVoice"][lookup_lang][
        #         #     self.tts_gender]
        #         # LOG.debug('language specific voice = ' + language_voice)
        #         # if self.voice != language_voice:
        #         #     self.voice = language_voice
        #         # # LOG.debug('stt language = '+self.stt_language)
        #         # LOG.debug('2 voice = ' + self.voice)
        #     except Exception as e:
        #         LOG.error(e)
        #         self.tts_language = "en-us"
        #         self.voice = "Joanna"

    def _finish_language_change(self, message, first=None, second=None):  # , called=None, singular=None, silent=None):
        """
        Finish changing languages after utterance has been parsed and languages are determined
        @param message (Message): message object associated with intent match
        @param first (list): first language data
        @param second (list): second language data
        @return: None
        """
        # if "silent" in message.data.get("utterance"):
        #     silent = True
        # phrase_to_say = None

        # Determine if second language should be cleared
        if "only" in str(message.data.get("utterance")).split():
            overwrite_second = True
        else:
            overwrite_second = False

        self.create_signal("TTS_voice_switch")
        # request = str(message.data.get("utterance")).replace("to ", '') if "to" in str(message.data.get("utterance"))
        #     else str(message.data.get("utterance"))
        utt = str(message.data.get("utterance"))

        # index_to_strip = str(message.data.get("utterance")).rfind("to ")
        # request = str(message.data.get("utterance"))[:index_to_strip] + \
        #     str(message.data.get("utterance"))[index_to_strip + 1:]
        # LOG.debug(f"DM: {request}")

        # Get gender option from utterance
        # self.gender_choice = message.data.get("gender") if not first and not second else first[1] \
        #     if first else second[1]
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
        # proposed = None

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
                        # self.speak_dialog("SwitchLanguageDialectOptions", {"language": proposed.capitalize()},
                        #                   True, private=True)
                        # self.enable_intent("LangMenu")
                        # self.request_check_timeout(30, "LangMenu")
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

        # for opt in (first, second):
        #     if opt:
        #         LOG.debug(f"DM: {opt}")
        #         if opt == first:
        #             LOG.debug(f"Change primary: {first}")
        #             proposed = primary_language
        #             gender = primary_gender
        #         elif opt == second:
        #             LOG.debug(f"Change second: {second}")
        #             proposed = second_language
        #             gender = second_gender
        #         else:
        #             LOG.error("Invalid opt")
        #             break
        #         LOG.info(f"proposed in self.language_list={proposed in self.language_list}")
        #         LOG.info(f"proposed in self.extra_default={proposed in self.extra_default}")
        #         self.options = {x: y for (x, y) in list(self.language_list.items()) if proposed in x and x not in
        #                         self.extra_default}
        #         # LOG.info(f"DM: {self.options}")
        #         LOG.info(f"genders={primary_gender}, {second_gender}")
        #
        #         self.default_options = {x: y for (x, y)
        #                                 in list(self.extra_default.items()) if x == proposed or proposed in x}
        #         LOG.debug(f"DM: default_options={self.default_options}")
                # Handle phrase translation request
        # TODO: This is where translate is handled... Move to separate intent DM
        if "translate" in utt:
            # Trim off language for "translate [phrase] to [lang]"
            if " to " in utt:
                request = " to ".join(utt.split(" to ")[:-1])
            else:
                request = utt
            LOG.debug(request)
            proposed = primary_language

            options = {x: y for (x, y) in list(self.language_list.items()) if proposed in x and x not in
                       self.extra_default}
            LOG.info(f"DM: {options}")
            default_options = {x: y for (x, y)
                               in list(self.extra_default.items()) if x == proposed or proposed in x}

            LOG.debug(f"DM: {proposed}")
            LOG.debug(request)
            phrase_to_say = request.replace(proposed, '').replace(message.data.get("TalkToMeKeyword"), '')
            phrase_to_say = phrase_to_say.replace(message.data.get("Neon"), "") if message.data.get("Neon") else \
                phrase_to_say
            LOG.debug(f"DM: {phrase_to_say}")
            phrase_to_say = phrase_to_say.strip()
            LOG.info(phrase_to_say)
            lang = options.get(proposed)
            if not lang:
                lang = default_options.get(proposed)
            gender = primary_gender
            LOG.info(list(self.language_list.keys())[list(self.language_list.values()).index(lang)].title())
            self.speak_dialog('WordInLanguage',
                              {'word': phrase_to_say.strip(),
                               'language': list(self.language_list.keys())[
                                   list(self.language_list.values()).index(lang)].title().capitalize()})
            # self.speak("{} in {} is".format(word.strip(), list(self.ll.keys())[list(self.ll.values()).
            #                                 index(lang)].title()))
            if gender or self.tts_gender == "female":
                tts_gender = gender if gender else self.default_gender
            else:
                tts_gender = self.default_gender
            if self.server and lang == "zh-zh":
                voice = self.configuration_available["ttsVoice"]["cmn"][tts_gender]
            elif self.server:
                voice = self.configuration_available["ttsVoice"][lang.split("-")[0]][tts_gender]
            else:
                voice = self.configuration_available["ttsVoice"][lang][tts_gender]
            LOG.info(voice)
            translated = clean_quotes(self.translator.translate(phrase_to_say, lang, "en"))
            LOG.info(translated)
            if self.gui_enabled:
                self.gui.show_text(translated, phrase_to_say)
                self.clear_gui_timeout()
            self.speak(translated, speaker={"name": "Neon",
                                            "language": lang,
                                            "gender": tts_gender,
                                            "voice": voice,
                                            "override_user": True,
                                            "translated": True},
                       meta={"untranslated": phrase_to_say,
                             "is_translated": True})
            # self.speak("Sure. The phrase '" + word_to_say + "' translates to:")
            # self.switch_tts_voice(self.options[proposed], self.gender_choice, phrase_to_say, secondary=second,
            #                       message=message)
        else:
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
                self.request_check_timeout(30, "LangMenu")

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
                    # speaker={"name": "Neon",
                    #          "language": primary_language,
                    #          "gender": primary_gender,
                    #          "voice": None}, private=True)
                elif second:
                    self.speak_dialog("SwitchLanguage", {"language": second_language,
                                                         "gender": second_gender,
                                                         "primary": "secondary"}, private=True)
                    # speaker={"name": "Neon",
                    #          "language": second_language,
                    #          "gender": second_gender,
                    #          "voice": None}, private=True)

        # Handle multiple dialect options
        # elif len(self.options) > 1:
        #     # if phrase_to_say:
        #     #     # LOG.debug(word_to_say)
        #     #     # self.speak("Sure. The phrase '" + word_to_say + "' translates to:")
        #
        #     #     self.switch_tts_voice(self.default_options[proposed], self.gender_choice, phrase_to_say,
        #     #                           secondary=second, message=message)
        #     # else:
        #     if self.default_options:
        #         # LOG.info("DM: *****" + str(second))
        #         self.switch_tts_voice(self.default_options[proposed], gender,
        #                               message=message, overwrite_second=overwrite_second)
        #         if (not first or (called and singular)) and not self.server:
        #             if primary_language == second_language:
        #                 self.create_signal("TR_secondary_language_options")
        #             if not silent:
        #                 self.speak_dialog("SwitchLanguageDialectOptions", {"language": proposed.capitalize()},
        #                                   True, private=True)
        #                 # self.speak("I am switching to " + proposed.capitalize() +
        #                 #            ". But I do have other dialect options for you. "
        #                 #            "Say language menu if you would "
        #                 #            "like to hear them", True, private=True)
        #                 self.enable_intent("LangMenu")
        #                 self.request_check_timeout(30, "LangMenu")
        #         else:
        #             if not self.alreadySpoke:
        #                 if not silent:
        #                     # LOG.debug(f"DM: {proposed}")
        #                     # self.speak("Switching to " + proposed.capitalize(), private=True)
        #                     self.speak_dialog("SwitchLanguage", {"language": proposed.capitalize()},
        #                                       private=True)
        #     else:
        #         LOG.info(">>>>>>DM: Got to multiple_options? <<<<<<")
        #         if not silent:
        #             self.speak_dialog("LanguageMenu", private=True)
        #             self.multiple_options()
        # Single match for requested language
        # else:
        #     try:
        #         # if phrase_to_say:
        #         #     # self.speak("Sure. The phrase '" + word_to_say + "' translates to:")
        #         #     self.switch_tts_voice(self.options[proposed], self.gender_choice, phrase_to_say,
        #         #                           secondary=second, message=message)
        #         # else:
        #         # LOG.info(f"DM: switch_tts_voice({self.options[proposed]}, {self.gender_choice}, "
        #         #          f"{second}...)")
        #         if proposed in self.default_options:
        #             lang = self.default_options[proposed]
        #         elif proposed in self.language_list:
        #             lang = self.language_list[proposed]
        #         elif proposed in self.extra_default:
        #             lang = self.extra_default[proposed]
        #         else:
        #             LOG.error(f"{proposed} not found in languages!")
        #             break
        #         self.switch_tts_voice(lang, gender, secondary=second,
        #                               message=message, overwrite_second=overwrite_second)
        #         if not silent:
        #             # self.speak("Switching to " + proposed.capitalize(), private=True)
        #             self.speak_dialog("SwitchLanguage", {"language": proposed.capitalize()}, private=True)
        #
        #     except KeyError as e:
        #         # if proposed in self.default_options:
        #         #     if phrase_to_say:
        #         #         # self.speak("Sure. The phrase '" + word_to_say + "' translates to:")
        #         #         self.switch_tts_voice(self.default_options[proposed], self.gender_choice, phrase_to_say,
        #         #                               secondary=second, message=message)
        #         #     else:
        #         #         self.switch_tts_voice(self.default_options[proposed], self.gender_choice, secondary=second,
        #         #                               message=message, overwrite_second=overwrite_second)
        #         #         if not silent:
        #         #             # self.speak("Switching to " + proposed.capitalize(), private=True)
        #         #             self.speak_dialog("SwitchLanguage", {"language": proposed.capitalize()}, private=True)
        #         #
        #         # else:
        #         LOG.error(e)
        # else:
        #     LOG.debug(f"DM: opt={opt}, first={first}, second={second}")
            # self.handle_talk_to_me(message, second=second) if first and not second and not called \
            #     else LOG.info("One Language")

    @intent_handler(IntentBuilder("SetPreferredLanguage").optionally("Neon").require("PreferredLanguage")
                    .require("language").build())
    def handle_set_preferred(self, message):
        """
        Intent to set a "preferred" language to be used for stt and tts
        @param message: message object associated with intent match
        @return:
        """
        self.create_signal("TTS_voice_switch")
        new_lang = self._check_if_valid_language(message.data.get('language'))
        LOG.info(new_lang)
        language = list(new_lang.values())[0]
        # gender = [x for x in message.data.get("utterance").split(" ") if x in ["male", "female"]]
        # LOG.info(gender)
        gender = self.preference_speech(message).get("tts_gender", self.default_gender)
        self.write_stt_change(language, message, do_emit=False)
        self.switch_tts_voice([language, gender], message=message, overwrite_second=True)
        # if self.server:
        #     flac_filename = message.data.get("flac_filename")
        #     LOG.debug(flac_filename)
        #     nick = get_chat_nickname_from_filename(flac_filename)
        #     LOG.debug(nick)
        #     css.emit('ai stt language change', language.split("-")[0], nick, flac_filename)
        # else:
        self.speak_dialog("ChangePreferredLanguage", {"language": list(new_lang.keys())[0].capitalize()}, private=True)

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
        # self.create_signal("isSpeaking")
        # self.create_signal("TR_twoLangs")
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
            # self.speak_dialog("SwitchPrimaryAndSecondary", {"primary_gender": str(primary_pair[1]),
            #                                                 "primary_language": str(primary_pair[0]),
            #                                                 "second_gender": str(secondary_pair[1]),
            #                                                 "second_language": str(secondary_pair[0])},
            #                   private=True)
            # self.speak("I am switching the primary language to " + str(primary_pair[1]) + " "
            #            + str(primary_pair[0]) + " and secondary language to " + str(secondary_pair[1])
            #            + " " + str(secondary_pair[0]), private=True)
            # self.alreadySpoke = True
            return primary_pair, secondary_pair
        else:
            LOG.error(f"Invalid language setting: primary={primary_pair} secondary={secondary_pair}")
            if (primary_pair[0]) == "not_valid":
                return "", secondary_pair
            return primary_pair, ""

    @intent_handler(IntentBuilder("LangMenu").optionally("Neon").require("ShowLanguageMenu"))
    def lang_menu(self):
        self.disable_intent("LangMenu")
        self.speak_dialog("LanguageMenu", private=True)
        self.create_signal("TK_active")
        # self.request_check_timeout(25, "LangMenu", "TK_active")
        self.multiple_options()

    @intent_handler(IntentBuilder("I_prefer").optionally("Neon").
                    require("I_prefer").optionally("gender").optionally("language")
                    .optionally("gender"))
    def choose_lang(self, message=None, selection_made=None):
        self.create_signal("TTS_voice_switch")
        # flac_filename = message.data.get('flac_filename')
        preference_speech = self.preference_speech(message)
        # config = self.user_info_available
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
        if stt:
            LOG.info("Getting Switch STT update")
            stt_dict = self.configuration_available["sttSpokenOpts"]
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
            self.language_list = (dict((bU.chunks([i.text.lower().replace("\n", "").replace(",", "") for i
                                                   in area_table.findAll('td') if i.text != "\xa0"], 2))))
            self.language_list = {**self.language_list, **self.extra_default}
        except Exception as e:
            LOG.error(e)
            self.language_list = self.extra_default
        try:
            with open(join(abspath(dirname(__file__)), 'language_from_polly.txt'),
                      'wb+') as language_from_polly_file:
                pickle.dump(self.language_list, language_from_polly_file)
                with open(self.voc_path, 'w+') as entity:
                    for i in list(self.language_list.keys()):
                        entity.write(i + "\n")

        except FileNotFoundError as e:
            LOG.error(e)

    def switch_tts_voice(self, primary=None, secondary=None, message=None,
                         overwrite_second=False):
        """
        Function for writing out tts configuration changes
        @param primary: nullable list of [language, gender]
        @param secondary: nullable list of [language, gender]
        @param message: message object associated with request
        @param overwrite_second: boolean to overwrite secondary language if not present
        @return:
        """
        # LOG.info(f"lang: {lang} gender: {gender} word: {word}")
        # LOG.info(gender)
        # LOG.info(word)
        LOG.info(f"primary={primary} | secondary={secondary}")
        # LOG.debug(message)
        self.user_config.check_for_updates()
        # user_dict = None
        nick = None
        flac_filename = None
        if self.server and message:
            flac_filename = message.data.get("flac_filename", "")
            nick = get_chat_nickname_from_filename(flac_filename)
        user_dict = self.build_user_dict(message)

        # Set Default Voice Values
        primary_voice, secondary_voice = "", ""
        if primary:
            primary_voice = self.configuration_available["ttsVoice"][primary[0]][primary[1]]
        if secondary:
            secondary_voice = self.configuration_available["ttsVoice"][secondary[0]][secondary[1]]
        LOG.debug(f"voices: {primary_voice} {secondary_voice}")
        if self.server:
            languages_matched = user_dict['tts_language'] == user_dict['secondary_tts_language']
            genders_matched = user_dict['tts_gender'] == user_dict['secondary_tts_gender']
            LOG.debug(f"checking: overwrite_second={overwrite_second} "
                      f"languages_matched={languages_matched} genders_matched={genders_matched}")

            # Update primary if present
            if primary:
                user_dict['tts_language'] = primary[0]
                user_dict['tts_gender'] = primary[1]
                user_dict['neon_voice'] = primary_voice
            # Update secondary if present
            if secondary:
                # LOG.debug("Called with secondary")
                user_dict['secondary_tts_language'] = secondary[0]
                user_dict['secondary_tts_gender'] = secondary[1]
                user_dict['secondary_neon_voice'] = secondary_voice
            # Overwrite secondary if option specified or if secondary matched primary
            elif overwrite_second or (languages_matched and genders_matched):
                # LOG.debug("overwriting second")
                user_dict['secondary_tts_language'] = primary[0]
                user_dict['secondary_tts_gender'] = primary[1]
                user_dict['secondary_neon_voice'] = ""
                # LOG.debug(f"overwrite_second: {user_dict['secondary_tts_language']} "
                #           f"{user_dict['secondary_tts_gender']}")

            # Update nick_profiles for the rest of this interaction
            message.context["nick_profiles"][nick]["tts_language"] = user_dict['tts_language']
            message.context["nick_profiles"][nick]["tts_gender"] = user_dict['tts_gender']
            message.context["nick_profiles"][nick]["neon_voice"] = user_dict['neon_voice']
            message.context["nick_profiles"][nick]["secondary_tts_language"] = user_dict['secondary_tts_language']
            message.context["nick_profiles"][nick]["secondary_tts_gender"] = user_dict['secondary_tts_gender']
            message.context["nick_profiles"][nick]["secondary_neon_voice"] = user_dict['secondary_neon_voice']

            # Emit updated profile to server
            LOG.debug(user_dict)
            ret = self.bus.wait_for_response(Message("css.emit",
                                                     {"event": "update profile",
                                                      "data": ("skill", user_dict, flac_filename)}),
                                             "language_related_change", timeout=2)
            LOG.debug(f"server response: {ret}")

            # self.socket_io_emit(event="update profile", kind="skill", flac_filename=flac_filename, message=user_dict)
            #
            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai voice change",
            #                                     "data": (user_dict['neon_voice'], nick,  flac_filename)}),
            #                            "ai_voice_change", timeout=2)
            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai secondary voice change",
            #                                     "data": (user_dict['secondary_neon_voice'], nick,  flac_filename)}),
            #                            "secondary_voice_change", timeout=2)
            #
            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai tts gender change",
            #                                     "data": (user_dict['tts_gender'], nick, flac_filename)}),
            #                            "ai_tts_gender_change", timeout=2)
            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai tts secondary gender change",
            #                                     "data": (user_dict['secondary_tts_gender'], nick, flac_filename)}),
            #                            "ai_tts_secondary_gender_change", timeout=2)
            #
            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai tts language change",
            #                                     "data": (user_dict['tts_language'], nick, flac_filename)}),
            #                            "ai_tts_language_change", timeout=2)
            # self.bus.wait_for_response(Message("css.emit",
            #                                    {"event": "ai tts secondary language change",
            #                                     "data": (user_dict['secondary_tts_language'], nick, flac_filename)}),
            #                            "ai_tts_secondary_language_change", timeout=2)

        else:
            if primary:
                self.user_config.update_yaml_file("speech", "tts_language", primary[0], True, False)
                self.user_config.update_yaml_file("speech", "tts_gender", primary[1], True, False)
                if secondary or overwrite_second:
                    self.user_config.update_yaml_file("speech", "neon_voice", primary_voice, True, False)
                else:
                    self.user_config.update_yaml_file("speech", "neon_voice", primary_voice, False, True)
            if secondary:
                self.user_config.update_yaml_file("speech", "secondary_tts_language", secondary[0], True, False)
                self.user_config.update_yaml_file("speech", "secondary_tts_gender", secondary[1], True, False)
                self.user_config.update_yaml_file("speech", "secondary_neon_voice", secondary_voice, False, True)
            elif overwrite_second:
                self.user_config.update_yaml_file("speech", "secondary_tts_language", "", True, False)
                self.user_config.update_yaml_file("speech", "secondary_tts_gender", "", True, False)
                self.user_config.update_yaml_file("speech", "secondary_neon_voice", "", False, True)
                LOG.debug("DM: Overwrite second")
            self.bus.emit(Message('check.yml.updates',
                                  {"modified": ["ngi_user_info"]}, {"origin": "translations\.neon"}))

        # Depreciated old method
        # Check that a language was passed
        # if lang:
        #
        #     # This is not a one-off translation, update user profile
        #     # if not word:
        #     self.create_signal("TTS_voice_switch")
        #     # self.create_signal("NGI_YAML_user_update")
        #     LOG.info(lang)
        #     self.check_for_signal("TK_active")
        #     self.tts_language = lang
        #
        #     # Check if gender was passed and use config if not
        #     if not gender:
        #         if not secondary:
        #             gender = user_dict.get("tts_gender", self.default_gender)
        #         else:
        #             gender = user_dict.get("secondary_tts_gender", self.default_gender)
        #         # if self.server and chat_filename:
        #         #     # if not mobile:
        #         #     # noinspection PyUnboundLocalVariable
        #         #     # css.emit('ai tts gender change', self.tts_gender, nick, chat_filename)
        #         #     if gender:
        #         #         # user_dict = self.build_user_dict(chat_filename)
        #         #         user_dict['tts_gender'] = gender
        #         #     else:
        #         #         gender = user_dict['tts_gender']
        #         #         # self.socket_io_emit(event="update profile", kind="skill",
        #         #         #                     flac_filename=chat_filename, message=user_dict)
        #         #     user_dict["tts_voice"] = self.configuration_available["ttsVoice"][lang][gender]
        #         #
        #         # else:
        #         #     if not secondary:
        #         #         self.user_config._update_yaml_file("speech", "tts_gender", self.tts_gender, True)
        #         #         # self.user_config.update_yaml_file("user", "speech", "secondary_tts_gender", "", True)
        #         #     else:
        #         #         self.user_config._update_yaml_file("speech", "secondary_tts_gender",
        #         #                                            self.tts_gender, True)
        #
        #     # Get voice name from config
        #     voice = self.configuration_available["ttsVoice"][lang][gender]
        #     LOG.info(voice)
        #
        #     # Write out profile changes
        #     if self.server and chat_filename:
        #         # if not mobile:
        #         # nick = get_chat_nickname_from_filename(chat_filename)
        #         # user_dict = self.build_user_dict(chat_filename)
        #         if not secondary:
        #             # Conditionally reset secondary language
        #             LOG.info(f"no secondary. {user_dict['tts_language']}, {user_dict['secondary_tts_language']}")
        #             if (str(user_dict['tts_language']).split('-')[0] ==
        #                     str(user_dict['secondary_tts_language']).split('-')[0]) or overwrite_second:
        #                 # css.emit('ai tts secondary language change', lang, nick, chat_filename)
        #                 user_dict['secondary_tts_language'] = lang
        #                 message.data["nick_profiles"][nick]["secondary_tts_language"] = lang
        #                 user_dict['secondary_neon_voice'] = ""
        #                 message.data["nick_profiles"][nick]["secondary_neon_voice"] = ""
        #
        #             # Update primary language
        #             # css.emit('ai tts language change', lang, nick, chat_filename)
        #             user_dict['tts_language'] = lang
        #             message.data["nick_profiles"][nick]["tts_language"] = lang
        #             user_dict['tts_gender'] = gender
        #             message.data["nick_profiles"][nick]["tts_gender"] = gender
        #             user_dict['neon_voice'] = voice
        #             message.data["nick_profiles"][nick]["neon_voice"] = voice
        #
        #             # if mobile:
        #             #     self.socket_io_emit("languages", f"&primary={lang}&secondary=", chat_filename)
        #         else:
        #             LOG.info("DM: Secondary language ONLY")
        #             # css.emit('ai tts secondary language change', lang, nick, chat_filename)
        #             user_dict['secondary_tts_language'] = lang
        #             message.data["nick_profiles"][nick]["secondary_tts_language"] = lang
        #             user_dict['secondary_tts_gender'] = gender
        #             message.data["nick_profiles"][nick]["secondary_tts_gender"] = gender
        #             user_dict['secondary_neon_voice'] = voice
        #             message.data["nick_profiles"][nick]["secondary_neon_voice"] = voice
        #
        #         LOG.debug(">>>Server Language Changes Complete<<<")
        #         LOG.debug(user_dict)
        #         self.socket_io_emit(event="update profile", kind="skill",
        #                             flac_filename=chat_filename, message=user_dict)
        #
        #             # if mobile:
        #             #     self.socket_io_emit("languages", f"&primary=&secondary={lang}", chat_filename)
        #         # css.emit('ai tts language change', self.tts_language, nick,
        #         #          chat_filename) if not secondary else css.emit('ai tts secondary language change',
        #         #                                                        self.tts_language, nick, chat_filename)
        #
        #         # if secondary:
        #         #     user_dict['secondary_tts_language'] = secondary
        #         # self.socket_io_emit(event="update profile", kind="skill",
        #         #                     flac_filename=chat_filename, message=user_dict)
        #
        #     # Update local config
        #     else:
        #         if not secondary:
        #             LOG.debug("DM: Changing language")
        #             self.create_signal('TR_voiceSwitch')
        #             self.user_config._update_yaml_file("speech", "tts_language", self.tts_language, True, False)
        #             if overwrite_second:
        #                 self.user_config._update_yaml_file("speech", "secondary_tts_language", '', True, False)
        #                 self.user_config._update_yaml_file("speech", "neon_voice", voice, True, False)
        #                 LOG.debug("DM: Overwrite second")
        #                 self.user_config._update_yaml_file("speech", "secondary_neon_voice", "", False, True)
        #                 LOG.debug("DM: Changing language complete")
        #             else:
        #                 LOG.debug("DM: No secondary change")
        #                 self.user_config._update_yaml_file("speech", "neon_voice", voice, False, True)
        #                 LOG.debug("DM: Change language complete")
        #             self.create_signal('TR_switchComplete')
        #         else:
        #             self.user_config._update_yaml_file("speech", "secondary_tts_language", self.tts_language,
        #                                                True, False)
        #             self.user_config._update_yaml_file("speech", "secondary_neon_voice", voice, False, True)
        #             LOG.debug("DM: Change language complete")
        #             self.create_signal('TR_switch2Complete')
        #
        #         # if self.server:
        #         #     if self.tts_language.split("-")[0] == "zh":
        #         #         lang = "cmn"
        #         #     else:
        #         #         lang = self.tts_language.split("-")[0]
        #         #     try:
        #         #         self.voice = self.configuration_available["ttsVoice"][lang][gender]
        #         #     except Exception as e:
        #         #         LOG.error(e)
        #         #         self.voice = "Joanna"
        #         #         self.tts_language = "en-us"
        #         # else:
        #         #     self.voice = self.configuration_available["ttsVoice"][self.tts_language][self.tts_gender]
        #         # LOG.info(self.voice)
        #
        #         # if self.server and chat_filename:
        #         #     # if not mobile:
        #         #     # user_dict = self.build_user_dict(chat_filename)
        #         #     if secondary:
        #         #         user_dict['secondary_neon_voice'] = voice
        #         #     else:
        #         #         # css.emit('ai voice change', self.voice, nick, chat_filename)
        #         #         user_dict['neon_voice'] = voice
        #         #     # if lang:
        #         #     #     user_dict['tts_language'] = lang
        #         #     # if secondary:
        #         #     #     user_dict['secondary_tts_language'] = secondary
        #         #     self.socket_io_emit(event="update profile", kind="skill",
        #         #                         flac_filename=chat_filename, message=user_dict)
        #         #     # if mobile:
        #         #     #     self.socket_io_emit("languages", f"&primary={lang}&secondary={secondary}", chat_filename)
        #         # else:
        #         #     LOG.debug("DM: Changing language")
        #         #     self.create_signal('TR_voiceSwitch')
        #         #     if not secondary:
        #         #         if overwrite_second:
        #         #             self.user_config._update_yaml_file("speech", "neon_voice", voice, True, False)
        #         #             LOG.debug("DM: Overwrite second")
        #         #             self.user_config._update_yaml_file("speech", "secondary_neon_voice", "", False, True)
        #         #             LOG.debug("DM: Changing language complete")
        #         #         else:
        #         #             LOG.debug("DM: No secondary change")
        #         #             self.user_config._update_yaml_file("speech", "neon_voice", voice, False, True)
        #         #             LOG.debug("DM: Change language complete")
        #         #         self.create_signal('TR_switchComplete')
        #         #     else:
        #         #         self.user_config._update_yaml_file("speech", "secondary_neon_voice", voice, False, True)
        #         #         LOG.debug("DM: Change language complete")
        #         #         self.create_signal('TR_switch2Complete')
        #             # self.bus.emit(Message('check.yml.updates'))
        #
        #     # Single phrase to translate
        #     # else:
        #     #     LOG.info(word.strip())
        #     #     LOG.info(list(self.language_list.keys())[list(self.language_list.values()).index(lang)].title())
        #     #     self.speak_dialog('WordInLanguage',
        #     #                       {'word': word.strip(),
        #     #                        'language': list(self.language_list.keys())[
        #     #                            list(self.language_list.values()).index(lang)].title().capitalize()})
        #     #     # self.speak("{} in {} is".format(word.strip(), list(self.ll.keys())[list(self.ll.values()).
        #     #     #                                 index(lang)].title()))
        #     #     if gender or self.tts_gender == "female":
        #     #         tts_gender = gender if gender else self.default_gender
        #     #     else:
        #     #         tts_gender = self.default_gender
        #     #     if self.server and lang == "zh-zh":
        #     #         voice = self.configuration_available["ttsVoice"]["cmn"][tts_gender]
        #     #     elif self.server:
        #     #         voice = self.configuration_available["ttsVoice"][lang.split("-")[0]][tts_gender]
        #     #     else:
        #     #         voice = self.configuration_available["ttsVoice"][lang][tts_gender]
        #     #     LOG.info(voice)
        #     #
        #     #     self.speak(word, speaker={"name": "Neon",
        #     #                               "language": lang,
        #     #                               "gender": tts_gender,
        #     #                               "voice": voice})
        #         # import boto3
        #         # import subprocess
        #         # amazon_conf = self.user_info_available['tts']['amazon']
        #         # region = amazon_conf.get('region')
        #         # access_key = amazon_conf.get("aws_access_key_id")
        #         # secret_key = amazon_conf.get("aws_secret_access_key")
        #         # result = boto3.client(service_name='translate', region_name=region, aws_access_key_id=access_key,
        #         #                       aws_secret_access_key=secret_key, use_ssl=True).translate_text(
        #         #     Text=word, SourceLanguageCode='en', TargetLanguageCode=lang.split("-")[0])
        #         # translated_sentence = str(result.get('TranslatedText'))
        #         # tts = boto3.client(service_name='polly', region_name=self.region, aws_access_key_id=access_key,
        #         #                    aws_secret_access_key=secret_key).synthesize_speech(OutputFormat='mp3',
        #         #                                                                        Text=translated_sentence,
        #         #                                                                        VoiceId=voice)
        #         # if not self.server:
        #         #     time.sleep(.25)
        #         #     while self.check_for_signal("isSpeaking", -1):
        #         #         time.sleep(.25)
        #         #     path = self.temp_dir + "/temp_tr.wav"
        #         #     speak_file = open(path, 'wb')
        #         #     sound_bytes = tts['AudioStream'].read()
        #         #     speak_file.write(sound_bytes)
        #         #     speak_file.close()
        #         #     subprocess.Popen(["mpv", "--volume=100", "--audio-client-name=neon-voice", path])
        #         #     # os.system("mpv --volume=100 " + path)
        #         # else:
        #         #     import os
        #         #
        #         #     path = None
        #         #     # if mobile:
        #         #     #     time.sleep(2)  # Make sure speak is processed before sending translation
        #         #     #     self.socket_io_emit("translation", f"&lang={lang}&text={translated_sentence}",
        #         chat_filename)
        #         #     #     # self.speak(f"{lang}: {translated_sentence}")
        #         #     if chat_filename:
        #         #         time.sleep(1)
        #         #         if chat_filename.endswith('.flac'):
        #         #             # LOG.debug('>>> 2.2 chatFilename input to tts execute = ' + chatFilename)
        #         #             # path = os.path.join(self.configuration_available['dirVars']['cacheDir'],
        #         #             #                     ("tts/" + '00all'),
        #         #             #                     os.path.basename(chat_filename)[0:-5] + '.' + 'wav')
        #         #             path = os.path.join(self.configuration_available['dirVars']['cacheDir'], f
        #         "tts/00_{lang}",
        #         #                                 os.path.basename(chat_filename)[0:-5] + '.' + 'wav')
        #         #             # LOG.debug('>>> 0.2 Mimic wav file = ' + wav_file)
        #         #         elif chat_filename.endswith('.txt'):
        #         #             path = os.path.join(self.configuration_available['dirVars']['cacheDir'],
        #         f"tts/00_{lang}",
        #         #                                 os.path.basename(chat_filename)[0:-4] + '.' + 'wav')
        #         #         # else:
        #         #         #     if chat_filename.endswith('.txt'):
        #         #         #         # LOG.debug('>>> chatFilename input to tts execute = ' + chatFilename)
        #         #         #         path = os.path.join(self.configuration_available['dirVars']['cacheDir'],
        #         #         #                             ("tts/" + '00all'),
        #         #         #                             os.path.basename(chat_filename)[0:-4] + '.' + 'wav')
        #         #         #         # LOG.debug('>>> 0.3 Mimic wav file = ' + wav_file)
        #         #
        #         #         x = 1
        #         #
        #         #         os.makedirs(os.path.dirname(path), exist_ok=True)
        #         #         # noinspection PyUnboundLocalVariable
        #         #         while os.path.isfile(path):
        #         #             parts = os.path.basename(path).split('-')
        #         #             parts[0] = 'sid' + str(x)
        #         #             new_file_name = '-'.join(parts)
        #         #             # path = os.path.join(self.configuration_available['dirVars']['cacheDir'],
        #         #             #                     ("tts/" + '00all'),
        #         #             #                     new_file_name)
        #         #             path = os.path.join(self.configuration_available['dirVars']['cacheDir'],
        #         f"tts/00_{lang}",
        #         #                                 new_file_name)
        #         #             x = x + 1
        #         #         speak_file = open(path, 'wb')
        #         #         sound_bytes = tts['AudioStream'].read()
        #         #         speak_file.write(sound_bytes)
        #         #         speak_file.close()
        #         #         self.bus.emit(Message("recognizer_loop:chatUser_response",
        #         #                               {"sentences": [translated_sentence], "wav_files": [path]}))
        #
        #     self.disable_intent("LangMenu")
        #     self.disable_intent("I_prefer")
        #     # LOG.debug('tts switch completed ' + str(lang))
        #
        # # Language Not Passed
        # else:
        #     LOG.error(f"No language passed with message: {message}")
        #     self.speak_dialog("LanguageError", private=True)

    def multiple_options(self):
        for i in list(self.options.keys()):
            self.speak(str(i).capitalize(), private=True)

        self.speak_dialog("AskPreferred", expect_response=True, private=True)
        self.enable_intent("I_prefer")

        if not self.server:
            test = tkHelper.CreateTable()
            test.add_buttons(list(self.options.keys()))

            param = test.start_table()
            LOG.info(param)
            self.check_for_signal("TK_active")
            self.check_for_signal("Button_Press")
            time.sleep(1)
            self.populate_method(param) if param else LOG.info("I prefer used")

    def populate_method(self, m=None):
        self.check_for_signal("TK_active")
        self.check_for_signal("CORE_isSpeaking")  # TODO: Depreciate this? DM
        LOG.info("Got here!" + str(m))
        self.bus.emit(Message("mycroft.stop"))
        self.choose_lang(selection_made=m)

    def stop(self):
        pass

    def write_stt_change(self, setting, message, do_emit=True):
        """
        Writes new STT setting to user profile
        @param setting: (str) new language setting (i.e. "en-US")
        @param message: (Message) message associated with intent
        @param do_emit: (Boolean) server use, emit updated profile to server (False if more changes expected)
        @return: None
        """
        import os
        LOG.info(setting)
        stt_language, stt_region = setting.split('-', 1)
        # self.create_signal("NGI_YAML_user_update")
        if self.server:
            flac_filename = message.context["flac_filename"]
            nick = get_chat_nickname_from_filename(flac_filename)
            message.context["nick_profiles"][nick]["stt_language"] = stt_language
            message.context["nick_profiles"][nick]["stt_region"] = stt_region
            if do_emit:
                user_dict = self.build_user_dict(message)
                user_dict["stt_language"] = stt_language
                user_dict["stt_region"] = stt_region
                LOG.debug(user_dict)
                self.socket_io_emit(event="update profile", kind="skill",
                                    flac_filename=flac_filename, message=user_dict)
                self.bus.wait_for_response(Message("css.emit",
                                                   {"event": "ai stt language change",
                                                    "data": (f"{stt_language}-{stt_region}", nick, flac_filename)}),
                                           "ai_stt_language_change", timeout=2)
        else:
            self.user_config.update_yaml_file("speech", "stt_language", stt_language, True)
            self.user_config.update_yaml_file("speech", "stt_region", stt_region, final=True)
            os.system("sudo -H -u " + self.configuration_available['devVars']['installUser'] + ' ' +
                      self.configuration_available['dirVars']['coreDir'] + "/start_neon.sh voice")


def create_skill():
    return TranslationNGI()
