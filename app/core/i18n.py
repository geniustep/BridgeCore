"""
Internationalization (i18n) Support

Multi-language support for API messages and responses
"""
from typing import Dict, Optional
from enum import Enum


class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    ARABIC = "ar"
    FRENCH = "fr"


class I18n:
    """
    Internationalization service

    Features:
    - Multi-language support (English, Arabic, French)
    - Error message translation
    - Field label translation
    - Dynamic language switching
    """

    def __init__(self, default_language: Language = Language.ENGLISH):
        self.default_language = default_language
        self.translations = self._load_translations()

    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """
        Load translation dictionaries

        Returns:
            Translation mappings
        """
        return {
            "en": {
                # Common messages
                "success": "Success",
                "error": "Error",
                "not_found": "Not found",
                "invalid_request": "Invalid request",
                "unauthorized": "Unauthorized",
                "forbidden": "Forbidden",
                "internal_error": "Internal server error",

                # CRUD operations
                "record_created": "Record created successfully",
                "record_updated": "Record updated successfully",
                "record_deleted": "Record deleted successfully",
                "records_found": "Records found",
                "no_records_found": "No records found",

                # Authentication
                "login_success": "Login successful",
                "login_failed": "Login failed",
                "logout_success": "Logout successful",
                "token_expired": "Token expired",
                "token_invalid": "Invalid token",
                "session_expired": "Session expired",

                # System
                "system_connected": "Connected to system",
                "system_disconnected": "Disconnected from system",
                "connection_failed": "Connection failed",

                # Fields
                "name": "Name",
                "email": "Email",
                "phone": "Phone",
                "mobile": "Mobile",
                "address": "Address",
                "city": "City",
                "country": "Country",
                "date": "Date",
                "price": "Price",
                "quantity": "Quantity",
                "total": "Total",
                "status": "Status",

                # Validation
                "required_field": "This field is required",
                "invalid_email": "Invalid email address",
                "invalid_phone": "Invalid phone number",
                "invalid_format": "Invalid format",
            },
            "ar": {
                # Common messages
                "success": "نجح",
                "error": "خطأ",
                "not_found": "غير موجود",
                "invalid_request": "طلب غير صالح",
                "unauthorized": "غير مصرح",
                "forbidden": "محظور",
                "internal_error": "خطأ داخلي في الخادم",

                # CRUD operations
                "record_created": "تم إنشاء السجل بنجاح",
                "record_updated": "تم تحديث السجل بنجاح",
                "record_deleted": "تم حذف السجل بنجاح",
                "records_found": "تم العثور على سجلات",
                "no_records_found": "لم يتم العثور على سجلات",

                # Authentication
                "login_success": "تم تسجيل الدخول بنجاح",
                "login_failed": "فشل تسجيل الدخول",
                "logout_success": "تم تسجيل الخروج بنجاح",
                "token_expired": "انتهت صلاحية الرمز",
                "token_invalid": "رمز غير صالح",
                "session_expired": "انتهت صلاحية الجلسة",

                # System
                "system_connected": "تم الاتصال بالنظام",
                "system_disconnected": "تم قطع الاتصال بالنظام",
                "connection_failed": "فشل الاتصال",

                # Fields
                "name": "الاسم",
                "email": "البريد الإلكتروني",
                "phone": "الهاتف",
                "mobile": "الجوال",
                "address": "العنوان",
                "city": "المدينة",
                "country": "الدولة",
                "date": "التاريخ",
                "price": "السعر",
                "quantity": "الكمية",
                "total": "المجموع",
                "status": "الحالة",

                # Validation
                "required_field": "هذا الحقل مطلوب",
                "invalid_email": "عنوان بريد إلكتروني غير صالح",
                "invalid_phone": "رقم هاتف غير صالح",
                "invalid_format": "صيغة غير صالحة",
            },
            "fr": {
                # Common messages
                "success": "Succès",
                "error": "Erreur",
                "not_found": "Non trouvé",
                "invalid_request": "Requête invalide",
                "unauthorized": "Non autorisé",
                "forbidden": "Interdit",
                "internal_error": "Erreur interne du serveur",

                # CRUD operations
                "record_created": "Enregistrement créé avec succès",
                "record_updated": "Enregistrement mis à jour avec succès",
                "record_deleted": "Enregistrement supprimé avec succès",
                "records_found": "Enregistrements trouvés",
                "no_records_found": "Aucun enregistrement trouvé",

                # Authentication
                "login_success": "Connexion réussie",
                "login_failed": "Échec de la connexion",
                "logout_success": "Déconnexion réussie",
                "token_expired": "Jeton expiré",
                "token_invalid": "Jeton invalide",
                "session_expired": "Session expirée",

                # System
                "system_connected": "Connecté au système",
                "system_disconnected": "Déconnecté du système",
                "connection_failed": "Échec de la connexion",

                # Fields
                "name": "Nom",
                "email": "Email",
                "phone": "Téléphone",
                "mobile": "Mobile",
                "address": "Adresse",
                "city": "Ville",
                "country": "Pays",
                "date": "Date",
                "price": "Prix",
                "quantity": "Quantité",
                "total": "Total",
                "status": "Statut",

                # Validation
                "required_field": "Ce champ est requis",
                "invalid_email": "Adresse email invalide",
                "invalid_phone": "Numéro de téléphone invalide",
                "invalid_format": "Format invalide",
            }
        }

    def translate(
        self,
        key: str,
        language: Optional[Language] = None,
        **kwargs
    ) -> str:
        """
        Translate a message key

        Args:
            key: Translation key
            language: Target language (defaults to default_language)
            **kwargs: Format parameters

        Returns:
            Translated message

        Example:
            i18n.translate("record_created", language=Language.ARABIC)
            # Returns: "تم إنشاء السجل بنجاح"
        """
        lang = language or self.default_language
        lang_dict = self.translations.get(lang.value, self.translations["en"])

        message = lang_dict.get(key, key)

        # Format message with parameters
        if kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError:
                pass

        return message

    def get_error_message(
        self,
        error_type: str,
        language: Optional[Language] = None,
        details: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get formatted error message

        Args:
            error_type: Error type key
            language: Target language
            details: Additional error details

        Returns:
            Error message dictionary

        Example:
            i18n.get_error_message("not_found", Language.ARABIC)
            # Returns: {"error": "خطأ", "message": "غير موجود"}
        """
        lang = language or self.default_language

        return {
            "error": self.translate("error", lang),
            "message": self.translate(error_type, lang),
            "details": details
        }

    def get_success_message(
        self,
        message_key: str,
        language: Optional[Language] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Get formatted success message

        Args:
            message_key: Message key
            language: Target language
            data: Additional data

        Returns:
            Success message dictionary
        """
        lang = language or self.default_language

        result = {
            "success": True,
            "message": self.translate(message_key, lang)
        }

        if data:
            result["data"] = data

        return result

    def add_translation(
        self,
        language: Language,
        key: str,
        value: str
    ):
        """
        Add custom translation

        Args:
            language: Target language
            key: Translation key
            value: Translation value

        Example:
            i18n.add_translation(Language.ARABIC, "custom_message", "رسالة مخصصة")
        """
        if language.value not in self.translations:
            self.translations[language.value] = {}

        self.translations[language.value][key] = value

    def get_supported_languages(self) -> list:
        """
        Get list of supported languages

        Returns:
            List of language codes
        """
        return [lang.value for lang in Language]


# Global i18n instance
i18n = I18n()
