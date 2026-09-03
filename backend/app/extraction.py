"""
MOCK CV extraction engine.

Replace later with llm-service extractor.
Current version generates schema-valid candidate data.
"""

from __future__ import annotations

import random


_FIRST = [
    "Somchai",
    "Ariya",
    "Nattapong",
    "Kanya",
    "Thanakorn",
    "Pimchanok",
    "Chalermsak",
    "Warunee",
    "Peerapat",
    "Sasithorn",
]


_LAST = [
    "Srisai",
    "Wong",
    "Chaicharoen",
    "Rattanakul",
    "Boonmee",
    "Intira",
    "Phumipat",
    "Kittisak",
]



_POSITIONS = [
    "Backend Engineer",
    "Data Engineer",
    "Frontend Engineer",
    "Machine Learning Engineer",
    "DevOps Engineer",
    "Full-Stack Developer",
]



_SKILLS = [

    (
        "Python",
        [
            "FastAPI",
            "Django",
            "pandas"
        ]
    ),

    (
        "JavaScript",
        [
            "React",
            "Node.js",
            "TypeScript"
        ]
    ),

    (
        "SQL",
        [
            "PostgreSQL",
            "BigQuery",
            "MySQL"
        ]
    ),

    (
        "Cloud",
        [
            "AWS",
            "Azure",
            "GCP"
        ]
    ),

    (
        "Data Engineering",
        [
            "Airflow",
            "dbt",
            "Spark"
        ]
    ),

    (
        "DevOps",
        [
            "Docker",
            "Kubernetes",
            "Terraform"
        ]
    )

]



_COMPANIES = [

    "Inteltion",
    "SCB TechX",
    "Agoda",
    "LINE MAN Wongnai",
    "KBTG",
    "Sertis",
    "Pomelo",
    "Ascend Money"

]



_UNIS = [

    "Chulalongkorn University",
    "Chiang Mai University",
    "Kasetsart University",
    "Thammasat University",
    "KMUTT"

]



_EDU_FIELDS = [

    "Computer Engineering",
    "Computer Science",
    "Information Technology",
    "Data Science",
    "Software Engineering"

]



_counter = random.Random()





def _generate_skills(rnd):


    selected = rnd.sample(
        _SKILLS,
        rnd.randint(1,4)
    )


    return [

        {
            "skill": name,
            "tools": tools[:]
        }

        for name,tools in selected

    ]








def _mock_candidate(seed:int):


    rnd = random.Random(seed)



    first = rnd.choice(_FIRST)

    last = rnd.choice(_LAST)



    position = rnd.choice(
        _POSITIONS
    )



    skills = _generate_skills(
        rnd
    )



    years = rnd.randint(
        1,
        12
    )




    experience = []


    end_year = 2026



    for i in range(
        rnd.randint(1,3)
    ):


        start_year = (
            end_year -
            rnd.randint(1,3)
        )


        experience.append(

            {

                "company":
                    rnd.choice(
                        _COMPANIES
                    ),


                "position":
                    position,


                "start_date":
                    f"{start_year}-01",


                "end_date":
                    "Present"
                    if i == 0
                    else f"{end_year}-12",


                "description":
                    (
                        "Built software systems "
                        "using "
                        +
                        skills[0]["skill"]
                    )

            }

        )


        end_year = start_year






    return {


        # BASIC INFO

        "full_name":
            f"{first} {last}",


        "email":
            f"{first.lower()}.{last.lower()}@example.com",


        "phone":
            f"08{rnd.randint(10000000,99999999)}",



        "location":
            rnd.choice(
                [
                    "Bangkok, Thailand",
                    "Chiang Mai, Thailand",
                    "Remote",
                    "Nonthaburi, Thailand"
                ]
            ),



        "applied_position":
            position,




        # SUMMARY

        "summary":
            (
                f"{position} with "
                f"{years} years of experience. "
                f"Experienced in "
                f"{skills[0]['skill']}."
            ),





        # SKILLS

        "skills":
            skills,






        # EXPERIENCE

        "experience":
            experience,



        "experience_total":
            float(years),





        # SALARY

        "current_salary":
            0.0,


        "expected_salary":
            0.0,






        # EDUCATION

        "education":

            [

                {

                    "institution":
                        rnd.choice(
                            _UNIS
                        ),

                    "degree":
                        "B.Eng.",


                    "field":
                        rnd.choice(
                            _EDU_FIELDS
                        ),


                    "year":
                        "2024"

                }

            ],







        "hr_comment":
            "",



        "line_manager_comment":
            "",




        "extraction_confidence":
            round(
                rnd.uniform(
                    0.75,
                    0.98
                ),
                2
            ),





        "raw_text_snippet":

            "[MOCK CV EXTRACTION]",





        "status":

            "New"


    }









def extract_candidate(
    file_bytes: bytes,
    filename: str | None = None
) -> dict:


    """
    Mock extractor.

    Same interface as real LLM extractor.
    """


    seed = (

        len(file_bytes)
        *
        2654435761
        +
        _counter.randint(
            0,
            10000000
        )

    ) & 0xffffffff



    return _mock_candidate(
        seed
    )