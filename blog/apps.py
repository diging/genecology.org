from __future__ import unicode_literals

from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = 'blog'

    def ready(self):
        import blog.signals
        super(BlogConfig, self).ready()
