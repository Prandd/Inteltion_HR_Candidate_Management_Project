import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api/axios";
import type { CandidateDetailType } from "../types/candidate";

import CandidateHeader from "../components/candidate/CandidateHeader";
import CandidateSummary from "../components/candidate/CandidateSummary";
import ExperienceSection from "../components/candidate/ExperienceSection";
import EducationSection from "../components/candidate/EducationSection";
import SkillsSection from "../components/candidate/SkillsSection";
import ContactSection from "../components/candidate/ContactSection";
import ResumeSection from "../components/candidate/ResumeSection";
import StatusHistorySection from "../components/candidate/StatusHistorySection";
import CommentSection from "../components/candidate/CommentSection";
import SectionCard from "../components/candidate/SectionCard";

function CandidateDetail() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [candidate, setCandidate] = useState<CandidateDetailType | null>(null);
    const [loading, setLoading] = useState(true);

    async function fetchCandidate() {
        if (!id) return;

        try {
            const response = await api.get(`/candidates/${id}`);
            setCandidate(response.data.data);
        } catch (error) {
            console.error("Failed to fetch candidate:", error);
            setCandidate(null);
        } finally {
            setLoading(false);
        }
    }

    async function deleteCandidate() {
        if (!id) return;

        const confirmed = window.confirm(
            "Are you sure you want to delete this candidate?"
        );

        if (!confirmed) return;

        try {
            await api.delete(`/candidates/${id}`);
            navigate("/");
        } catch (error) {
            console.error("Failed to delete candidate:", error);
        }
    }

    useEffect(() => {
        fetchCandidate();
    }, [id]);

    if (loading) {
        return (
            <div className="p-10">
                Loading candidate...
            </div>
        );
    }

    if (!candidate) {
        return (
            <div className="p-10">
                Candidate not found
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#f7f9ff] p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                <CandidateHeader
                    candidate={candidate}
                    onDelete={deleteCandidate}
                    onUpdate={fetchCandidate}
                />

                <div className="grid grid-cols-12 gap-6">
                    <div className="col-span-8 space-y-6">
                        <CandidateSummary candidate={candidate} />

                        <SectionCard title="Experience">
                            {candidate.experience?.length ? (
                                <ExperienceSection candidate={candidate} />
                            ) : (
                                <p className="text-gray-400">
                                    No experience available
                                </p>
                            )}
                        </SectionCard>

                        <SectionCard title="Education">
                            {candidate.education?.length ? (
                                <EducationSection candidate={candidate} />
                            ) : (
                                <p className="text-gray-400">
                                    No education available
                                </p>
                            )}
                        </SectionCard>

                        <CommentSection
                            candidate={candidate}
                            onUpdate={fetchCandidate}
                        />
                    </div>

                    <div className="col-span-4 space-y-6">
                        <ContactSection candidate={candidate} />

                        <ResumeSection candidate={candidate} />

                        <SectionCard title="Skills">
                            {candidate.skills?.length ? (
                                <SkillsSection candidate={candidate} />
                            ) : (
                                <p className="text-gray-400">
                                    No skills available
                                </p>
                            )}
                        </SectionCard>

                        <StatusHistorySection candidate={candidate} />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default CandidateDetail;