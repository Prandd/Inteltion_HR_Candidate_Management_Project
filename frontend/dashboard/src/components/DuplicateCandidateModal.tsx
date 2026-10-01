import {
    useNavigate
} from "react-router-dom";

export interface DuplicateCandidate {
    candidate_id: string;
    full_name?: string;
    email?: string;
    phone?: string;
    applied_position?: string;
    status?: string;
    created_at?: string;
    updated_at?: string;
    rejected_at?: string | null;
    rejected_from_status?: string | null;
    rejection_reason?: string;
    latest_comment?: string;
    latest_comment_by?: string;
}

export interface PendingUploadReview {
    pending_upload_id: string;
    filename: string;
    extracted_preview: Record<string, unknown>;
    duplicate_candidates: DuplicateCandidate[];
    uploaded_by: string;
    created_at: string;
}

interface Props {
    review: PendingUploadReview;
    loading?: boolean;
    onClose: () => void;
    onUpdateRecord: () => void;
    onCreateNewCycle: () => void;
}

function DuplicateCandidateModal({
    review,
    loading = false,
    onClose,
    onUpdateRecord,
    onCreateNewCycle
}: Props) {
    const navigate = useNavigate();
    const candidate = review.duplicate_candidates[0];
    const rejectedAt = candidate?.rejected_at
        ? new Date(candidate.rejected_at)
        : null;
    const cooldownEndsAt = rejectedAt && candidate?.status === "Rejected"
        ? addCalendarMonths(rejectedAt, 3)
        : null;
    const cooldownElapsed = cooldownEndsAt !== null && cooldownEndsAt <= new Date();
    const recommendedAction = cooldownElapsed ? "create" : "update";

    function previewValue(key: string) {
        const value = review.extracted_preview[key];
        return typeof value === "string" || typeof value === "number"
            ? String(value) || "-"
            : "-";
    }

    function viewCandidate() {
        if (!candidate) return;
        navigate(`/candidate/${candidate.candidate_id}`);
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="duplicate-review-title"
                className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-2xl"
            >
                <div className="border-b border-blue-100 bg-blue-50/60 p-6">
                    <div className="flex items-start gap-4">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-500 text-xl font-bold text-white">
                            !
                        </div>
                        <div className="min-w-0 flex-1">
                            <span className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                                ● ตรวจพบประวัติเดิม (Duplicate Profile Detected)
                            </span>
                            <h2 id="duplicate-review-title" className="mt-2 text-xl font-bold text-slate-900">
                                พบข้อมูลผู้สมัครเดิมในระบบ (Existing Candidate Found)
                            </h2>
                            <p className="mt-2 text-sm leading-6 text-slate-600">
                                ระบบพบประวัติหรือข้อมูลที่ตรงกับ CV นี้ โปรดตรวจสอบก่อนเลือกว่าจะสร้างรอบสมัครใหม่หรืออัปเดตประวัติเดิม
                            </p>
                            <p className="mt-2 truncate text-xs text-slate-500">ไฟล์: {review.filename}</p>
                        </div>
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={loading}
                            aria-label="Close duplicate review"
                            className="shrink-0 px-2 text-2xl leading-none text-slate-400 hover:text-slate-700 disabled:opacity-40"
                        >
                            ×
                        </button>
                    </div>

                    <div className="mt-5 rounded-xl border border-blue-200 bg-white p-4">
                        <div className="flex flex-wrap items-center gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                                {(candidate?.full_name || "?").split(/\s+/).map((part) => part[0]).slice(0, 2).join("").toUpperCase()}
                            </div>
                            <div className="min-w-0 flex-1">
                                <p className="font-semibold text-slate-900">
                                    {candidate?.full_name || "Candidate record unavailable"}
                                    {review.duplicate_candidates.length > 1 && (
                                        <span className="ml-2 text-xs font-normal text-slate-500">
                                            +{review.duplicate_candidates.length - 1} possible match(es)
                                        </span>
                                    )}
                                </p>
                                <p className="mt-1 break-all text-xs text-slate-500">
                                    {candidate?.email || "No email"} <span className="px-1">·</span> {candidate?.phone || "No phone"}
                                </p>
                            </div>
                            {candidate && (
                                <button
                                    type="button"
                                    onClick={viewCandidate}
                                    disabled={loading}
                                    className="text-sm font-semibold text-blue-700 hover:text-blue-900 disabled:opacity-40"
                                >
                                    ดูประวัติแบบละเอียด ↗
                                </button>
                            )}
                        </div>
                        <div className="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-3">
                            <InfoRow label="ข้อมูลจาก CV ใหม่ · ชื่อ" value={previewValue("full_name")} />
                            <InfoRow label="อีเมล" value={previewValue("email")} />
                            <InfoRow label="เบอร์โทร" value={previewValue("phone")} />
                            <InfoRow label="ตำแหน่งที่สมัครจาก CV ใหม่" value={previewValue("applied_position")} />
                        </div>
                    </div>
                </div>

                <div className="space-y-6 p-6">
                    <section>
                        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                            <h3 className="text-xs font-bold uppercase tracking-wide text-slate-500">
                                สรุปประวัติเดิมในระบบ (Previous Record Summary)
                            </h3>
                            {cooldownEndsAt ? (
                                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${cooldownElapsed ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"}`}>
                                    {cooldownElapsed
                                        ? `พ้นช่วง Cooldown 3 เดือนแล้ว · ${formatDate(cooldownEndsAt)}`
                                        : `ช่วง Cooldown ถึง ${formatDate(cooldownEndsAt)}`}
                                </span>
                            ) : (
                                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                                    ยังไม่มีประวัติการปฏิเสธ
                                </span>
                            )}
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <p className="text-sm text-slate-700">
                                    ตำแหน่งเดิม: <strong className="text-slate-900">{candidate?.applied_position || "ไม่ระบุ"}</strong>
                                </p>
                                <span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700">
                                    ● {candidate?.status || "ไม่ทราบสถานะ"}
                                </span>
                            </div>
                            {candidate?.created_at && (
                                <p className="mt-3 text-xs text-slate-500">
                                    สมัครเมื่อ {formatDate(candidate.created_at)}
                                </p>
                            )}
                            {rejectedAt && (
                                <p className="mt-3 text-xs text-slate-500">
                                    ปฏิเสธเมื่อ {formatDate(rejectedAt)}
                                    {candidate?.rejected_from_status && ` · ก่อนหน้าอยู่ขั้น ${candidate.rejected_from_status}`}
                                </p>
                            )}
                            {(candidate?.rejection_reason || candidate?.latest_comment) && (
                                <div className="mt-4 space-y-3 rounded-lg border border-slate-200 bg-white p-4">
                                    {candidate.rejection_reason && (
                                        <InfoRow label="เหตุผลการปฏิเสธ" value={candidate.rejection_reason} />
                                    )}
                                    {candidate.latest_comment && (
                                        <div>
                                            <p className="text-xs font-semibold text-slate-500">
                                                ความเห็นล่าสุด{candidate.latest_comment_by ? `: ${candidate.latest_comment_by}` : ""}
                                            </p>
                                            <p className="mt-1 text-sm leading-6 text-slate-700">{candidate.latest_comment}</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </section>

                    <section>
                        <h3 className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">
                            กรุณาเลือกรูปแบบการดำเนินการ (Select Action)
                        </h3>
                        <div className="grid gap-4 md:grid-cols-2">
                            <ActionPanel
                                number="1"
                                title="สร้างรอบการสมัครใหม่"
                                recommended={recommendedAction === "create"}
                                description="เก็บประวัติเดิมไว้แยกต่างหาก และสร้าง Fresh Application Cycle สำหรับ CV ใบนี้"
                                note="เหมาะเมื่อผู้สมัครกลับมา Re-apply หรือสมัครตำแหน่ง/รอบใหม่"
                                buttonText="＋  สร้างเป็นรอบใหม่ (Create New Cycle)"
                                onClick={onCreateNewCycle}
                                disabled={loading}
                                primary={recommendedAction === "create"}
                            />
                            <ActionPanel
                                number="2"
                                title="อัปเดตข้อมูลทับประวัติเดิม"
                                recommended={recommendedAction === "update"}
                                description="เพิ่มไฟล์ Resume / Portfolio ล่าสุดเข้า Timeline เดิม โดยคงสถานะและข้อมูลที่ HR บันทึกไว้"
                                note="เหมาะสำหรับส่งเอกสารเพิ่มเติมหรือแก้ไข CV ของรอบเดิม"
                                buttonText="↻  อัปเดตประวัติเดิม (Update Record)"
                                onClick={onUpdateRecord}
                                disabled={loading || !candidate}
                                primary={recommendedAction === "update"}
                            />
                        </div>
                    </section>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 bg-slate-50 px-6 py-4 text-xs text-slate-500">
                    <span className="text-emerald-700">✓ ประวัติเดิมยังคงอยู่และตรวจสอบย้อนหลังได้</span>
                    <button type="button" onClick={onClose} disabled={loading} className="hover:text-slate-900 disabled:opacity-40">
                        ข้ามขั้นตอนนี้ก่อน (Skip for now)
                    </button>
                </div>
            </div>
        </div>
    );
}

function InfoRow({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <p className="text-xs text-slate-500">{label}</p>
            <p className="mt-1 break-words text-sm font-medium text-slate-800">{value}</p>
        </div>
    );
}

function ActionPanel({
    number,
    title,
    recommended,
    description,
    note,
    buttonText,
    onClick,
    disabled,
    primary
}: {
    number: string;
    title: string;
    recommended: boolean;
    description: string;
    note: string;
    buttonText: string;
    onClick: () => void;
    disabled: boolean;
    primary: boolean;
}) {
    return (
        <div className={`relative flex flex-col rounded-xl border p-4 ${primary ? "border-blue-500 bg-blue-50/30 ring-1 ring-blue-500" : "border-slate-200 bg-white"}`}>
            {recommended && (
                <span className="absolute -top-2.5 right-4 rounded-full bg-blue-600 px-3 py-1 text-[10px] font-bold text-white">
                    แนะนำ (RECOMMENDED)
                </span>
            )}
            <div className="flex items-center gap-3">
                <span className={`flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold ${primary ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600"}`}>
                    {number}
                </span>
                <h4 className="text-sm font-bold text-slate-900">{title}</h4>
            </div>
            <p className="mt-4 min-h-16 text-sm leading-6 text-slate-600">{description}</p>
            <p className="mt-3 flex-1 rounded-lg bg-slate-100 px-3 py-2 text-xs leading-5 text-slate-600">✓ {note}</p>
            <button
                type="button"
                onClick={onClick}
                disabled={disabled}
                className={`mt-4 min-h-11 rounded-lg px-3 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${primary ? "bg-blue-600 text-white hover:bg-blue-700" : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"}`}
            >
                {buttonText}
            </button>
        </div>
    );
}

function addCalendarMonths(date: Date, months: number) {
    const result = new Date(date);
    const day = result.getDate();
    result.setDate(1);
    result.setMonth(result.getMonth() + months);
    const lastDay = new Date(result.getFullYear(), result.getMonth() + 1, 0).getDate();
    result.setDate(Math.min(day, lastDay));
    return result;
}

function formatDate(value: Date | string) {
    const date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) return "ไม่ระบุวันที่";
    return new Intl.DateTimeFormat("th-TH", {
        day: "numeric",
        month: "short",
        year: "numeric"
    }).format(date);
}

export default DuplicateCandidateModal;
