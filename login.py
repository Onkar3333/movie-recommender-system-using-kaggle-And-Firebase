import pickle
import streamlit as st
import pandas as pd
import requests
import firebase_admin
from firebase_admin import credentials, auth

# Check if Firebase app is already initialized
if not firebase_admin._apps:
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate("movie-recommender-system-42a96-firebase-adminsdk-rutfk-0c6dfdd8e8.json")
    firebase_admin.initialize_app(cred)

# Function to fetch movie poster
def fetch_poster(movie_id):
    try:
        url = "https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US".format(movie_id)
        data = requests.get(url)
        data = data.json()
        poster_path = data.get('poster_path')  # Use .get() to handle NoneType
        if poster_path:
            full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
            return full_path
        else:
            return None  # Return None if poster_path is None
    except requests.ConnectionError as e:
        st.error("Error fetching movie poster. Please check your internet connection or try again later.")
        return None

# Function to recommend movies
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        # Fetch the movie poster
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names, recommended_movie_posters

# Login logic
def login(email, password):
    try:
        # Verify email and password
        user = auth.get_user_by_email(email)
        # Attempt to sign in the user with provided credentials
        auth.sign_in_with_email_and_password(email, password)
        st.sidebar.success("Logged in successfully!")
        st.session_state['user'] = user.uid
        return True
    except auth.UserNotFoundError:
        st.sidebar.error("Invalid email or password")
        return False
    except auth.InvalidPasswordError:
        st.sidebar.error("Invalid email or password")
        return False

# Signup logic
def signup(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        st.sidebar.success("Account created successfully!")
        st.session_state['user'] = user.uid
        return True
    except auth.EmailAlreadyExistsError:
        st.sidebar.error("Email already exists")
        return False

# Set up Streamlit
st.set_page_config(layout="wide")  # Make the layout wider

# Load movie data and similarity scores
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Background image CSS
background_image = "https://8f430952.rocketcdn.me/wp-content/uploads/2019/05/apps.55787.9007199266246365.687a10a8-4c4a-4a47-8ec5-a95f70d8852d.jpg"
background_style = f"""
    <style>
        .stApp {{
            background-image: url("{background_image}");
            background-size: cover;
        }}
        .title {{
            text-align: center;
            font-size: 40px;
            color: red;
            font-weight: bold;
            text-shadow: 1px 1px 1.25px #808080;
        }}
    </style>
"""
st.markdown(background_style, unsafe_allow_html=True)

# Title
st.markdown(
    f"""
    <div class="title">Movie Recommendation System</div>
    """,
    unsafe_allow_html=True
)

# Sidebar for login/signup
st.sidebar.title('Welcome to The Movie Recommender System')

# Sidebar CSS
sidebar_style = """
    <style>
        .sidebar-content .title {
            width: 100%;
            text-align: center !important;
            
        }
    </style>
"""
st.markdown(sidebar_style, unsafe_allow_html=True)

# Radio button to choose between login and signup
action = st.sidebar.radio('Login/Signup', ['Login', 'Signup'])

if action == 'Login':
    login_form = st.sidebar.form(key='login_form')
    login_email = login_form.text_input('Email')
    login_password = login_form.text_input('Password', type='password')
    login_button = login_form.form_submit_button('Login')

    if login_button:
        try:
            user = auth.get_user_by_email(login_email)
            st.sidebar.success("Logged in successfully!")
            st.session_state['user'] = user.uid
        except auth.UserNotFoundError:
            st.sidebar.error("Invalid email or password")

elif action == 'Signup':
    signup_form = st.sidebar.form(key='signup_form')
    signup_email = signup_form.text_input('Email')
    signup_password = signup_form.text_input('Password', type='password')
    signup_button = signup_form.form_submit_button('Signup')

    if signup_button:
        try:
            user = auth.create_user(email=signup_email, password=signup_password)
            st.sidebar.success("Account created successfully!")
            st.session_state['user'] = user.uid
        except auth.EmailAlreadyExistsError:
            st.sidebar.error("Email already exists")

# Button to show recommendations (visible only if logged in)
if 'user' in st.session_state:
    selected_movie = st.selectbox("Type or select a movie from the dropdown", movies['title'].values)
    if st.button('Show Recommendation'):
        recommended_movie_names, recommended_movie_posters = recommend(selected_movie)
        columns = st.columns(5)
        for i in range(5):
            with columns[i]:
                if recommended_movie_posters[i] is not None:
                    st.text(recommended_movie_names[i])
                    google_search_url = f"https://www.google.com/search?q={'+'.join(recommended_movie_names[i].split())}"
                    st.markdown(f'''<a href="{google_search_url}" target='_blank' style='text-decoration: none; color: white; background-color: #008CBA; border: 2px solid #008CBA; padding: 5px 10px; border-radius: 5px; display: inline-block;'>Google Search</a>''', unsafe_allow_html=True)
                    st.image(recommended_movie_posters[i])
                else:
                    st.text(recommended_movie_names[i])  # Display only the title if no poster is available
else:
    st.warning("Please login/signup to use the app")
