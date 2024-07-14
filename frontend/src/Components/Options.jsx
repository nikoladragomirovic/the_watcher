import React, { useState } from "react";

const Options = ({
  username,
  settings,
  setSettings,
  handleLogOut,
  setView,
}) => {
  return (
    <div
      id="options"
      className="py-1 relative px-4 cursor-pointer flex items-center justify-center text-gray-500 border border-gray-500 bg-gray-100 font-extralight text-xl rounded-3xl"
    >
      <p
        onClick={(e) => {
          e.stopPropagation();
          setSettings(!settings);
        }}
      >
        {username}
      </p>
      <div
        className={`${
          settings ? "opacity-100" : "opacity-0 pointer-events-none"
        } absolute top-full space-y-4 mt-8 px-6 py-4 border rounded-3xl bg-white duration-300`}
      >
        <p
          onClick={(e) => {
            e.stopPropagation();
            setView("feed");
            setSettings(false);
          }}
          className="py-1 px-4 text-center text-gray-500 border cursor-pointer border-gray-500 bg-gray-100 font-extralight text-xl rounded-3xl"
        >
          Home
        </p>
        <p
          onClick={(e) => {
            e.stopPropagation();
            setView("settings");
            setSettings(false);
          }}
          className="py-1 px-4 text-center text-gray-500 border cursor-pointer border-gray-500 bg-gray-100 font-extralight text-xl rounded-3xl"
        >
          Settings
        </p>
        <p
          onClick={(e) => {
            handleLogOut(e);
          }}
          className="py-1 px-4 text-center text-gray-500 border cursor-pointer border-gray-500 bg-gray-100 font-extralight text-xl rounded-3xl"
        >
          Logout
        </p>
      </div>
    </div>
  );
};

export default Options;
