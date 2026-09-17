from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
import uuid



router = APIRouter(
    prefix="/positions",
    tags=["positions"]
)





# =========================
# SCHEMA
# =========================


class PositionCreate(BaseModel):

    title: str

    department: str

    description: Optional[str] = ""

    location: Optional[str] = ""

    skills: list[str] = Field(
        default_factory=list
    )









# =========================
# MOCK DATABASE
# =========================


positions = [


    {
        "id": "1",

        "title": "AI Engineer",

        "department": "Data Science & AI",

        "description":
            "Build AI systems",

        "skills": [
            "Python",
            "TensorFlow"
        ],

        "location":
            "Bangkok",

        "status":
            "Open",

        "candidate_count":
            12
    },



    {
        "id": "2",

        "title": "Frontend Developer",

        "department":
            "Engineering",

        "description":
            "Build web applications",

        "skills": [
            "React",
            "TypeScript"
        ],

        "location":
            "Remote",

        "status":
            "Open",

        "candidate_count":
            8
    }


]









# =========================
# GET POSITIONS
# =========================


@router.get("")
def get_positions():


    return {

        "data":
            positions,

        "error":
            None

    }









# =========================
# CREATE POSITION
# =========================


@router.post("")
def create_position(

    position: PositionCreate

):


    new_position = {


        "id":
            str(uuid.uuid4()),



        "title":
            position.title,



        "department":
            position.department,



        "description":
            position.description,



        "skills":
            position.skills,



        "location":
            position.location,



        "status":
            "Open",



        "candidate_count":
            0


    }







    positions.append(

        new_position

    )






    return {


        "data":
            new_position,


        "error":
            None

    }








# =========================
# GET POSITION BY ID
# =========================


@router.get("/{position_id}")
def get_position(

    position_id:str

):


    for position in positions:


        if position["id"] == position_id:


            return {

                "data":
                    position,

                "error":
                    None

            }





    return {


        "data":
            None,

        "error":
            "Position not found"

    }