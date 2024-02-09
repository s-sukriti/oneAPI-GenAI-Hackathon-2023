import streamlit as st
import streamlit_authenticator as stauth
from dependencies import sign_up, fetch_users
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder
)
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_chat import message
from utils import *
from googletrans import Translator
import pyttsx3
import speech_recognition as sr
import json

def translate_response(response, target_language='en'):
    translator = Translator()
    translated_response = translator.translate(response, dest=target_language)
    return translated_response.text

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Say something...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=10)

    try:
        st.info("Recognizing...")
        query = recognizer.recognize_google(audio)
        st.text("You said: " + query)
        return query
    except sr.UnknownValueError:
        st.warning("Sorry, could not understand audio.")
        return None
    except sr.RequestError as e:
        st.error("Speech recognition request failed; {0}".format(e))
        return None

st.header('Welcome to :violet[Khaanvaani]')

try:
    users = fetch_users()
    emails = []
    usernames = []
    passwords = []

    for user in users:
        emails.append(user['key'])
        usernames.append(user['username'])
        passwords.append(user['password'])

    credentials = {'usernames': {}}
    for index in range(len(emails)):
        credentials['usernames'][usernames[index]] = {'name': emails[index], 'password': passwords[index]}

    Authenticator = stauth.Authenticate(credentials, cookie_name='Streamlit', key='abcdef', cookie_expiry_days=4)
    email, authentication_status, username = Authenticator.login(':green[Login]', 'main')
    info, info1 = st.columns(2)

    if not authentication_status:
        sign_up()

    if username:
        if username in usernames:
            if authentication_status:
                st.sidebar.subheader(f'Welcome {username}')

                class AHome:
                    @staticmethod
                    def app():
                        try:
                            if 'responses' not in st.session_state:
                                st.session_state['responses'] = ["Hello!, How can I assist you?"]

                            if 'requests' not in st.session_state:
                                st.session_state['requests'] = []

                            with open('config.json') as config_file:
                                config = json.load(config_file)
                                api_key = config.get('openai_api_key', None)

                            if api_key is None:
                                st.error("API key is missing. Please provide a valid API key in the config.json file.")
                                st.stop()
                            else:
                                llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=api_key)

                                if 'buffer_memory' not in st.session_state:
                                    st.session_state.buffer_memory = ConversationBufferWindowMemory(k=5, return_messages=True)

                                # Initialize 'context' with a default value
                                context = ""

                        except ValueError:
                            st.error("Incorrect API key provided. Please check and update the API key in the config.json file.")
                            st.stop()
                        except Exception as e:
                            st.error("An error occurred during initialization: " + str(e))
                            llm = None
                            st.session_state.buffer_memory = None

                        system_msg_template = SystemMessagePromptTemplate.from_template(
                            template="""Answer the question as truthfully as possible using the provided context, 
                            and if the answer is not contained within the text below, say 'This is beyond my ability can you be more specific?'"""
                        )

                        human_msg_template = HumanMessagePromptTemplate.from_template(template="{input}")

                        prompt_template = ChatPromptTemplate.from_messages([system_msg_template, MessagesPlaceholder(variable_name="history"), human_msg_template])

                        conversation = ConversationChain(memory=st.session_state.buffer_memory, prompt=prompt_template, llm=llm, verbose=True)

                        response_container = st.container()
                        textcontainer = st.container()

                        with textcontainer:
                            query = st.text_input("Query: ", key="input")
                            if query:
                                with st.spinner("typing..."):
                                    try:
                                        conversation_string = get_conversation_string()
                                        refined_query = query_refiner(conversation_string, query)
                                        st.subheader("Refined Query:")
                                        st.write(refined_query)
                                        context = find_match(query)

                                        if "coal" in context.lower() or "mine" in context.lower() or "hi" in context.lower() or "hello" in context.lower() or "hey" in context.lower():
                                            response = conversation.predict(input=f"Context:\n {context} \n\n Query:\n{query}")
                                            st.session_state.requests.append(query)

                                            # Translate response based on selected language
                                            selected_language = st.session_state.get('selected_language', 'en')
                                            translated_response = translate_response(response, target_language=selected_language)
                                            st.session_state.responses.append(translated_response)

                                            # Speak the translated response
                                            speak(translated_response)

                                        else:
                                            st.warning("This query is not related to coal mining. Please ask a question about coal mines.")

                                    except Exception as e:
                                        st.error("An error occurred during conversation: " + str(e))

                        with response_container:
                            if st.session_state['responses']:
                                for i in range(len(st.session_state['responses'])):
                                    try:
                                        message(st.session_state['responses'][i], key=str(i))
                                        if i < len(st.session_state['requests']):
                                            message(st.session_state["requests"][i], is_user=True, key=str(i) + '_user')
                                            # Speak the response from the bot
                                            speak(st.session_state['responses'][i])
                                    except Exception as e:
                                        st.error("An error occurred while displaying messages: " + str(e))

                        # Language selection dropdown below the response box
                        selected_language = st.selectbox('Select Language', ['English', 'Hindi', 'Kannada', 'Telugu', 'Malayalam', 'Tamil'])

                        # Set selected language in session state
                        st.session_state.selected_language = selected_language

                        # Microphone button for speech recognition
                        if st.button('🎤 Speak'):
                            query = recognize_speech()
                            if query:
                                st.text("Recognized Query: " + query)
                                st.session_state.requests.append(query)
                                response = conversation.predict(input=f"Context:\n {context} \n\n Query:\n{query}")
                                st.session_state.responses.append(response)
                                st.text("Response: " + response)
                                speak(response)

                class AboutUs:
                    @staticmethod
                    def app():
                        html_content = """
                            <h1>About Khaanvaani - A Chatbot</h1>

                            <p>Khaanvaani is an intelligent virtual assistant developed to cater to the needs of individuals in the mining sector. It provides quick and efficient responses to queries related to Acts, Rules, and Regulations pertinent to the mining industry. Our aim is to streamline the process of retrieving essential information, making it user-friendly and accessible at any time.</p>

                            <h2>Project Overview</h2>

                            <h3>Purpose</h3>
                            <p>The primary objective of Khaanvaani is to offer comprehensive information on various aspects of mining safety, accident protocols, regulations, and guidance on compensation claims.</p>

                            <h3>Features</h3>
                            <ul>
                                <li><strong>24/7 Availability:</strong> Khaanvaani is accessible round the clock, ensuring prompt responses to text queries.</li>
                                <li><strong>Text Queries:</strong> Users can ask questions and receive relevant information related to the mining industry.</li>
                                <li><strong>Ease of Use:</strong> The interface is designed to be user-friendly, facilitating a seamless experience for individuals seeking mining-related information.</li>
                            </ul>

                            <h2>Tech Stack</h2>
                            <h3>Programming Languages</h3>
                            <ul>
                                <li><strong>Python:</strong> Utilized as the primary programming language.</li>
                            </ul>

                            <h3>Technologies and Libraries</h3>
                            <ul>
                                <li><strong>LangChain:</strong> Leveraged for Natural Language Processing (NLP) capabilities.</li>
                                <li><strong>Pinecone:</strong> Implemented for vector search database functionality, enhancing information retrieval efficiency.</li>
                            </ul>

                            <h3>Tools for Testing and Security</h3>
                            <ul>
                                <li><strong>Bandit:</strong> Used for code vulnerability checking.</li>
                                <li><strong>Wapiti:</strong> Employed for dynamic checking.</li>
                                <li><strong>Pytest:</strong> Utilized for testing purposes.</li>
                                <li><strong>Terraform:</strong> Integrated as an Infrastructure as Code (IAC) tool.</li>
                            </ul>

                            <h2>Future Developments</h2>
                            <h3>Expansion into Regional Languages</h3>
                            <p>We aim to enhance Khaanvaani's accessibility by incorporating support for various regional languages.</p>

                            <h3>Voice Search Integration</h3>
                            <p>Planning to implement voice search functionality, enabling users to interact with Khaanvaani using voice commands.</p>

                            <h3>Legal Representative Assistance</h3>
                            <p>Exploring the addition of features that provide guidance on legal matters pertinent to the mining industry.</p>

                            <h2>Contact Us</h2>
                            <p>For any inquiries or suggestions, feel free to reach out to us at <a href="mailto:contact@email.com">contact@email.com</a>. We value your feedback and strive to continuously improve Khaanvaani to better serve the mining community.</p>
                        """
                        st.write(html_content, unsafe_allow_html=True)

                class contactus:
                    @staticmethod
                    def app():
                        st.write('contactus')

                class statistics:
                    @staticmethod
                    def app():
                        st.write('statistics')

                class MultiApp:
                    def __init__(self):
                        self.apps = []

                    def add_app(self, title, func):
                        self.apps.append({
                            "title": title,
                            "function": func
                        })

                def run():
                    with st.sidebar:
                        app = option_menu(
                            menu_title='Khaanvaani',
                            options=['Home', 'About us', 'Contact us', '📊Stats', 'Account'],
                            icons=['house-fill', 'person', 'phone', '', 'person-circle'],
                            menu_icon='chat-text-fill',
                            default_index=1,
                            styles={
                                "container": {"padding": "5!important", "background-color": 'black'},
                                "icon": {"color": "white", "font-size": "23px"},
                                "nav-link": {"color": "white", "font-size": "20px", "text-align": "left", "margin": "0px", "--hover-color": "#52c4f2"},
                                "nav-link-selected": {"background-color": "#02A6E8 "},
                            }
                        )
                        Authenticator.logout('Log Out', 'sidebar')

                    if app == "Home":
                        AHome.app()
                    if app == "About us":
                        AboutUs.app()
                    if app == "Trending":
                        contactus.app()
                    if app == 'Your Posts':
                        statistics.app()

                run()

            elif not authentication_status:
                with info:
                    st.error('Incorrect Password or username')
            else:
                with info:
                    st.warning('Please feed in your credentials')

        else:
            with info:
                st.warning('Username does not exist, Please Sign up')

except Exception as e:
    st.error('An error occurred: ' + str(e))
    st.success('Refresh Page')
