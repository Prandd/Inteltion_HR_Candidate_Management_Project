export function formatStatusLabel(status: string): string {
    return status === "CV rejected" || status === "Rejected"
        ? "Reject"
        : status;
}