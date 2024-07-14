import React, { useState } from "react";
import { IoIosClose } from "react-icons/io";
import { HiOutlinePlusSmall } from "react-icons/hi2";
import { IoPerson } from "react-icons/io5";
import { BiSolidEdit } from "react-icons/bi";
import { FaCheck } from "react-icons/fa6";
import { IoChatbox } from "react-icons/io5";

const Settings = ({
  cameras,
  faces,
  chat_id,
  deleteFace,
  deleteCamera,
  enrollCamera,
  renameCamera,
  updateTelegram,
}) => {
  const [newCameraId, setNewCameraId] = useState("");
  const [newCameraName, setNewCameraName] = useState("");
  const [newChatId, setNewChatId] = useState("");
  const [nameEditMode, setNameEditMode] = useState(false);
  const [editCameraName, setEditCameraName] = useState("");
  const [telegramEditMode, setTelegramEditMode] = useState(false);
  const [error, setError] = useState("");

  const errorMap = {
    303: "Camera linked to other account",
    401: "Camera id does not exist",
    409: "Camera already linked",
  };

  const handleEnrollCamera = async () => {
    const response = await enrollCamera(newCameraId, newCameraName);
    if (response === 200) {
      setNewCameraId("");
      setNewCameraName("");
      setError("");
    } else {
      setError(errorMap[response]);
    }
  };

  return (
    <div className="w-full pt-24 font-dosis min-h-screen flex flex-col items-center justify-start">
      <h1 className="text-3xl">Settings</h1>
      <h2 className="text-xl mt-10 mb-4">Cameras</h2>
      <div className="w-[200px]">
        <ul className="space-y-4">
          {cameras.map((camera) => (
            <li
              className="flex text-lg flex-row py-2 space-x-1 items-center justify-between px-4 border border-gray-500 rounded-3xl bg-gray-200"
              key={camera.id}
            >
              <div>
                {nameEditMode ? (
                  <div className="flex flex-row items-center my-2">
                    <input
                      placeholder={camera.name}
                      value={editCameraName}
                      onChange={(e) => setEditCameraName(e.target.value)}
                      className="mr-2 w-3/4 bg-gray-100 rounded-3xl px-3 py-1 text-sm focus:outline-0"
                    ></input>
                    <FaCheck
                      onClick={() => {
                        renameCamera(
                          camera.id,
                          editCameraName !== "" ? editCameraName : "No Name"
                        );
                        setNameEditMode(false);
                        setEditCameraName("");
                      }}
                      className=""
                    />
                    <IoIosClose
                      className="text-3xl"
                      onClick={() => {
                        setNameEditMode(false);
                        setEditCameraName("");
                      }}
                    />
                  </div>
                ) : (
                  <div className="flex flex-row items-center">
                    <p className="mr-1">{camera.name}</p>
                    <BiSolidEdit
                      onClick={() => setNameEditMode(true)}
                      className="text-lg -mb-0.5"
                    />
                  </div>
                )}
                <p className="text-sm text-gray-700">{camera.id}</p>
              </div>
              <IoIosClose
                className={`text-2xl ${nameEditMode ? "hidden" : ""}`}
                onClick={() => deleteCamera(camera.id)}
              />
            </li>
          ))}
        </ul>
        <p className="text-rose-600 w-full text-center mt-4">{error}</p>
        <div className="flex flex-col space-y-4 items-center mt-4">
          <input
            type="text"
            placeholder="New Camera Name"
            value={newCameraName}
            onChange={(e) => setNewCameraName(e.target.value)}
            className="rounded-3xl px-3 placeholder:text-gray-400 py-1.5 border border-gray-500 focus:outline-0"
          />
          <input
            type="text"
            placeholder="New Camera ID"
            value={newCameraId}
            onChange={(e) => setNewCameraId(e.target.value)}
            className="px-3 py-1.5 rounded-3xl placeholder:text-gray-400 border border-gray-500 focus:outline-0"
          />
          <HiOutlinePlusSmall
            onClick={handleEnrollCamera}
            className="text-3xl bg-gray-200 rounded-3xl border border-gray-500"
          />
        </div>
      </div>
      <h2 className="text-xl mt-10 mb-4">People</h2>
      <ul className="w-[150px] space-y-4">
        {faces.map((face) => (
          <li
            className="flex text-lg flex-row space-x-1 items-center py-0.5 justify-between px-2 border border-gray-500 rounded-3xl bg-gray-200"
            key={face}
          >
            <span className="flex flex-row items-center">
              <IoPerson className="mr-1" />
              {face}
            </span>
            <IoIosClose className="text-2xl" onClick={() => deleteFace(face)} />
          </li>
        ))}
      </ul>
      <h2 className="text-xl mt-10 mb-3">Telegram ID</h2>
      {telegramEditMode || chat_id === "" ? (
        <div className="flex flex-col items-center">
          <input
            type="text"
            placeholder="New Chat ID"
            value={newChatId}
            onChange={(e) => setNewChatId(e.target.value)}
            className="px-3 py-1.5 rounded-3xl placeholder:text-gray-400 border mb-3 mr-3 border-gray-500 focus:outline-0"
          />
          <div className="flex flex-row items-center justify-center">
            <FaCheck
              onClick={() => {
                updateTelegram(newChatId);
                setTelegramEditMode(false);
                setNewChatId("");
              }}
              className="text-xl text-gray-600 mr-2"
            />
            <IoIosClose
              onClick={() => {
                setTelegramEditMode(false);
                setNewChatId("");
              }}
              className={`text-3xl ${chat_id === "" ? "hidden" : ""}`}
            />
          </div>
        </div>
      ) : (
        <div className="flex flex-row items-center justify-center">
          <p className="text-gray-500 mr-2 text-lg">{chat_id}</p>
          <BiSolidEdit
            className="text-lg -mb-0.5"
            onClick={() => setTelegramEditMode(true)}
          />
        </div>
      )}
    </div>
  );
};

export default Settings;
