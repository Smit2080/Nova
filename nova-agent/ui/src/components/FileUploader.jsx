import React, { useRef } from "react";

export default function FileUploader({ onFilesSelected }) {
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    onFilesSelected(files);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    onFilesSelected(files);
  };

  return (
    <div
      className="file-upload-container"
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current.click()}
    >
      <input
        type="file"
        ref={fileInputRef}
        className="hidden-input"
        multiple
        onChange={handleFileSelect}
      />
      <span className="upload-icon">📎</span>
    </div>
  );
}