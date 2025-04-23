from website import create_app

app = create_app()

#makes sure we are in them main file on only run the app then
if __name__ == '__main__':
    app.run(debug=True) # run flask app, starts web server
