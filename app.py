import streamlit as st
import pandas as pd
import altair as alt

from google import genai

client = genai.Client(api_key=st.secrets["gemini"]["api_key"])




st.set_page_config(page_title="Tariff Explainer Chatbot", layout="wide")
st.title("📦 U.S. Tariff Impact Visualizer + Economic Chatbot")
st.caption("Explore how tariffs affect imports, prices, and supply chains.")

# Load your CSV data
df = pd.read_csv("data.csv")


# Initialize session state for messages if it doesn't exist
if "messages" not in st.session_state:
    st.session_state["messages"] = []


if "country" not in st.session_state:
    st.session_state.country = None



# Country dropdown
country = st.selectbox("🌍 Select a Country", df["Country"].unique())

# Filter country data
selected = df[df["Country"] == country].iloc[0]

#Reset chat history if country changes
if st.session_state.country != country:
    st.session_state.messages = []
    st.session_state.country = country


# Show summary metrics
col1, col2, col3 = st.columns(3)
col1.metric("📊 Tariff", f"{selected['Tariff Imposed by US (%)']}%")
col2.metric("💰 Import Value", f"${selected['Estimated Annual Import Value (Billion USD)']}B")
col3.metric("🔄 Base vs. Tariff Price", f"↑ {selected['Tariff Imposed by US (%)']}%")

st.divider()

# Details section
st.subheader(f"🛠️ Product Impact for {country}")
st.markdown(f"**Top Product Categories:** {selected['Top Product Categories']}")
st.markdown(f"**Specific Products:** {selected['Specific Product Names']}")
st.markdown(f"**Alternative Suppliers:** `{selected['Alternative Suppliers']}`")
st.markdown(f"**Use Case Impact:** {selected['Use Case Impact']}")

st.divider()



# Simulate price impact
base_price = 100  # Use a dummy base price
tariff_rate = selected['Tariff Imposed by US (%)']
price_after_tariff = base_price * (1 + tariff_rate / 100)

# Create a dataframe for the chart
chart_df = pd.DataFrame({
    "Label": ["Base Price", "After Tariff"],
    "Price (USD)": [base_price, price_after_tariff]
})

# Altair bar chart
st.subheader("💸 Price Impact Visualization")
chart = alt.Chart(chart_df).mark_bar().encode(
    x=alt.X("Label", sort=None),
    y="Price (USD)",
    color="Label"
).properties(
    width=200,
    height=500
)

st.altair_chart(chart, use_container_width=True)


# Chatbot section

st.subheader("🤖 Chatbot")
st.divider()
st.subheader(f"🤖 Ask a Question about the Tariff on {country}")

# Display previous messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])


st.markdown("""<script>
var chatContainer = document.querySelector(".stChatMessage");
if (chatContainer) {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}
</script>""", unsafe_allow_html=True)


if prompt := st.chat_input("Ask me about economic policy, tariffs, or trade..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)


    
    # Pre-responses for general questions
    general_questions = {
        "who are you": "I am an AI assistant designed to explain economic policies, particularly tariffs and their impacts.",
        "what can you do": "I can provide information about U.S. tariffs, their potential effects on prices and imports, and related economic concepts. You can ask me specific questions about tariffs on different countries or products.",
        "tell me a joke": "I'm still learning how to be funny in the realm of economics!",
        "hello": "Hey there! Ask me something about trade, economics or tarrifs.",
        "hi": "Hey there! Ask me something about trade, economics or tarrifs.",
        "how are you": "I'm just a program, but I'm here to help you with your questions about tariffs and trade!",
    }

    lowered_prompt = prompt.lower()
    if lowered_prompt in general_questions:
        response_content = general_questions[lowered_prompt]
        st.session_state["messages"].append({"role": "assistant", "content": response_content})
        with st.chat_message("assistant"):
            st.write(response_content)
    else:
        # Prepare the prompt for Gemini
        context = f"""
        You are an AI economic policy explainer. Your primary focus is on U.S. tariffs, their impact on import values, product prices, and related economic policies.
        
        Here is the current tariff information for {country}:
        Tariff Imposed by US: {selected['Tariff Imposed by US (%)']}%
        Estimated Annual Import Value: ${selected['Estimated Annual Import Value (Billion USD)']} Billion
        Top Product Categories: {selected['Top Product Categories']}
        Specific Products: {selected['Specific Product Names']}
        Use Case Impact: {selected['Use Case Impact']}
        Alternative Suppliers: {selected['Alternative Suppliers']}

        You should only answer questions that are directly related to these topics. If a question is outside of this scope, politely decline to answer.


        Here is the conversation history:
        """
        for msg in st.session_state["messages"][:-1]:  # Exclude the current user prompt
            context += f"{msg['role']}: {msg['content']}\n"

        current_prompt = st.session_state["messages"][-1]["content"]

        final_prompt = f"{context}\nUser's current question: {current_prompt}\n\nAssistant's response:"

        ask_for_resources =  any(word in current_prompt.lower() for word in ["resources", "links", "learn more"])

        if ask_for_resources:
            final_prompt += " Also, provide a few relevant resources or links where the user can learn more about this topic."

        with st.spinner("🤖 Generating explanation..."):
            try:
                response = client.models.generate_content(model="gemini-2.0-flash", contents=final_prompt)
                response_content = response.text
                st.session_state["messages"].append({"role": "assistant", "content": response_content})
                with st.chat_message("assistant"):
                    st.write(response_content)

                    # Suggest relevant resources

                    if ask_for_resources:
                        st.subheader("📚 Explore Further")
                        if country:
                            st.markdown(f"- [U.S. International Trade Commission on trade with {country}](https://www.usitc.gov/)") # Replace with actual relevant links
                            st.markdown("- [Bureau of Economic Analysis (BEA)](https://www.bea.gov/)")
                            st.markdown("- [Congressional Research Service Reports on Trade](https://crsreports.congress.gov/)") # Example
                        st.markdown("- [World Trade Organization (WTO)](https://www.wto.org/)")

            except Exception as e:
                st.error(f"Error: {e}")



# #intent classifier
# generic_responses = {
#     "who are you": "I'm your economic policy assistant, here to explain tariffs, pricing, and global trade issues.",
#     "hello": "Hey there! Ask me something about trade, economics or tarrifs.",
#     "what can you do": "I specialize in explaining economic policies, trade relations, and tariffs using real-time data.",
#     "how are you": "I'm just a program, but I'm here to help you with your questions about tariffs and trade!",
#     "what is tarrif": "A tariff is a tax imposed by a government on imported goods. It can affect prices and trade relations.",
#     "what is the impact of tarrif": "Tariffs can increase the cost of imported goods, affecting prices and trade relations.",
#     "how to calculate tarrif": "Tariffs are usually calculated as a percentage of the value of the imported goods.",
#     "how to avoid tarrif": "To avoid tariffs, companies may source products from countries with lower or no tariffs.",
#     "how to calculate tarrif": "Tariffs are usually calculated as a percentage of the value of the imported goods.",
# }

# def classify_question(q):
#     q= q.lower()
#     if any(word in q for word in ["tariff", "trade", "import", "export", "price", "policy", "product"]):
#         return "relevant"
    
#     for g in generic_responses.keys():
#         if g in q:
#             return "generic"
#     return "irrelevant"


# #show previous chat history

# for entry in st.session_state.chat_history:
#     st.markdown(f"**User:** {entry['User']}")
#     st.markdown(f"**Bot:** {entry['Bot']}")
   


# user_question = st.text_input("Ask question:")
# # explain_button = st.button("🔍 Explain")

# if st.button("📤 Ask") and user_question:
#     intention = classify_question(user_question)
   
#     if intention == "generic":
#         response = generic_responses[next(k for k in generic_responses if k in user_question.lower())]

#     elif intention == "irrelevant":
#         response = "⚠️ I'm designed to answer questions about trade, tariffs, and economics. Please stay on-topic."

#     elif intention == "relevant":
#         base_context = f"""
#         The U.S. currently imposes a {tariff_rate}% tariff on imports from {country}.
#         Top product categories include: {selected['Top Product Categories']}.
#         Example products: {selected['Specific Product Names']}.
#         Use cases: {selected['Use Case Impact']}.
#         Alternative suppliers: {selected['Alternative Suppliers']}.
#         """

#         prompt = base_context +f"\nUser question: {user_question}"

#         try:
#             with st.spinner("🤖 Generating answer..."):
#                 result = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
#                 response = result.text
#                 # st.session_state.chat_history.append({"user": user_question, "gemini": explanation})
#                 # st.markdown(f"**Bot:** {explanation}")

#         except Exception as e:
#             st.markdown(f"⚠️ Error: {e}")

#         st.session_state.chat_history.append({"User": user_question, "Bot": response})  
#         st.markdown(f"**Bot:** {response}")
    








# if explain_button and user_question:
#     prompt = f"""
#     The U.S. currently imposes a {tariff_rate}% tariff on imports from {country}.
#     The major product categories impacted are: {selected['Top Product Categories']}.
#     Example products include: {selected['Specific Product Names']}.
#     These products are used for: {selected['Use Case Impact']}.
#     The annual import value is around ${selected['Estimated Annual Import Value (Billion USD)']} billion.
#     Alternative suppliers include: {selected['Alternative Suppliers']}.

#     User's question: {user_question}

#     Answer the question based on the above information. If the User's question is irrelevant, please say "I can't answer this ".
   
#     """

#     with st.spinner("🤖 Generating answer..."):
#         try:
#             response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
#             explanation = response.text
#             st.markdown("### 🤖 Answer")
#             st.write(explanation)
#         except Exception as e:
#             st.error(f"Error: {e}")