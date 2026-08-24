import { useRef, useState } from "react";
import { Camera, UploadCloud, Image as ImageIcon, X } from "lucide-react";

function UploadBox() {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const handleFile = (file) => {
    if (!file) return;

    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

    if (!allowedTypes.includes(file.type)) {
      alert("Please upload a JPG, PNG, or WEBP image.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert("Image size must be less than 10MB.");
      return;
    }

    setSelectedFile(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleInputChange = (event) => {
    const file = event.target.files[0];
    handleFile(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();

    const file = event.dataTransfer.files[0];
    handleFile(file);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const removeFile = () => {
    setSelectedFile(null);
    setPreview(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="rounded-2xl border border-[#E2E8F0] bg-white p-6 shadow-sm min-h-[500px]">

      {/* Heading */}
      <div>
        <h2 className="text-xl font-bold text-[#172033]">
          Start New Inspection
        </h2>

        <p className="mt-1 text-sm text-[#64748B]">
          Upload package image to analyze compliance
        </p>
      </div>

      {/* Upload Area */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
        className="mt-5 flex min-h-[330px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-[#B8C7D9] bg-[#FAFCFE] px-6 text-center transition hover:border-[#0F766E] hover:bg-[#F0FDFA]"
      >

        {preview ? (
          /* Image Preview */
          <div className="relative w-full max-w-md">

            <img
              src={preview}
              alt="Selected package"
              className="mx-auto max-h-48 rounded-lg object-contain"
            />

            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                removeFile();
              }}
              className="absolute right-0 top-0 flex h-8 w-8 items-center justify-center rounded-full bg-red-500 text-white shadow-md hover:bg-red-600"
            >
              <X size={17} />
            </button>

            <div className="mt-3 flex items-center justify-center gap-2 text-sm font-medium text-[#12355B]">
              <ImageIcon size={17} />
              <span className="max-w-xs truncate">
                {selectedFile?.name}
              </span>
            </div>

          </div>
        ) : (
          <>
            {/* Camera Icon */}
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[#EFF6FA] text-[#12355B]">
              <Camera size={32} strokeWidth={1.8} />
            </div>

            <p className="mt-4 text-sm font-medium text-[#334155]">
              Drag & drop package image here
            </p>

            <p className="mt-1 text-sm text-[#64748B]">
              or
            </p>

            {/* Upload Button */}
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                fileInputRef.current?.click();
              }}
              className="mt-3 flex items-center gap-2 rounded-lg bg-[#0F766E] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#0B625C]"
            >
              <UploadCloud size={18} />
              Upload Package Image
            </button>
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleInputChange}
          className="hidden"
        />
      </div>

      {/* Supported formats */}
      <p className="mt-4 text-xs text-[#64748B]">
        ⓘ Supports JPG, PNG, WEBP (Max 10MB per image)
      </p>

    </div>
  );
}

export default UploadBox;