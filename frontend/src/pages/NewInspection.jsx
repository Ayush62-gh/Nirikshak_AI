import { useState } from "react";
import {
  Camera,
  Upload,
  Image as ImageIcon,
  Lightbulb,
  CheckCircle2,
  XCircle,
  AlertCircle,
  AlertTriangle,
  FileText,
  ShieldAlert,
  ArrowRight,
  X,
  Loader2,
} from "lucide-react";
import { submitScan } from "../services/api";

function NewInspection() {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scanResult, setScanResult] = useState(null);

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

  const handleSubmit = async () => {
    if (images.length === 0 || loading) return;

    setLoading(true);
    setError(null);
    setScanResult(null);

    try {
      const result = await submitScan(images[0].file);
      setScanResult(result);
    } catch (err) {
      setError(err.message || "An unexpected error occurred during scan submission.");
    } finally {
      setLoading(false);
    }
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
        <div>
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

            {/* 2. Review & Submit Section */}
            <div className="mt-8 pt-6 border-t border-[#DDE6F0]">
              <h2 className="text-xl font-bold text-[#142B4A]">
                2. Review & Submit
              </h2>
              <p className="mt-1 text-sm text-[#6B7F99]">
                Submit the staged image to the backend API for compliance analysis.
              </p>

              <div className="mt-4">
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={images.length === 0 || loading}
                  className={`inline-flex items-center justify-center gap-2.5 rounded-xl px-6 py-3.5 font-semibold transition-all ${
                    images.length === 0
                      ? "bg-[#E1E7EE] text-[#8A99AA] cursor-not-allowed"
                      : loading
                      ? "bg-[#2878D7]/80 text-white cursor-wait opacity-90"
                      : "bg-[#2878D7] text-white hover:bg-[#1F64B8] shadow-sm cursor-pointer"
                  }`}
                >
                  {loading ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      <span>Analyzing Package...</span>
                    </>
                  ) : (
                    <>
                      <ArrowRight size={20} />
                      <span>Submit for Inspection</span>
                    </>
                  )}
                </button>
              </div>
            </div>

          </div>

          {/* Error Display Banner */}
          {error && (
            <div className="mt-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-5 text-red-800 shadow-sm">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
              <div className="flex-1">
                <h4 className="font-bold text-red-900">Inspection Failed</h4>
                <p className="mt-1 text-sm leading-relaxed text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Compliance Results Section */}
          {scanResult && (
            <div className="mt-6 rounded-2xl border border-[#DDE6F0] bg-white p-7 shadow-sm">
              {/* Header */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#DDE6F0] pb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-[#142B4A]">
                      Inspection Results
                    </h2>
                    {scanResult.scan_id && (
                      <span className="rounded-full bg-[#E2EEFC] px-3 py-0.5 text-xs font-semibold text-[#2878D7]">
                        Scan #{scanResult.scan_id.slice(0, 8)}
                      </span>
                    )}
                  </div>
                  {scanResult.timestamp && (
                    <p className="mt-1 text-xs text-[#6B7F99]">
                      Scanned on {new Date(scanResult.timestamp).toLocaleString()}
                    </p>
                  )}
                </div>

                {/* Compliance Status Badge */}
                <div>
                  {scanResult.compliance?.status === "COMPLIANT" && (
                    <div className="flex items-center gap-2 rounded-xl border border-[#BFE8E3] bg-[#F0FBF9] px-4 py-2 text-[#0F8F83]">
                      <CheckCircle2 size={20} />
                      <span className="font-bold text-sm">COMPLIANT</span>
                    </div>
                  )}
                  {scanResult.compliance?.status === "NON_COMPLIANT" && (
                    <div className="flex items-center gap-2 rounded-xl border border-[#F8C4C4] bg-[#FDF2F2] px-4 py-2 text-[#D9381E]">
                      <XCircle size={20} />
                      <span className="font-bold text-sm">NON-COMPLIANT</span>
                    </div>
                  )}
                  {scanResult.compliance?.status === "PARTIAL" && (
                    <div className="flex items-center gap-2 rounded-xl border border-[#F0DFAD] bg-[#FFF9E9] px-4 py-2 text-[#D99A00]">
                      <AlertTriangle size={20} />
                      <span className="font-bold text-sm">PARTIALLY COMPLIANT</span>
                    </div>
                  )}
                  {!["COMPLIANT", "NON_COMPLIANT", "PARTIAL"].includes(
                    scanResult.compliance?.status
                  ) && (
                    <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-4 py-2 text-gray-700">
                      <span className="font-bold text-sm">
                        {scanResult.compliance?.status || "UNKNOWN"}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Product Information Grid */}
              <div className="mt-6">
                <h3 className="text-base font-bold text-[#142B4A] mb-4">
                  Extracted Product Information
                </h3>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div className="rounded-xl border border-[#E9EFF6] bg-[#F8FAFC] p-3.5">
                    <p className="text-xs font-medium text-[#6B7F99]">Product Name</p>
                    <p className="mt-1 text-sm font-semibold text-[#142B4A]">
                      {scanResult.product?.product_name || "N/A"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-[#E9EFF6] bg-[#F8FAFC] p-3.5">
                    <p className="text-xs font-medium text-[#6B7F99]">Manufacturer</p>
                    <p className="mt-1 text-sm font-semibold text-[#142B4A]">
                      {scanResult.product?.manufacturer || "N/A"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-[#E9EFF6] bg-[#F8FAFC] p-3.5">
                    <p className="text-xs font-medium text-[#6B7F99]">Net Quantity</p>
                    <p className="mt-1 text-sm font-semibold text-[#142B4A]">
                      {scanResult.product?.net_quantity || "N/A"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-[#E9EFF6] bg-[#F8FAFC] p-3.5">
                    <p className="text-xs font-medium text-[#6B7F99]">MRP</p>
                    <p className="mt-1 text-sm font-semibold text-[#142B4A]">
                      {scanResult.product?.mrp || "N/A"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-[#E9EFF6] bg-[#F8FAFC] p-3.5">
                    <p className="text-xs font-medium text-[#6B7F99]">Batch Number</p>
                    <p className="mt-1 text-sm font-semibold text-[#142B4A]">
                      {scanResult.product?.batch_number || "N/A"}
                    </p>
                  </div>

                  <div className="rounded-xl border border-[#E9EFF6] bg-[#F8FAFC] p-3.5">
                    <p className="text-xs font-medium text-[#6B7F99]">Mfg Date</p>
                    <p className="mt-1 text-sm font-semibold text-[#142B4A]">
                      {scanResult.product?.mfg_date || "N/A"}
                    </p>
                  </div>

                  <div className="col-span-full rounded-xl border border-[#E9EFF6] bg-[#F8FAFC] p-3.5">
                    <p className="text-xs font-medium text-[#6B7F99]">Consumer Care</p>
                    <p className="mt-1 text-sm font-semibold text-[#142B4A]">
                      {scanResult.product?.consumer_care || "N/A"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Violations List */}
              {scanResult.compliance?.violations &&
                scanResult.compliance.violations.length > 0 && (
                  <div className="mt-6 pt-5 border-t border-[#DDE6F0]">
                    <h3 className="text-base font-bold text-[#142B4A] mb-3 flex items-center gap-2">
                      <AlertCircle size={18} className="text-[#D9381E]" />
                      Compliance Violations ({scanResult.compliance.violations.length})
                    </h3>

                    <div className="space-y-3">
                      {scanResult.compliance.violations.map((v, idx) => (
                        <div
                          key={idx}
                          className="rounded-xl border border-red-200 bg-red-50/50 p-4"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-bold text-sm text-red-900">
                              {v.rule || "Violation Rule"}
                            </span>
                            {v.field && (
                              <span className="rounded-md bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800">
                                Field: {v.field}
                              </span>
                            )}
                          </div>
                          {v.description && (
                            <p className="mt-1.5 text-sm text-red-700">
                              {v.description}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          )}
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
            onClick={handleSubmit}
            disabled={images.length === 0 || loading}
            className={`flex w-full items-center justify-center gap-3 rounded-xl px-5 py-4 font-semibold transition-all ${
              images.length === 0
                ? "bg-[#E1E7EE] text-[#8A99AA] cursor-not-allowed"
                : loading
                ? "bg-[#2878D7]/80 text-white cursor-wait opacity-90"
                : "bg-[#2878D7] text-white hover:bg-[#1F64B8] shadow-sm cursor-pointer"
            }`}
          >
            {loading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <span>Start Inspection</span>
                <ArrowRight size={20} />
              </>
            )}
          </button>

        </div>
      </div>
    </div>
  );
}

export default NewInspection;