import React, { useState } from "react";

const Login = ({ setLoggedIn }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [register, setRegister] = useState(false);
  const [status, setStatus] = useState(0);

  const errorMap = {
    400: "Username or password missing",
    401: "Wrong password",
    404: "Username does not exist",
    409: "Username already exists",
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(
        "http://127.0.0.1:5000/" + (register ? "register" : "login"),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams({
            username: username,
            password: password,
          }),
        }
      );
      const jsonResponse = await response.json();
      if (response.ok) {
        localStorage.setItem("username", username);
        localStorage.setItem("session_token", jsonResponse.session_token);
        setLoggedIn(true);
      } else {
        console.error(jsonResponse);
      }
      setStatus(response.status);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div className="flex font-dosis flex-col items-center justify-center w-full min-h-screen bg-white">
      <form
        className="flex flex-col items-center justify-center"
        onSubmit={handleSubmit}
      >
        <input
          className="px-4 py-2 text-xl focus:outline-none mb-8 caret-gray-300 text-gray-500 font-light border-gray-500 placeholder:text-gray-500 placeholder:font-light rounded-3xl"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
        />
        <input
          className="px-4 py-2 text-xl focus:outline-none mb-4 caret-gray-300 text-gray-500 font-light border-gray-500 placeholder:text-gray-500 placeholder:font-light rounded-3xl"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
        <p className="text-md text-rose-500 mb-4">{errorMap[status]}</p>
        <button
          type="submit"
          className="py-1 px-4 text-gray-500 border border-gray-500 bg-gray-100 font-extralight mb-4 text-xl rounded-3xl"
        >
          {register ? "Register" : "Login"}
        </button>
      </form>
      {register ? (
        <button
          className="text-md font-light text-gray-500 cursor-pointer underline"
          onClick={() => {
            setRegister(false);
            setStatus(0);
          }}
        >
          Already have an account?
          <br />
          Login
        </button>
      ) : (
        <button
          className="text-md font-light text-gray-500 cursor-pointer underline"
          onClick={() => {
            setRegister(true);
            setStatus(0);
          }}
        >
          Don't have an account?
          <br />
          Register
        </button>
      )}
    </div>
  );
};

export default Login;
