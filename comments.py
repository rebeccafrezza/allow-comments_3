import urllib
import os
import webapp2
import jinja2
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), 
extensions=['jinja2.ext.autoescape'], autoescape=True)
	
class Handler(webapp2.RequestHandler):
  def render(self, template, **kw):
    self.write(self.render_str(template,**kw))

  def render_str(self, template, **params):
    template = jinja_env.get_template(template)
    return template.render(params)

  def write(self, *a, **kw):
    self.response.write(*a, **kw)

DEFAULT = 'Comment'

def comment_key(comments_page=DEFAULT):
    return ndb.Key('Comments', comments_page)

class User(ndb.Model):
    identity = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)
  	
class Post(ndb.Model):
    user = ndb.StructuredProperty(User)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(Handler):
    def get(self, error=""):
        comments_page = self.request.get('comments_page',DEFAULT)

        if comments_page == DEFAULT.lower(): comments_page = DEFAULT

        posts_to_fetch = 5

        cursor_url = self.request.get('continue_posts')

        arguments = {'comments_page': comments_page}
		
        posts_query = Post.query(ancestor = comment_key(comments_page)).order(-Post.date)
	
        posts, cursor, more = posts_query.fetch_page(posts_to_fetch, start_cursor =
            Cursor(urlsafe=cursor_url))
			
        if more:
            arguments['continue_posts'] = cursor.urlsafe()
			
        arguments['posts'] = posts
		
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            user = 'Anonymous User'
            url = users.create_login_url(self.request.uri)
            url_linktext = 'login'
        
        error = self.request.get('error',"")
        arguments['user_name'] = user
        arguments['url'] = url
        arguments['url_linktext'] = url_linktext
        arguments['error'] = error
		
        self.render('comments.html', **arguments)

    def post(self):
        comments_page = self.request.get('comments_page',DEFAULT)
        post = Post(parent=comment_key(comments_page))
        if users.get_current_user():
            post.user = User(
                    identity=users.get_current_user().user_id(),
                    name=users.get_current_user().nickname(),
                    email=users.get_current_user().email())
        
        content = self.request.get('content')
		
        if content and content.strip():
            if type(content) != unicode:
                post.content = unicode(self.request.get('content'),'utf-8')			
            else:
                post.content = self.request.get('content')
                post.put()
                self.redirect('/#comment')
        else:
            error = "Please enter a valid comment."
            query_params = {'error': error}
            self.redirect('/?' + urllib.urlencode(query_params) + '#comment')    

app = webapp2.WSGIApplication([('/', MainPage), ('/comment', MainPage)], debug=True)
