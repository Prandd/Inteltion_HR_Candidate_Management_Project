export interface CandidateSummary {


    candidate_id: string;


    full_name?: string;


    applied_position?: string;


    location?: string;


    email?: string;


    phone?: string;


    experience_total?: number;


    status?: string;


    top_skills?: string[];


    extraction_confidence?: number;


    created_at?: string;

}

export interface Experience {


    company?: string;


    position?: string;


    start_date?: string;


    end_date?: string;


    description?: string;

    skills?: string[];

}

export interface Education {


    institution?: string;


    degree?: string;


    field?: string;


    year?: string;

}

export interface CandidateSkill {


    skill:string;


    tools:string[];

}

export interface CandidateDetailType {

    candidate_id:string;

    full_name?:string;

    applied_position?:string;

    location?:string;

    email?:string;

    phone?:string;

    experience_total?:number;

    status?:string;

    skills?:CandidateSkill[];

    summary?:string;

    experience?:Experience[];

    education?:Education[];

    resume_url?:string;

    resume_filename?:string;

    top_skills?:string[];

    hr_comment?:string;

    line_manager_comment?:string;

    extraction_confidence?:number;

    status_history?:StatusHistory[];

    evaluation?: Evaluation;

    created_at?: string;

}


export interface Evaluation {

    overall_score?:number;

    recommendation?:string;

    technical_score?:number;

    communication_score?:number;

    experience_score?:number;

}


export interface CandidateComment {

    hr_comment?:string;

    line_manager_comment?:string;

}


export interface StatusHistory {


    status:string;

    action?:string;

    changed_by?:string;

    changed_at?:string;

    previous_status?:string;

}

export interface CandidateComment {

    id:number;

    author:string;

    role:string;

    comment:string;

    created_at:string;

}