import Login from "./Login";
import Page from "./Page";
import { useState, useEffect } from "react";

function App() {
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    const username = localStorage.getItem("username");
    const session_token = localStorage.getItem("session_token");

    if (username && session_token) {
      setLoggedIn(true);
    }
  }, []);

  return (
    <>
      {loggedIn ? (
        <Page setLoggedIn={setLoggedIn} />
      ) : (
        <Login setLoggedIn={setLoggedIn} />
      )}
    </>
  );
}

export default App;
