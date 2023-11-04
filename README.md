# SpotifyTestApp

This is a simple GUI application I created to learn the basics of tkinter.

The user first has to log in with their own client_id and client_secret (anyone can obtain these keys by creating an application on the Spotify developer website).

Following this, the application opens up a tab in the user's browser to direct them to a Spotify API generated authorisation URL, which provides a code the user also has to input into the GUI. This code allows for tokens to be generated in order to actually interact with the Spotify API.

Following this, the main application will launch. 
Here, a user can enter a playlist URL or playlist ID. In either case, this will give the list of genres contained within the playlist, and their counts. This algorithm is made significantly more efficient by using the get_multiple_artist API endpoint.