Initial prompt to gemini:

_I want to do some ai coding. Help me write a prompt. Basically, I want an app that lets me enter a lego set id number (eg "42228"), looks up the lego set and returns the number, name of the kit, and type (eg Technic) and writes it to an existing google doc in a new row on a table_


And then the prompt it created that I used in claude (4.5 sonnet, free):

_Task: Create a Streamlit web application that acts as a Lego Set Inventory logger.
Functionality:
1. Provide a text input for a Lego Set ID.
2. When a button is clicked, use the Rebrickable API to fetch the Set Name, Year, and Theme.
3. Display the fetched data and the set's image in the app UI for confirmation.
4. Use the google-api-python-client to append this data as a new row in a table within a specific Google Doc.
5. Include a "Recent Additions" section using st.table to show what was just added.
Technical Details:
* Use st.secrets to handle the Google Service Account credentials and Lego API Key.
* Provide instructions on how to set up the .streamlit/secrets.toml file._
