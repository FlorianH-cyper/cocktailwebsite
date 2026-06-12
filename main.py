import os

from website import create_app

app = create_app()

#makes sure we are in them main file on only run the app then
if __name__ == '__main__':
    # set FLASK_DEBUG=1 locally for auto-reload; never set it in production
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
