import React, { useState } from "react";
import { HiTrash, HiDownload } from "react-icons/hi";
import { HiFaceSmile } from "react-icons/hi2";
import { IoMdSave } from "react-icons/io";

const Feed = ({ loading, frames, clearFrame, saveFace }) => {
  const [editNameMode, setEditNameMode] = useState(-1);
  const [inputValue, setInputValue] = useState("");
  const [error, setError] = useState("");

  const errorMap = {
    400: "No faces in frame",
    409: "Name already exists",
    303: "Face already exists",
  };

  const formatDate = (dateString) => {
    const options = { year: "numeric", month: "short", day: "numeric" };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const formatTime = (timeString) => {
    const options = { hour: "numeric", minute: "numeric", second: "numeric" };
    return new Date(`1970-01-01T${timeString}Z`).toLocaleTimeString(
      undefined,
      options
    );
  };

  const handleSaveFace = async () => {
    let response = await saveFace(inputValue, frame.cameraId, frame.name);
    if (response === 200) {
      setEditNameMode(-1);
      setInputValue("");
    } else {
      setError(errorMap[response]);
    }
  };

  return (
    <div className="text-gray-500">
      {frames.length === 0 && !loading ? (
        <div className="h-screen flex items-center justify-center">
          <p className="text-gray-500">Nothing to see here 😄</p>
        </div>
      ) : (
        <div className="pt-24 grid grid-cols-1 gap-4">
          {frames.map((frame, frameIndex) => (
            <div
              className="bg-gray-200 rounded-3xl py-2 border border-gray-500"
              key={frameIndex}
            >
              <div className="flex flex-row items-center justify-evenly">
                <p className="text-center">{frame.cameraName}</p>
              </div>
              <div className="flex justify-center">
                <a
                  href={frame.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cursor-pointer"
                >
                  <img
                    className="py-2 w-[300px]"
                    src={frame.url}
                    alt="camera feed"
                  />
                </a>
              </div>
              <div className="w-full flex flex-row items-center justify-evenly pt-2 pb-4 text-4xl text-gray-500">
                <HiTrash
                  className="text-rose-500 cursor-pointer"
                  onClick={() => clearFrame(frame.cameraId, frame.name)}
                />
                <HiFaceSmile
                  className="text-emerald-500 cursor-pointer"
                  onClick={() => {
                    setEditNameMode(
                      editNameMode === frameIndex ? -1 : frameIndex
                    );
                    setError("");
                    setInputValue("");
                  }}
                />
                <HiDownload className="text-sky-500" />
              </div>
              {editNameMode === frameIndex ? (
                <>
                  <div className="w-full px-6 flex items-center justify-center pb-4 pt-2">
                    <input
                      className="px-4 py-1 rounded-3xl mr-2 focus:outline-0 bg-gray-100"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                    />
                    <IoMdSave
                      className="text-3xl cursor-pointer"
                      onClick={saveFace}
                    />
                  </div>
                  <p className="text-rose-600 w-full text-center mb-4">
                    {error}
                  </p>
                </>
              ) : null}
              <div className="flex flex-row w-full items-center justify-evenly">
                <p className="text-center tracking-wide">
                  {formatDate(frame.date)}
                </p>
                <p className="text-center tracking-wider">
                  {formatTime(frame.time)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Feed;
