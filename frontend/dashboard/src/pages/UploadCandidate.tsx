import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import DuplicateCandidateModal from "../components/DuplicateCandidateModal";
import type { PendingUploadReview } from "../components/DuplicateCandidateModal";

interface UploadItem {
    file: File;
    progress: number;
    status: "ready" | "uploading" | "success" | "error" | "review";
}

function UploadCandidate() {
    const navigate = useNavigate();
    const [files, setFiles] = useState<UploadItem[]>([]);
    const [uploading, setUploading] = useState(false);
    const [stage, setStage] = useState("");
    const [reviewQueue, setReviewQueue] = useState<PendingUploadReview[]>([]);
    const [currentReview, setCurrentReview] = useState<PendingUploadReview | null>(null);
    const [resolvingDuplicate, setResolvingDuplicate] = useState(false);
    const [resolvingAction, setResolvingAction] = useState<"update" | "create-new" | null>(null);
    const [reviewError, setReviewError] = useState("");
    const [pendingError, setPendingError] = useState("");
    const uploadableCount = files.filter(item => item.status === "ready" || item.status === "error").length;

    useEffect(() => {
        let cancelled = false;
        api.get("/pending-uploads").then(response => {
            if (cancelled) return;
            let accountId = "";
            try {
                accountId = JSON.parse(sessionStorage.getItem("inteltion_account") || "null")?.account_id || "";
            } catch { return; }
            const pending = (response.data.data as PendingUploadReview[]).filter(item => item.uploaded_by === accountId);
            setReviewQueue(previous => {
                const ids = new Set(previous.map(item => item.pending_upload_id));
                return [...previous, ...pending.filter(item => !ids.has(item.pending_upload_id))];
            });
        }).catch(() => {
            if (!cancelled) setPendingError("Unable to load pending reviews. Refresh to try again.");
        });
        return () => { cancelled = true; };
    }, []);

    function handleFiles(selected: File[]) {
        const newFiles: UploadItem[] = selected.map((file) => ({
            file,
            progress: 0,
            status: "ready"
        }));
        setFiles((prev) => [...prev, ...newFiles]);
    }

    function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
        handleFiles(Array.from(e.target.files || []));
        e.target.value = "";
    }

    function updateAllUploading(progress: number) {
        setFiles((prev) =>
            prev.map((item) =>
                item.status === "uploading" ? { ...item, progress } : item
            )
        );
    }

    function markByFilename(filename: string, status: UploadItem["status"]) {
        setFiles((prev) =>
            prev.map((item) =>
                item.file.name === filename
                    ? {
                          ...item,
                          status,
                          progress: status === "success" ? 100 : item.progress
                      }
                    : item
            )
        );
    }

    async function uploadFiles() {
        if (files.length === 0 || uploading) return;

        const itemsToUpload = files.filter(
            (item) => item.status === "ready" || item.status === "error"
        );
        if (itemsToUpload.length === 0) return;

        setUploading(true);
        setStage("Uploading resumes...");
        setFiles((prev) =>
            prev.map((item) =>
                itemsToUpload.some((target) => target.file === item.file)
                    ? { ...item, status: "uploading", progress: 5 }
                    : item
            )
        );

        const formData = new FormData();
        itemsToUpload.forEach((item) => formData.append("files", item.file));

        try {
            const response = await api.post("/candidates/upload", formData, {
                onUploadProgress: (event) => {
                    if (!event.total) return;
                    const percent = Math.min(
                        Math.round((event.loaded / event.total) * 90),
                        90
                    );
                    updateAllUploading(percent);
                    if (event.loaded >= event.total) setStage("Reading CVs and checking for duplicates...");
                }
            });

            const result = response.data?.data ?? response.data ?? {};
            const failed: Array<{ filename: string; error?: string }> =
                Array.isArray(result.failed) ? result.failed : [];
            const needsReview: PendingUploadReview[] =
                Array.isArray(result.needs_review) ? result.needs_review : [];

            const failedNames = new Set(failed.map((item) => item.filename));
            const reviewNames = new Set(
                needsReview.map((item) => item.filename)
            );

            setFiles((prev) =>
                prev.map((item) => {
                    if (
                        !itemsToUpload.some(
                            (target) => target.file === item.file
                        )
                    ) {
                        return item;
                    }

                    if (failedNames.has(item.file.name)) {
                        return { ...item, status: "error", progress: 0 };
                    }

                    if (reviewNames.has(item.file.name)) {
                        return { ...item, status: "review", progress: 100 };
                    }

                    return { ...item, status: "success", progress: 100 };
                })
            );

            if (needsReview.length > 0) {
                setReviewQueue(previous => [...previous, ...needsReview]);
                setReviewError("");
                setCurrentReview(needsReview[0]);
                setStage(
                    `${needsReview.length} upload${
                        needsReview.length > 1 ? "s need" : " needs"
                    } duplicate review`
                );
                return;
            }

            if (failed.length > 0) {
                setStage(
                    `Upload completed with ${failed.length} failed file${
                        failed.length > 1 ? "s" : ""
                    }`
                );
                return;
            }

            setStage("Completed successfully");
        } catch (error) {
            console.error(error);
            setFiles((prev) =>
                prev.map((item) =>
                    item.status === "uploading"
                        ? { ...item, status: "error", progress: 0 }
                        : item
                )
            );
            setStage("Upload failed");
        } finally {
            setUploading(false);
        }
    }

    function showNextReview(resolvedId: string) {
        const remaining = reviewQueue.filter(item => item.pending_upload_id !== resolvedId);
        setReviewQueue(remaining);
        setCurrentReview(remaining[0] || null);
    }

    async function resolveDuplicate(action: "update" | "create-new") {
        if (!currentReview || resolvingDuplicate) return;

        setResolvingDuplicate(true);
        setResolvingAction(action);
        setReviewError("");
        try {
            const response = await api.post(
                `/pending-uploads/${currentReview.pending_upload_id}/${action}`
            );
            const resolvedCandidate = response.data?.data?.candidate;
            markByFilename(currentReview.filename, "success");
            setStage(
                action === "update"
                    ? `Replaced CV for ${resolvedCandidate?.full_name || "existing candidate"} · Status: New`
                    : `Created ${resolvedCandidate?.full_name || "new candidate"}`
            );
            showNextReview(currentReview.pending_upload_id);
        } catch (error) {
            console.error(error);
            setReviewError(isAxiosError(error) && typeof error.response?.data?.error === "string"
                ? error.response.data.error : "Could not save your choice. Please try again.");
        } finally {
            setResolvingDuplicate(false);
            setResolvingAction(null);
        }
    }

    function removeFile(index: number) {
        if (uploading || files[index]?.status === "review") return;
        setFiles((prev) => prev.filter((_, i) => i !== index));
    }

    return (
        <>
            {currentReview && (
                <DuplicateCandidateModal
                    key={currentReview.pending_upload_id}
                    review={currentReview}
                    loading={resolvingDuplicate}
                    action={resolvingAction}
                    error={reviewError}
                    onClose={() => {
                        setCurrentReview(null);
                        setReviewError("");
                        setStage("Duplicate review pending");
                    }}
                    onUpdateRecord={() => resolveDuplicate("update")}
                    onCreateNewCycle={() => resolveDuplicate("create-new")}
                />
            )}

            <div className="min-h-screen bg-[#f7f9ff] p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    <div>
                        <button
                            onClick={() => navigate("/")}
                            className="text-sm text-gray-500 mb-4"
                        >
                            ← Back
                        </button>

                        <h1 className="text-3xl font-bold text-gray-900">
                            Add Candidate
                        </h1>

                        <p className="text-gray-500 mt-1">
                            Upload resumes and automatically extract candidate information
                        </p>
                    </div>

                    <div className="bg-white border rounded-2xl p-6">
                        {pendingError && <p role="alert" className="mb-4 text-sm text-red-600">{pendingError}</p>}
                        {reviewQueue.length > 0 && (
                            <section className="mb-6 rounded-xl border border-amber-200 bg-amber-50/50 p-4">
                                <h2 className="text-sm font-semibold text-slate-800">Pending duplicate reviews ({reviewQueue.length})</h2>
                                <p className="mt-1 text-xs text-slate-500">These CVs need your decision before they can be saved.</p>
                                <div className="mt-3 space-y-2">
                                    {reviewQueue.map(review => (
                                        <div key={review.pending_upload_id} className="flex items-center justify-between gap-3">
                                            <span className="min-w-0 truncate text-sm text-slate-600">{review.filename}</span>
                                            <button type="button" disabled={uploading || resolvingDuplicate} onClick={() => {
                                                setReviewError(""); setCurrentReview(review);
                                            }} className="shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-white disabled:opacity-50">Review</button>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}
                        <label className="h-56 border-2 border-dashed border-blue-300 rounded-2xl flex flex-col items-center justify-center cursor-pointer hover:bg-blue-50 transition">
                            <div className="w-14 h-14 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-3xl mb-3">
                                ↑
                            </div>

                            <p className="font-semibold text-blue-600">
                                Click to upload CV
                            </p>

                            <p className="text-sm text-gray-400 mt-1">
                                PDF, DOCX up to 10MB
                            </p>

                            <input
                                hidden
                                multiple
                                type="file"
                                accept=".pdf,.docx"
                                onChange={onFileChange}
                                disabled={uploading}
                            />
                        </label>

                        <div className="mt-6 space-y-3">
                            {files.map((item, index) => (
                                <div
                                    key={`${item.file.name}-${index}`}
                                    className="border rounded-xl p-4"
                                >
                                    <div className="flex justify-between">
                                        <div>
                                            <p className="font-medium">
                                                {item.file.name}
                                            </p>

                                            <p className="text-xs mt-1 text-gray-500">
                                                {item.status === "ready" &&
                                                    "Ready to upload"}
                                                {item.status === "uploading" &&
                                                    `Processing ${item.progress}%`}
                                                {item.status === "success" &&
                                                    "Uploaded successfully"}
                                                {item.status === "review" &&
                                                    "Needs duplicate review"}
                                                {item.status === "error" &&
                                                    "Upload failed"}
                                            </p>
                                        </div>

                                        <button
                                            onClick={() => removeFile(index)}
                                            disabled={uploading || item.status === "review"}
                                            aria-label={`Remove ${item.file.name}`}
                                            className="text-red-500 disabled:text-gray-300"
                                        >
                                            ×
                                        </button>
                                    </div>

                                    {item.status === "uploading" && (
                                        <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-600 transition-all duration-300"
                                                style={{
                                                    width: `${item.progress}%`
                                                }}
                                            />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {stage && (
                            <p role="status" className="text-center text-sm text-gray-500 mt-4">
                                {stage}
                            </p>
                        )}

                        <button
                            disabled={
                                uploadableCount === 0 ||
                                uploading ||
                                currentReview !== null
                            }
                            onClick={uploadFiles}
                            className="mt-6 w-full bg-blue-600 text-white py-3 rounded-xl font-semibold disabled:bg-gray-300"
                        >
                            {uploading
                                ? "Processing..."
                                : `Upload ${uploadableCount} CV${
                                      uploadableCount === 1 ? "" : "s"
                                  }`}
                        </button>
                        {files.some(item => item.status === "success") && <button type="button" onClick={() => navigate("/")}
                            className="mt-3 w-full rounded-xl py-2 text-sm text-slate-500 hover:text-slate-800">View dashboard →</button>}
                    </div>
                </div>
            </div>
        </>
    );
}

export default UploadCandidate;
