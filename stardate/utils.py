from django.core.exceptions import ImproperlyConfigured


def get_post_model():
    """
    Return the Post model that is active in this project
    """
    from django.conf import settings

    try:
        from django.apps import apps
        get_model = apps.get_model
    except ImportError:
        from django.db.models import get_model

    try:
        POST_MODEL = getattr(settings, 'STARDATE_POST_MODEL')
    except AttributeError:
        raise NotImplementedError('STARDATE_POST_MODEL is not defined.')

    try:
        app_label, model_name = POST_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured("STARDATE_POST_MODEL must be of the form 'app_label.model_name'")

    post_model = get_model(app_label, model_name)
    if post_model is None:
        raise ImproperlyConfigured("STARDATE_POST_MODEL refers to model '%s' that has not been installed" % POST_MODEL)
    return post_model
