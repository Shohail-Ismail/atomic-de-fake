import streamlit as st


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    if st.button("Log in"):
        st.session_state.logged_in = True
        st.rerun()

def logout():
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()


if __name__ == "__main__":

    login_page = st.Page(login, title="Log in", icon=":material/login:")
    logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

    # dashboard = st.Page(
    #     "reports/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True
    # )
    # bugs = st.Page("reports/bugs.py", title="Bug reports", icon=":material/bug_report:")
    # alerts = st.Page(
    #     "reports/alerts.py", title="System alerts", icon=":material/notification_important:"
    # )

    # search = st.Page("tools/search.py", title="Search", icon=":material/search:")
    # history = st.Page("tools/history.py", title="History", icon=":material/history:")

    
    user_post_page = st.Page("user_post.py", title="User post", icon=":material/add_circle:")
    contributor_page = st.Page("contributor.py", title="Contributor", icon=":material/delete:")

    
    if st.session_state.logged_in:
        pg = st.navigation(
            {
                "Account": [logout_page],
                # "Reports": [dashboard, bugs, alerts],
                # "Tools": [search, history],
                "AtomicDeFake": [user_post_page, contributor_page],
            }
        )
        st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
    else:
        pg = st.navigation([login_page])

    pg.run()