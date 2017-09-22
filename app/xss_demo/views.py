from pyramid.view import (
    view_defaults,
    view_config,
    forbidden_view_config,
    )
from pyramid.request import Response
from pyramid.renderers import render_to_response
import pyramid.httpexceptions as exc
from pyramid.security import (
    remember,
    forget,
    )
import html
import json

from .models import (
    DB,
    Post,
    Comment,
    User,
    )

def _add_csp_header_hard(request):
    request.response.headers['Content-Security-Policy'] = (
    "default-src 'none';"
    "script-src 'self';"
    "connect-src 'self';"
    "img-src 'self';"
    "style-src 'self';"
    )


def _add_csp_header(request):
    request.response.headers['Content-Security-Policy'] = (
    "default-src 'none';"
    "script-src 'self' oss.maxcdn.com 'unsafe-inline';"
    "connect-src 'self';"
    "img-src 'self' placehold.it placeholdit.imgix.net;"
    "style-src 'self' oss.maxcdn.com 'unsafe-inline';"
    "font-src 'self' oss.maxcdn.com;"
    )

@view_defaults(renderer='home.pt')
class MainView:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(route_name='home', renderer='templates/home.pt')
    def home(self):
        posts = DB.get_all(Post)
        return {'posts': sorted(posts, key=lambda post: post.date, reverse=True)}
    
    
    @view_config(route_name='post', renderer='templates/post.pt')
    def post(self):
        post_id = int(self.request.matchdict['id'])
        post = DB.get(Post, post_id)
        comments = []
        for cid in post.comment_ids:
            comments.append(DB.get(Comment, cid))
        
        return {
            'post': post,
            'comments': sorted(comments, key=lambda comment: comment.date,
                   reverse=True)
         }
    
    
    @view_config(route_name='add_comment')
    def add_comment(self):
        post_id = int(self.request.matchdict['id'])
        post = DB.get(Post, post_id)
        author = self.request.params['author']
        message = self.request.params['message']
        comment = Comment(message, author, post_id)
        DB.save(comment)
        post.comment_ids.append(comment.id)
        DB.save(post)
        raise exc.HTTPFound(self.request.route_url('post', id=post_id))
    
    
    @view_config(route_name='new_post', renderer='templates/new_post.pt')
    def new_post(self):
        if self.request.authenticated_userid != 'Administrator':
            raise exc.HTTPForbidden()
        return {}
    
    
    @view_config(route_name='add_post')
    def add_post():
        if self.request.authenticated_userid != 'Administrator':
            raise exc.HTTPForbidden()
        author = self.request.authenticated_userid
        title = self.request.params['title']
        content = self.request.params['content']
        post = Post(title, content, author)
        DB.save(post)
        raise exc.HTTPFound(self.request.route_url('post', id=post.id))
    
    
    @view_config(route_name='login', renderer='templates/login.pt')
    @forbidden_view_config(renderer='templates/login.pt')
    def login(self):
        login_url = self.request.route_url('login')
        referrer = self.request.url
        if referrer == login_url:
            referrer = '/' # never use the login form itself as came_from
        came_from = self.request.params.get('came_from', referrer)
        message = ''
        username = ''
        password = ''
        if 'form.submitted' in self.request.params:
            username = self.request.params['username']
            password = self.request.params['password']
            for user in DB.get_all(User):
                if user.username.lower() == username.lower() and \
                    user.password_correct(password):
                    headers = remember(self.request, user.username)
                    raise exc.HTTPFound(location = came_from, headers = headers)
            message = 'Failed login'
    
        return dict(
            message = message,
            came_from = came_from,
            username = username,
        )
    
    @view_config(route_name='logout')
    def logout(self):
        if self.request.authenticated_userid == 'Administrator':
            raise exc.HTTPFound(location = '/', headers = forget(self.request))
    
        raise exc.HTTPFound(location = '/login')
    
    
    @view_config(route_name='search', renderer='templates/search.pt')
    def search(self):
        return {'query': self.request.params.get('q', '')}
        # http://localhost:6543/search?q=%3Cscript%3Ealert(123)%3C/script%3E
        # chromium-browser --temp-profile --disable-xss-auditor
    
    
    @view_config(route_name='search_raw')
    def search_raw(self):
        """
        Search results without template (raw Response() object).
        Templates help escaping characters.
        """
        query = self.request.params.get('q', '')
        #query = html.escape(query)
        content = """
    <html>
        <body>
        <p>Your query is: {0}</p>
        </body>
    </html>""".format(query)
        return Response(content)

    @view_config(route_name='comment_authors')
    def comment_authors(self):
        authors = ""
        for comment in DB.get_all(Comment):
            comment = comment.serialize()
            if comment['author'] not in authors:
                authors += "<li>"+comment['author']+"</li>"

        return Response(authors, content_type = 'text/plain')
