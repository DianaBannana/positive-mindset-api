"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, X, FileAudio, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createBrowserClient } from "@/lib/supabase";

interface AudioUploadProps {
  orgId: string;
  userId: string;
  onUploadSuccess?: () => void;
}

export function AudioUpload({ orgId, userId, onUploadSuccess }: AudioUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const supabase = createBrowserClient();

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleFileSelect = useCallback(async (file: File) => {
    // Validate file type
    const validTypes = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/m4a", "audio/webm", "audio/*"];
    const isValidType = validTypes.some(type => {
      if (type === "audio/*") return file.type.startsWith("audio/");
      return file.type === type || file.name.toLowerCase().endsWith(type.split("/")[1]);
    });

    if (!isValidType) {
      setError("Invalid file type. Please upload an audio file (MP3, WAV, M4A, etc.)");
      return;
    }

    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      setError("File too large. Maximum size is 50MB.");
      return;
    }

    setError(null);
    setSuccess(false);
    setUploading(true);
    setProgress(0);

    try {
      // Get Supabase session token
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error("Not authenticated. Please log in again.");
      }

      // DEV_ONLY: FORCE override - if DEV_ORG_ID is set, use it regardless of passed orgId
      const devOrgId = process.env.NEXT_PUBLIC_DEV_ORG_ID;
      let uploadOrgId = orgId;
      if (devOrgId) {
        const originalOrgId = orgId;
        uploadOrgId = devOrgId;
        console.log("!!! FORCING DEV ORG ID:", uploadOrgId);
        console.log("[Upload] DEV_ONLY OVERRIDE: Original orgId was:", originalOrgId, "→ Forced to:", uploadOrgId);
      } else if (!orgId || orgId === "default-org-id") {
        console.warn("[Upload] No DEV_ORG_ID set and orgId is invalid:", orgId);
      }

      // Create FormData
      const formData = new FormData();
      formData.append("file", file);
      formData.append("org_id", uploadOrgId);
      formData.append("user_id", userId);
      formData.append("client_name", ""); // Optional, can be empty

      console.log("[Upload] Starting upload...");
      console.log("[Upload] File:", file.name, `(${(file.size / 1024 / 1024).toFixed(2)} MB)`);
      console.log("[Upload] Org ID:", uploadOrgId);
      console.log("[Upload] User ID:", userId);

      // Upload with progress tracking using Promise wrapper
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            setProgress(percentComplete);
            console.log(`[Upload] Progress: ${percentComplete.toFixed(1)}%`);
          }
        });

        // Handle completion
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              console.log("[Upload] Success:", response);
              setSuccess(true);
              setProgress(100);
              
              // Reset after 2 seconds
              setTimeout(() => {
                setSuccess(false);
                setProgress(0);
                setUploading(false);
              }, 2000);

              // Trigger table refresh
              if (onUploadSuccess) {
                onUploadSuccess();
              }
              
              resolve();
            } catch (parseError) {
              console.error("[Upload] Failed to parse response:", parseError);
              reject(new Error("Invalid response from server"));
            }
          } else {
            let errorMsg = `Server error: ${xhr.status}`;
            try {
              if (xhr.responseText) {
                const errorResponse = JSON.parse(xhr.responseText);
                errorMsg = errorResponse.detail || errorResponse.message || errorMsg;
              }
            } catch {
              errorMsg = `Upload failed: ${xhr.status} ${xhr.statusText}`;
            }
            reject(new Error(errorMsg));
          }
        });

        // Handle errors
        xhr.addEventListener("error", () => {
          reject(new Error("Network error. Check if the backend is running at " + API_URL));
        });

        // Handle abort
        xhr.addEventListener("abort", () => {
          reject(new Error("Upload cancelled."));
        });

        // Open and send request
        xhr.open("POST", `${API_URL}/api/v1/meetings/upload`);
        
        // Set authorization header with Supabase token
        xhr.setRequestHeader("Authorization", `Bearer ${session.access_token}`);
        
        // Send FormData
        xhr.send(formData);
      });

    } catch (err: any) {
      console.error("[Upload] Error:", err);
      setError(err.message || "Upload failed. Please try again.");
      setUploading(false);
      setProgress(0);
      
      // Show alert for visibility
      alert(`Upload failed: ${err.message || "Unknown error"}`);
    }
  }, [orgId, userId, supabase, API_URL, onUploadSuccess]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          relative border-2 border-dashed rounded-lg p-6 sm:p-8 text-center cursor-pointer
          transition-all duration-200
          min-h-[200px] sm:min-h-[240px]
          flex items-center justify-center
          touch-manipulation
          ${
            isDragging
              ? "border-blue-500 bg-blue-50"
              : uploading
              ? "border-gray-300 bg-gray-50 cursor-not-allowed"
              : "border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50 active:bg-blue-100"
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*,.mp3,.wav,.m4a,.webm"
          onChange={handleFileInputChange}
          disabled={uploading}
          className="hidden"
        />

        {uploading ? (
          <div className="space-y-4">
            <Loader2 className="h-12 w-12 mx-auto animate-spin text-blue-600" />
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">Uploading...</p>
              {/* Progress Bar */}
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">{progress.toFixed(0)}%</p>
            </div>
          </div>
        ) : success ? (
          <div className="space-y-2">
            <CheckCircle2 className="h-12 w-12 mx-auto text-green-600" />
            <p className="text-sm font-medium text-green-700">Upload successful!</p>
            <p className="text-xs text-gray-500">Your meeting is being processed...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="rounded-full bg-blue-100 p-4">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">
                {isDragging ? "Drop audio file here" : "Click to upload or drag and drop"}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                MP3, WAV, M4A, WEBM (Max 50MB)
              </p>
            </div>
            <Button 
              variant="outline" 
              size="lg" 
              disabled={uploading}
              className="min-h-[48px] min-w-[200px] text-base touch-manipulation"
            >
              <FileAudio className="h-5 w-5 mr-2" />
              Select Audio File
            </Button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">Upload Failed</p>
            <p className="text-xs text-red-600 mt-1">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
