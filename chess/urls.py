from django.conf.urls import url

from . import views

app_name = 'chess'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^change/$', views.change, name='change'),
    url(r'^new/$', views.new, name='new'),
    url(r'^move/(?P<frm>[0-9]+),(?P<to>[0-9]+)/$', views.move, name='move'),
    url(r'^recent/(?P<offset>[0-9]+)$', views.recent, name='recent'),
    url(r'^review/(?P<gid>[0-9a-z\-_]*)$', views.review, name='review'),
    #url(r'^(?P<question_id>[0-9]+)/$', views.detail, name='detail'),
    #url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]
