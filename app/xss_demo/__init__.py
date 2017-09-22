from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
import os
from .models import (
    DB,
    Post,
    Comment,
    User,
    )


def _init_db():
    user1 = User('Administrator', 'top-secret')
    DB.save(user1)
    p1 = Post('First blogpost', 'My first blogpost. [...]', 'Administrator')
    p2 = Post('Second blogpost', 'Another blogpost. [...]', 'Administrator')
    p3 = Post('Third blogpost', 'Yet another blogpost. [...]', 'Administrator')
    DB.save(p1)
    DB.save(p2)
    DB.save(p3)
    c1 = Comment('Great post!', 'Paul E.', post_id=p1.id)
    c2 = Comment(
        'Well written but I disagree with your conclusion.',
        'Max M.',
        post_id=p1.id
        )
    c3 = Comment('Hmm', 'T.T.', post_id=p3.id)
    DB.save(c1)
    DB.save(c2)
    DB.save(c3)
    p1.comment_ids = [c1.id, c2.id]
    p3.comment_ids = [c3.id]
    DB.save(p1)
    DB.save(p3)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    secret = os.urandom(32)  # Cookies will become invalid after restart
    authn_policy = AuthTktAuthenticationPolicy(secret)
    # http_only=True
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('post', '/post/{id}')
    config.add_route('add_comment', '/post/{id}/add_comment')
    config.add_route('search', '/search')
    config.add_route('search_raw', '/search_raw')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('new_post', '/new_post')
    config.add_route('add_post', '/add_post')
    config.add_route('comment_authors', '/comment_authors')
    config.scan()
    _init_db()
    return config.make_wsgi_app()
