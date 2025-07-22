import streamlit as st

st.title("Debug Test")
st.write("Basic Streamlit is working")

# Test session state
if 'test_value' not in st.session_state:
    st.session_state.test_value = "Initial value"

st.write(f"Session state value: {st.session_state.test_value}")

if st.button("Change Value"):
    st.session_state.test_value = "Changed value!"
    st.write("Value changed!")

# Test basic tabs
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])

with tab1:
    st.write("This is tab 1")
    if st.button("Button 1"):
        st.write("Button 1 clicked!")

with tab2:
    st.write("This is tab 2")
    if st.button("Button 2"):
        st.write("Button 2 clicked!")