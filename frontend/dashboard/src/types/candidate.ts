export interface CandidateSummary {


    candidate_id: string;

    full_name: string;

    applied_position: string;

    location: string;

    email: string;

    phone: string;

    experience_total: number;

    status: string;

    top_skills: string[];

    extraction_confidence: number;

    created_at: string;

}





export interface Experience {


    company: string;

    position: string;

    start_date: string;

    end_date: string;

    description: string;

}





export interface Education {


    institution: string;

    degree: string;

    field: string;

    year: string;

}





export interface CandidateDetailType {


    candidate_id: string;


    full_name: string;


    applied_position: string;


    location: string;


    email: string;


    phone: string;


    experience_total: number;


    status: string;



    skills: {

        skill:string;

        tools:string[];

    }[];



    summary:string;



    experience: Experience[];



    education: Education[];



    resume_url:string;



    resume_filename:string;



    hr_comment:string;



    extraction_confidence:number;


}