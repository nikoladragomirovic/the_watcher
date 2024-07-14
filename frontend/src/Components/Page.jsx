import React, { useState, useEffect } from "react";
import Options from "./Options";
import Settings from "./Settings";
import Feed from "./Feed";

const Page = ({ setLoggedIn }) => {
  const [frames, setFrames] = useState([]);
  const [settings, setSettings] = useState(false);
  const [view, setView] = useState("feed");
  const [chatId, setChatId] = useState("");
  const [loading, setLoading] = useState(true);
  const [cameras, setCameras] = useState([]);
  const [faces, setFaces] = useState([]);

  async function fetchSettings() {
    const response = await fetch("http://127.0.0.1:5000/settings", {
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
      setCameras(data.cameras);
      setFaces(data.faces);
      setChatId(data.chat_id);
    } else {
      console.error("Failed to fetch settings", response.status);
    }
  }

  async function fetchFrames() {
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
      setFrames(data.reverse());
      setLoading(false);
    } else {
      console.error("Failed to fetch frames", response.status);
    }
  }

  useEffect(() => {
    fetchFrames();
    fetchSettings();
  }, []);

  const handleLogOut = async (e) => {
    e.preventDefault();
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
  };

  const deleteFace = async (name) => {
    const response = await fetch("http://127.0.0.1:5000/delete", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: localStorage.getItem("username"),
        session_token: localStorage.getItem("session_token"),
        name: name,
      }),
    });
    if (response.ok) {
      console.log("Face deleted successfully");
      fetchSettings();
    } else {
      console.error("Failed to delete face");
    }
  };

  const deleteCamera = async (camera_id) => {
    const response = await fetch("http://127.0.0.1:5000/exclude", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: localStorage.getItem("username"),
        session_token: localStorage.getItem("session_token"),
        camera_id: camera_id,
      }),
    });
    if (response.ok) {
      console.log("Camera deleted successfully");
      fetchSettings();
      fetchFrames();
    } else {
      console.error("Failed to delete camera");
    }
  };

  const enrollCamera = async (camera_id, camera_name) => {
    const response = await fetch("http://127.0.0.1:5000/enroll", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: localStorage.getItem("username"),
        session_token: localStorage.getItem("session_token"),
        camera_id: camera_id,
        name: camera_name,
      }),
    });
    if (response.ok) {
      console.log("Camera enrolled successfully", response.status);
      fetchSettings();
      fetchFrames();
      return 200;
    } else {
      console.error("Failed to enroll camera", response.status);
      return response.status;
    }
  };

  const renameCamera = async (camera_id, camera_name) => {
    const response = await fetch("http://127.0.0.1:5000/rename", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: localStorage.getItem("username"),
        session_token: localStorage.getItem("session_token"),
        camera_id: camera_id,
        name: camera_name,
      }),
    });
    if (response.ok) {
      console.log("Camera renamed successfully");
      fetchSettings();
      fetchFrames();
    } else {
      console.error("Failed to rename camera");
    }
  };

  const clearFrame = async (camera_id, image_name) => {
    const response = await fetch("http://127.0.0.1:5000/clear", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: localStorage.getItem("username"),
        session_token: localStorage.getItem("session_token"),
        camera_id: camera_id,
        image_name: image_name,
      }),
    });
    if (response.ok) {
      console.log("Frame cleared successfully");
      fetchSettings();
      fetchFrames();
    } else {
      console.error("Failed to clear frame");
    }
  };

  const saveFace = async (name, camera_id, frame_name) => {
    const response = await fetch("http://127.0.0.1:5000/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: localStorage.getItem("username"),
        session_token: localStorage.getItem("session_token"),
        name: name,
        camera_id: camera_id,
        frame_name: frame_name,
      }),
    });
    if (response.ok) {
      console.log("Face saved successfully", response.status);
      clearFrame(camera_id, frame_name);
      return 200;
    } else {
      console.error("Failed to save face", response.status);
      return response.status;
    }
  };

  const updateTelegram = async (chat_id) => {
    const response = await fetch("http://127.0.0.1:5000/telegram", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: localStorage.getItem("username"),
        session_token: localStorage.getItem("session_token"),
        chat_id: chat_id,
      }),
    });
    if (response.ok) {
      console.log("Telegram id updated successfully");
      fetchFrames();
      fetchSettings();
    } else {
      console.error("Failed to update telegram id");
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
        <Options
          username={localStorage.getItem("username")}
          settings={settings}
          setSettings={setSettings}
          handleLogOut={handleLogOut}
          setView={setView}
        />
      </div>
      {view === "feed" && (
        <Feed
          loading={loading}
          frames={frames}
          clearFrame={clearFrame}
          saveFace={saveFace}
        />
      )}
      {view === "settings" && (
        <Settings
          cameras={cameras}
          faces={faces}
          chat_id={chatId}
          deleteFace={deleteFace}
          deleteCamera={deleteCamera}
          enrollCamera={enrollCamera}
          renameCamera={renameCamera}
          updateTelegram={updateTelegram}
        />
      )}
    </div>
  );
};

export default Page;
