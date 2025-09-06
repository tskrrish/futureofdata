import React from "react";
import { DataStoryNotebook } from "../notebook/DataStoryNotebook";

export function DataStoriesTab({ volunteerData }) {
  return (
    <div className="mt-6">
      <DataStoryNotebook volunteerData={volunteerData} />
    </div>
  );
}