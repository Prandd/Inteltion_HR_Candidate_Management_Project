import { useCallback, useEffect, useState } from "react";
import { isAxiosError } from "axios";
import api from "../../api/axios";
import type { CandidateDetailType } from "../../types/candidate";

interface CommentType {
    comment_id: string;
    author_account_id: string;
    author_name: string;
    author_role: string;
    comment: string;
    commented_at: string;
    created_at: string;
    updated_at: string;
    is_edited: boolean;
}
interface Account {
    account_id: string;
    full_name: string;
    username: string;
    role: string;
}

function formatDate(value: string) {
    const date = new Date(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
    return Number.isNaN(date.getTime()) ? "Unknown date" : date.toLocaleString("en-GB", {
        dateStyle: "medium", timeStyle: "short",
    });
}

function roleLabel(role: string) {
    return ({ admin: "Admin", hr: "HR", line_manager: "Line Manager", recruiter: "Recruiter" } as Record<string, string>)[role] || role.replaceAll("_", " ");
}

function CommentSection({ candidate, onUpdate }: {
    candidate: CandidateDetailType;
    onUpdate?: () => void;
}) {
    const [comments, setComments] = useState<CommentType[]>([]);
    const [account, setAccount] = useState<Account | null>(null);
    const [text, setText] = useState("");
    const [fetching, setFetching] = useState(true);
    const [busy, setBusy] = useState<string | null>(null);
    const [error, setError] = useState("");
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editText, setEditText] = useState("");
    const commentsUrl = `/candidates/${candidate.candidate_id}/comments`;

    const refreshComments = useCallback(async () => {
        const response = await api.get(commentsUrl);
        setComments(response.data.data ?? []);
    }, [commentsUrl]);

    useEffect(() => {
        let cancelled = false;
        Promise.all([api.get(commentsUrl), api.get("/auth/me")]).then(([response, me]) => {
            if (!cancelled) {
                setComments(response.data.data ?? []);
                setAccount(me.data.data);
            }
        }).catch(() => {
            if (!cancelled) setError("Unable to load comments. Please refresh and try again.");
        }).finally(() => { if (!cancelled) setFetching(false); });
        return () => { cancelled = true; };
    }, [commentsUrl]);

    function showError(err: unknown) {
        setError(isAxiosError(err) && typeof err.response?.data?.error === "string"
            ? err.response.data.error : "Could not save your changes. Please try again.");
    }

    async function addComment(event: React.FormEvent) {
        event.preventDefault();
        if (!text.trim() || busy) return;
        setBusy("add");
        setError("");
        try {
            // The backend attributes the comment to the authenticated account.
            await api.post(commentsUrl, { comment: text.trim() });
            setText("");
            await refreshComments();
            onUpdate?.();
        } catch (err) { showError(err); }
        finally { setBusy(null); }
    }

    async function updateComment(event: React.FormEvent, commentId: string) {
        event.preventDefault();
        if (!editText.trim() || busy) return;
        setBusy(commentId);
        setError("");
        try {
            await api.put(`/comments/${commentId}`, { comment: editText.trim() });
            setEditingId(null);
            setEditText("");
            await refreshComments();
            onUpdate?.();
        } catch (err) { showError(err); }
        finally { setBusy(null); }
    }

    async function deleteComment(commentId: string) {
        if (busy || !window.confirm("Delete this comment?")) return;
        setBusy(commentId);
        setError("");
        try {
            await api.delete(`/comments/${commentId}`);
            await refreshComments();
            onUpdate?.();
        } catch (err) { showError(err); }
        finally { setBusy(null); }
    }

    return (
        <section className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <header className="mb-5">
                <h2 className="text-sm font-bold uppercase text-slate-900">Recruitment Collaboration & Feedback</h2>
                <p className="mt-1 text-xs text-slate-400">Comments and feedback history</p>
            </header>
            {error && <p role="alert" className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            <div className="mb-5 space-y-3" aria-busy={fetching}>
                {fetching ? <p className="text-sm text-slate-400">Loading comments...</p>
                    : comments.length === 0 ? <p className="text-sm text-slate-400">No comments yet.</p>
                    : comments.map(comment => {
                        const author = comment.author_name?.trim() || "Unknown account";
                        const isAuthor = account?.account_id === comment.author_account_id;
                        const initials = author.split(/\s+/).slice(0, 2).map(part => part[0]).join("").toUpperCase();
                        return <article key={comment.comment_id} className="rounded-xl border border-slate-100 bg-slate-50/50 p-4">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                                <div className="flex min-w-0 items-center gap-3">
                                    <span aria-hidden="true" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-semibold text-blue-600">{initials}</span>
                                    <div className="min-w-0">
                                        <p className="break-words text-sm font-semibold text-slate-800">{author}</p>
                                        <p className="mt-0.5 text-xs text-slate-500">{roleLabel(comment.author_role)}</p>
                                    </div>
                                </div>
                                <div className="text-xs text-slate-400">
                                    <time dateTime={comment.commented_at || comment.created_at}>{formatDate(comment.commented_at || comment.created_at)}</time>
                                    {comment.is_edited && <p className="mt-1">Edited {formatDate(comment.updated_at)}</p>}
                                </div>
                            </div>
                            {editingId === comment.comment_id ? (
                                <form onSubmit={event => updateComment(event, comment.comment_id)} className="mt-3">
                                    <textarea aria-label="Edit comment" value={editText} onChange={event => setEditText(event.target.value)}
                                        rows={3} maxLength={500} disabled={busy !== null}
                                        className="w-full rounded-lg border border-slate-200 bg-white p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200" />
                                    <div className="mt-2 flex items-center gap-3">
                                        <button type="submit" disabled={busy !== null || !editText.trim()}
                                            className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50">{busy === comment.comment_id ? "Saving..." : "Save"}</button>
                                        <button type="button" disabled={busy !== null} onClick={() => { setEditingId(null); setEditText(""); }}
                                            className="text-xs text-slate-500 disabled:opacity-50">Cancel</button>
                                        <span className="ml-auto text-xs text-slate-400">{editText.length}/500</span>
                                    </div>
                                </form>
                            ) : <>
                                <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">{comment.comment}</p>
                                {(isAuthor || account?.role === "admin") && <div className="mt-3 flex gap-3">
                                    {isAuthor && <button type="button" disabled={busy !== null} onClick={() => { setEditingId(comment.comment_id); setEditText(comment.comment); }}
                                        className="text-xs font-medium text-blue-600 hover:text-blue-800 disabled:opacity-50">Edit</button>}
                                    <button type="button" disabled={busy !== null} onClick={() => deleteComment(comment.comment_id)}
                                        className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50">{busy === comment.comment_id ? "Deleting..." : "Delete"}</button>
                                </div>}
                            </>}
                        </article>;
                    })}
            </div>
            <form onSubmit={addComment}>
                <label htmlFor={`feedback-${candidate.candidate_id}`} className="mb-2 block text-xs text-slate-500">
                    {account ? `Comment as a ${account.full_name || account.username}` : "Add feedback"}
                </label>
                <textarea id={`feedback-${candidate.candidate_id}`} value={text} onChange={event => setText(event.target.value)}
                    rows={3} maxLength={500} placeholder="Add feedback..." disabled={busy !== null || fetching || !account}
                    className="w-full resize-none rounded-xl border border-slate-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:bg-slate-50" />
                <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-slate-400">{text.length}/500</span>
                    <button type="submit" disabled={busy !== null || fetching || !account || !text.trim()}
                        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">{busy === "add" ? "Adding..." : "Add Comment"}</button>
                </div>
            </form>
        </section>
    );
}

export default CommentSection;
