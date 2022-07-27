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

import shutil
import unittest
import pytest

from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from mycroft_bus_client import Message
from ovos_utils.messagebus import FakeBus


class TestSkill(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        from mycroft.skills.skill_loader import SkillLoader

        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance
        cls.test_fs = join(dirname(__file__), "skill_fs")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs

        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_fs)

    def tearDown(self) -> None:
        self.skill.speak.reset_mock()
        self.skill.speak_dialog.reset_mock()

    def test_00_skill_init(self):
        # Test any parameters expected to be set in init or initialize methods
        from neon_utils.skills import NeonSkill

        self.assertIsInstance(self.skill, NeonSkill)

    def test_handle_translate_phrase(self):
        valid_phrase = "hello"
        invalid_phrase = ""
        valid_language = "spanish"
        invalid_language = ""
        unsupported_language = "laotian"

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
        self.skill.speak.assert_called_once_with(
            "Hola", speaker={"language": "es", "name": "Neon",
                             "gender": "female", "override_user": True}
        )

        # Unsupported language
        self.skill.handle_translate_phrase(Message(
            "test", {"phrase": valid_phrase, "language": unsupported_language,
                     "lang": "en-us"}))
        self.skill.speak_dialog.assert_called_with("language_not_supported",
                                                   {"lang": "Laothian"})
        # TODO: Test gender determination


if __name__ == '__main__':
    pytest.main()
