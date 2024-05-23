import React, { useState, useEffect } from "react";

const Page = ({ setLoggedIn }) => {
  const [photos, setPhotos] = useState([]);
  const [settings, setSettings] = useState(false);

  useEffect(() => {
    async function fetchphotos() {
      try {
        const response = await fetch("http://127.0.0.1:5000/frames", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams({
            username: localStorage.getItem("username"),
            session_token: localStorage.getItem("session_token"),
          }),
        });
        if (response.ok) {
          const data = await response.json();
          setPhotos(data);
        } else {
          console.error("Failed to fetch photos");
        }
      } catch (error) {
        console.error("Error:", error);
      }
    }

    fetchphotos();
  }, []);

  const handleLogOut = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("http://127.0.0.1:5000/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
          username: localStorage.getItem("username"),
          session_token: localStorage.getItem("session_token"),
        }),
      });
      if (response.ok) {
        const jsonResponse = await response.json();
        console.log("Logout successful", jsonResponse);
        localStorage.removeItem("username");
        localStorage.removeItem("session_token");
        setLoggedIn(false);
      } else {
        console.error("Logout failed");
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div
      onClick={() => {
        setSettings(false);
      }}
      className="w-full font-dosis min-h-screen flex flex-col items-center justify-start"
    >
      <div className="fixed bg-white border-b rounded-b-2xl border-gray-500 flex flex-row justify-around py-4 w-full">
        <div className="py-1 relative px-4 cursor-pointer flex items-center justify-center text-gray-500 border border-gray-500 bg-gray-100 font-extralight text-xl rounded-3xl">
          <p
            onClick={(e) => {
              e.stopPropagation();
              setSettings(!settings);
            }}
          >
            {localStorage.getItem("username")}
          </p>
          <div
            className={`${
              settings ? "opacity-100" : "opacity-0"
            } absolute top-full space-y-4 mt-8 px-6 py-4 border rounded-3xl bg-white duration-300`}
          >
            <p
              onClick={(e) => {
                handleLogOut(e);
              }}
              className="py-1 px-4 text-gray-500 border cursor-pointer border-gray-500 bg-gray-100 font-extralight text-xl rounded-3xl"
            >
              Logout
            </p>
            <p className="py-1 px-4 text-gray-500 border cursor-pointer border-gray-500 bg-gray-100 font-extralight text-xl rounded-3xl">
              Settings
            </p>
          </div>
        </div>
      </div>
      <div className="pt-20 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
        {photos.map((photo, index) => (
          <div
            key={index}
            className="border border-gray-500 p-5 m-4 bg-gray-50 rounded-3xl"
          >
            <img key={index} src={photo.url} alt={`Image ${index}`} />
            <p>{photo.camera}</p>
            <p>{photo.time}</p>
            <div className="flex flex-row justify-start space-x-6 text-lg items-start"></div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Page;
