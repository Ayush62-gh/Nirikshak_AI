import { useState } from "react";
import {
  Camera,
  Upload,
  Image as ImageIcon,
  Lightbulb,
  CheckCircle2,
  FileText,
  ShieldAlert,
  ArrowRight,
  X,
} from "lucide-react";

function NewInspection() {
  const [images, setImages] = useState([]);

  const handleUpload = (e) => {
    const files = Array.from(e.target.files);

    const newImages = files.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      name: file.name,
    }));

    setImages((prev) => [...prev, ...newImages]);
  };

  const removeImage = (index) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-full bg-[#F6F9FC] px-8 pt-0 pb-8">

      {/* Page Heading */}
      <div className="mb-5">
        <h1 className="text-3xl font-bold text-[#142B4A]">
          New Inspection
        </h1>

        <p className="mt-2 text-lg text-[#6B7F99]">
          Capture or upload package image(s) to begin compliance inspection.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_320px]">

        {/* LEFT */}
        <div className="rounded-2xl border border-[#DDE6F0] bg-white p-7 shadow-sm">

          <h2 className="text-xl font-bold text-[#142B4A]">
            1. Capture or Upload Image
          </h2>

          <p className="mt-1 text-[#6B7F99]">
            Choose a method to add package image(s) for analysis.
          </p>

          {/* Capture / Upload options */}
          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">

            {/* Camera */}
            <button
              type="button"
              className="rounded-xl border border-[#BFE8E3] bg-[#F0FBF9] p-6 text-center transition hover:border-[#0F8F83] hover:shadow-sm"
            >
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#DDF5F1] text-[#0F8F83]">
                <Camera size={32} />
              </div>

              <h3 className="mt-4 text-lg font-bold text-[#142B4A]">
                Scan with Camera
              </h3>

              <p className="mx-auto mt-2 max-w-xs text-sm leading-6 text-[#647A95]">
                Use your device camera to capture package image
              </p>

              <span className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[#0F8F83] px-5 py-2.5 font-semibold text-white">
                <Camera size={18} />
                Open Camera
              </span>
            </button>

            {/* Upload */}
            <label
              htmlFor="package-upload"
              className="cursor-pointer rounded-xl border border-[#C9DDF5] bg-[#F3F8FE] p-6 text-center transition hover:border-[#2878D7] hover:shadow-sm"
            >
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#E2EEFC] text-[#2878D7]">
                <Upload size={32} />
              </div>

              <h3 className="mt-4 text-lg font-bold text-[#142B4A]">
                Upload from Device
              </h3>

              <p className="mx-auto mt-2 max-w-xs text-sm leading-6 text-[#647A95]">
                Upload existing image(s) from your device
              </p>

              <span className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[#2878D7] px-5 py-2.5 font-semibold text-white">
                <Upload size={18} />
                Upload Images
              </span>

              <input
                id="package-upload"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                multiple
                onChange={handleUpload}
                className="hidden"
              />
            </label>

          </div>

          {/* OR */}
          <div className="my-6 flex items-center gap-4 text-sm text-[#71849B]">
            <div className="h-px flex-1 bg-[#DDE6F0]" />
            OR
            <div className="h-px flex-1 bg-[#DDE6F0]" />
          </div>

          {/* Uploaded Images */}
          <div>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-[#142B4A]">
                  Uploaded Images ({images.length})
                </h2>

                <p className="mt-1 text-sm text-[#6B7F99]">
                  You can add multiple images for better analysis.
                </p>
              </div>
            </div>

            {images.length === 0 ? (
              <div className="mt-5 flex min-h-[170px] items-center justify-center rounded-xl border-2 border-dashed border-[#C9D8E8] bg-[#FBFDFF]">
                <div className="text-center">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#EEF4F9] text-[#7289A2]">
                    <ImageIcon size={28} />
                  </div>

                  <p className="mt-3 font-medium text-[#405570]">
                    No images uploaded yet
                  </p>

                  <p className="mt-1 text-sm text-[#8191A5]">
                    Capture or upload images to get started.
                  </p>
                </div>
              </div>
            ) : (
              <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                {images.map((image, index) => (
                  <div
                    key={index}
                    className="relative overflow-hidden rounded-xl border border-[#DDE6F0] bg-white"
                  >
                    <img
                      src={image.preview}
                      alt={image.name}
                      className="h-36 w-full object-contain bg-[#F8FAFC]"
                    />

                    <button
                      type="button"
                      onClick={() => removeImage(index)}
                      className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-red-500 text-white"
                    >
                      <X size={15} />
                    </button>

                    <p className="truncate px-3 py-2 text-xs text-[#647A95]">
                      {image.name}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT SIDEBAR */}
        <div className="space-y-5">

          {/* Tips */}
          <div className="rounded-2xl border border-[#DDE6F0] bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#E8F8F5] text-[#0F8F83]">
                <Lightbulb size={21} />
              </div>

              <h3 className="font-bold text-[#142B4A]">
                Inspection Tips
              </h3>
            </div>

            <p className="mt-5 font-medium text-[#405570]">
              For best results, ensure:
            </p>

            <div className="mt-4 space-y-4">
              {[
                "Image is clear and well-lit",
                "All sides of the package are visible",
                "Focus on label and markings",
                "Avoid glare and blur",
              ].map((tip) => (
                <div key={tip} className="flex items-start gap-3">
                  <CheckCircle2
                    size={18}
                    className="mt-0.5 shrink-0 text-[#0F8F83]"
                  />
                  <span className="text-sm text-[#526982]">{tip}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Formats */}
          <div className="rounded-2xl border border-[#DDE6F0] bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#E5F0FF] text-[#2878D7]">
                <FileText size={20} />
              </div>

              <h3 className="font-bold text-[#142B4A]">
                Supported Formats
              </h3>
            </div>

            <p className="mt-5 text-sm text-[#526982]">
              JPG, JPEG, PNG, WEBP
            </p>

            <p className="mt-2 text-sm text-[#526982]">
              Max file size: 10MB per image
            </p>
          </div>

          {/* Privacy */}
          <div className="rounded-2xl border border-[#F0DFAD] bg-[#FFF9E9] p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#FFF0C5] text-[#D99A00]">
                <ShieldAlert size={20} />
              </div>

              <h3 className="font-bold text-[#142B4A]">
                Privacy & Security
              </h3>
            </div>

            <p className="mt-4 text-sm leading-6 text-[#526982]">
              All images are processed securely and are not stored permanently.
            </p>
          </div>

          {/* Start Inspection */}
          <button
            type="button"
            disabled={images.length === 0}
            className="flex w-full items-center justify-center gap-3 rounded-xl bg-[#E1E7EE] px-5 py-4 font-semibold text-[#8A99AA] disabled:cursor-not-allowed"
          >
            Start Inspection
            <ArrowRight size={20} />
          </button>

        </div>
      </div>
    </div>
  );
}

export default NewInspection;