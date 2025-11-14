"""
Internationalization tests
"""
import pytest
from app.core.i18n import I18n, Language


def test_i18n_initialization():
    """Test i18n initialization"""
    i18n = I18n()

    assert i18n.default_language == Language.ENGLISH
    assert "en" in i18n.translations
    assert "ar" in i18n.translations
    assert "fr" in i18n.translations


def test_translate_english():
    """Test English translation"""
    i18n = I18n()

    message = i18n.translate("record_created", language=Language.ENGLISH)

    assert message == "Record created successfully"


def test_translate_arabic():
    """Test Arabic translation"""
    i18n = I18n()

    message = i18n.translate("record_created", language=Language.ARABIC)

    assert message == "تم إنشاء السجل بنجاح"


def test_translate_french():
    """Test French translation"""
    i18n = I18n()

    message = i18n.translate("record_created", language=Language.FRENCH)

    assert message == "Enregistrement créé avec succès"


def test_get_error_message():
    """Test error message generation"""
    i18n = I18n()

    error_msg = i18n.get_error_message("not_found", Language.ARABIC)

    assert error_msg["error"] == "خطأ"
    assert error_msg["message"] == "غير موجود"


def test_get_success_message():
    """Test success message generation"""
    i18n = I18n()

    success_msg = i18n.get_success_message(
        "record_created",
        Language.ENGLISH,
        data={"id": 123}
    )

    assert success_msg["success"] is True
    assert success_msg["message"] == "Record created successfully"
    assert success_msg["data"]["id"] == 123


def test_add_custom_translation():
    """Test adding custom translation"""
    i18n = I18n()

    i18n.add_translation(Language.ENGLISH, "custom_key", "Custom Message")

    message = i18n.translate("custom_key", Language.ENGLISH)

    assert message == "Custom Message"


def test_get_supported_languages():
    """Test getting supported languages"""
    i18n = I18n()

    languages = i18n.get_supported_languages()

    assert "en" in languages
    assert "ar" in languages
    assert "fr" in languages
    assert len(languages) == 3
