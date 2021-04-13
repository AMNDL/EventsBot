# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
from .settings import root, env


public_root = root.path('public/')
# Media config
MEDIA_ROOT = public_root('media')
MEDIA_URL = env.str('MEDIA_URL', default='/media/')
# Static config
STATIC_ROOT = public_root('static')
STATIC_URL = env.str('STATIC_URL', default='/static/')
