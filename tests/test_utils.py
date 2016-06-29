from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from mock import Mock, patch

from stardate.utils import get_post_model


class UninstalledModel(models.Model):
    pass


class UtilsTestCase(TestCase):
    @override_settings()
    def test_missing_setting_raises_exception(self):
        del settings.STARDATE_POST_MODEL
        self.assertRaises(NotImplementedError, get_post_model)

    @override_settings(STARDATE_POST_MODEL='kablooey')
    def test_incorrect_model_raises_exception(self):
        self.assertRaises(ImproperlyConfigured, get_post_model)

    @patch('stardate.utils.get_model')
    def test_not_installed_model_raises_exception(self, mock_get_model):
        mock_get_model.return_value = None

        self.assertRaises(ImproperlyConfigured, get_post_model)
